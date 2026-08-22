"""Phase-10 Brainvision lifecycle, recovery, and runtime hosting.

This module owns only Brainvision lifecycle orchestration.  It intentionally
does not parse observations, perform replay admission, expose sinks, or connect
to memory, cognition, kernel, SRG, Hivermind, or model systems.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
import logging
import os
from os import PathLike
import time

from brainvision.character_modulation import modulation_profile_id
from brainvision.clock import MonotonicNsSource, VisualClock
from brainvision.configuration import (
    BrainvisionConfigurationV1,
    brainvision_configuration_path,
    fresh_disabled_brainvision_configuration,
    load_brainvision_configuration,
    validate_configuration_replacement,
    write_brainvision_configuration,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DISABLED,
    LIFECYCLE_SUSPENDED,
)
from brainvision.vhe import VheState, evolve_vhe_state_as_of
from brainvision.vhe_sidecar import (
    CONFIG_AHEAD,
    EQUAL,
    SIDECAR_AHEAD,
    VheSidecarV1,
    fresh_vhe_sidecar,
    load_vhe_sidecar,
    validate_configuration_sidecar_compatibility,
    vhe_sidecar_path,
    write_vhe_sidecar,
)
from torment_service.agent_locks import AgentLockManager
from torment_service.identity import AgentIdentity, IdentityStore
from torment_service.pathing import ensure_within_base, safe_slug


_LOG = logging.getLogger(__name__)


class BrainvisionLifecycleError(RuntimeError):
    """A Phase-10 lifecycle, recovery, or durability failure."""

    def __init__(
        self,
        field: str,
        reason: str,
        *,
        durable_committed: bool = False,
    ) -> None:
        self.field = field
        self.reason = reason
        self.durable_committed = durable_committed
        super().__init__(f"{field}: {reason}")


@dataclass
class BrainvisionRuntime:
    """Process-local state for one active or suspended Brainvision agent."""

    configuration: BrainvisionConfigurationV1
    vhe_state: VheState
    visual_clock: VisualClock


@dataclass(frozen=True, kw_only=True)
class BrainvisionRuntimeSnapshot:
    """Immutable internal state snapshot for a later projection boundary."""

    configuration: BrainvisionConfigurationV1
    vhe_state: VheState
    active_time_ns: int


class BrainvisionActiveTransaction:
    """One locked, staged Phase-11 successor-commit boundary."""

    def __init__(
        self,
        *,
        manager: "BrainvisionLifecycleManager",
        key: tuple[str, str],
        configuration: BrainvisionConfigurationV1,
        base_vhe_state: VheState,
        prior_committed_active_time_ns: int,
        cutoff_active_time_ns: int,
        elapsed_active_time_ns: int,
        replay_watermark: int,
        staged_clock: VisualClock,
    ) -> None:
        self.configuration = configuration
        self.base_vhe_state = base_vhe_state
        self.prior_committed_active_time_ns = prior_committed_active_time_ns
        self.cutoff_active_time_ns = cutoff_active_time_ns
        self.elapsed_active_time_ns = elapsed_active_time_ns
        self.current_replay_watermark = replay_watermark
        self._manager = manager
        self._key = key
        self._staged_clock = staged_clock
        self._committed = False
        self._closed = False

    def commit_successor(
        self,
        successor_vhe_state: VheState,
        accepted_source_sequence: int,
    ) -> BrainvisionRuntimeSnapshot:
        """Durably commit a Phase-11-derived successor once."""

        if self._closed:
            raise BrainvisionLifecycleError("transaction", "transaction_closed")
        if self._committed:
            raise BrainvisionLifecycleError("transaction", "transaction_already_committed")
        self._committed = True
        return self._manager._commit_successor_locked(
            transaction=self,
            successor_vhe_state=successor_vhe_state,
            accepted_source_sequence=accepted_source_sequence,
        )

    def _close(self) -> None:
        self._closed = True


class BrainvisionLifecycleManager:
    """Brainvision-owned runtime registry and lifecycle authority."""

    def __init__(
        self,
        *,
        data_dir: str | PathLike[str],
        identity_store: IdentityStore,
        lock_manager: AgentLockManager,
        monotonic_ns_source: MonotonicNsSource = time.monotonic_ns,
    ) -> None:
        root = os.fspath(data_dir)
        if type(root) is not str:
            raise TypeError("data_dir must be a string path")
        if type(identity_store) is not IdentityStore:
            raise TypeError("identity_store must be IdentityStore")
        if type(lock_manager) is not AgentLockManager:
            raise TypeError("lock_manager must be AgentLockManager")
        if not callable(monotonic_ns_source):
            raise TypeError("monotonic_ns_source must be callable")
        self._data_dir = os.path.realpath(root)
        self._identity_store = identity_store
        self._lock_manager = lock_manager
        self._monotonic_ns_source = monotonic_ns_source
        self._manager_reconstruction_epoch_ns = monotonic_ns_source()
        self._runtimes: dict[tuple[str, str], BrainvisionRuntime] = {}
        self._initialized_runtime_keys: set[tuple[str, str]] = set()

    @property
    def runtime_count(self) -> int:
        """Return the process-local Brainvision runtime count."""

        return len(self._runtimes)

    def _key(self, workspace_id: str, agent_id: str) -> tuple[str, str]:
        return (workspace_id, agent_id)

    def _validate_identifiers(self, workspace_id: object, agent_id: object) -> tuple[str, str]:
        if type(workspace_id) is not str:
            raise BrainvisionLifecycleError("workspace_id", "invalid_identifier")
        if type(agent_id) is not str:
            raise BrainvisionLifecycleError("agent_id", "invalid_identifier")
        try:
            return (
                safe_slug(workspace_id, "workspace_id"),
                safe_slug(agent_id, "agent_id"),
            )
        except ValueError as error:
            raise BrainvisionLifecycleError("identifier", "invalid_identifier") from error

    def _load_known_identity(self, workspace_id: str, agent_id: str) -> AgentIdentity:
        try:
            identity = self._identity_store.load(workspace_id, agent_id)
        except Exception as error:
            raise BrainvisionLifecycleError("identity", "agent_identity_invalid") from error
        if identity is None:
            raise BrainvisionLifecycleError("agent", "unknown_agent")
        if (
            type(identity) is not AgentIdentity
            or identity.workspace_id != workspace_id
            or identity.agent_id != agent_id
        ):
            raise BrainvisionLifecycleError("identity", "agent_identity_invalid")
        return identity

    @contextmanager
    def _locked_known_agent(
        self,
        workspace_id: object,
        agent_id: object,
    ) -> Iterator[tuple[str, str]]:
        """Validate identity before lock allocation and revalidate under lock."""

        workspace_id, agent_id = self._validate_identifiers(workspace_id, agent_id)
        self._load_known_identity(workspace_id, agent_id)
        lock = self._lock_manager.agent_lock(workspace_id, agent_id)
        with lock:
            self._load_known_identity(workspace_id, agent_id)
            yield self._key(workspace_id, agent_id)

    def _configuration_path(self, workspace_id: str, agent_id: str) -> str:
        return brainvision_configuration_path(self._data_dir, workspace_id, agent_id)

    def _sidecar_path(self, workspace_id: str, agent_id: str) -> str:
        return vhe_sidecar_path(self._data_dir, workspace_id, agent_id)

    def _delete_contained_file(self, path: str, *, missing_ok: bool) -> None:
        ensure_within_base(path, self._data_dir)
        try:
            os.unlink(path)
        except FileNotFoundError:
            if not missing_ok:
                raise

    def _load_artifacts_locked(
        self,
        workspace_id: str,
        agent_id: str,
    ) -> tuple[BrainvisionConfigurationV1 | None, VheSidecarV1 | None]:
        try:
            configuration = load_brainvision_configuration(
                self._data_dir, workspace_id, agent_id
            )
        except Exception as error:
            raise BrainvisionLifecycleError(
                "configuration", "sidecar_integrity_failure"
            ) from error
        try:
            sidecar = load_vhe_sidecar(self._data_dir, workspace_id, agent_id)
        except Exception as error:
            raise BrainvisionLifecycleError(
                "sidecar", "sidecar_integrity_failure"
            ) from error
        return configuration, sidecar

    def _sidecar_for(
        self,
        *,
        configuration: BrainvisionConfigurationV1,
        vhe_state: VheState,
        committed_active_time_ns: int,
        accepted_source_sequence: int,
    ) -> VheSidecarV1:
        return replace(
            fresh_vhe_sidecar(configuration),
            accepted_source_sequence=accepted_source_sequence,
            committed_active_time_ns=committed_active_time_ns,
            vhe_state=vhe_state,
        )

    def _repair_watermark_locked(
        self,
        workspace_id: str,
        agent_id: str,
        configuration: BrainvisionConfigurationV1,
        sidecar: VheSidecarV1,
    ) -> BrainvisionConfigurationV1:
        candidate = replace(
            configuration,
            last_accepted_source_sequence=sidecar.accepted_source_sequence,
        )
        try:
            validate_configuration_replacement(configuration, candidate)
            write_brainvision_configuration(
                self._data_dir, workspace_id, agent_id, candidate
            )
        except Exception as error:
            raise BrainvisionLifecycleError(
                "configuration", "durability_failure"
            ) from error
        return candidate

    def _build_runtime(
        self,
        configuration: BrainvisionConfigurationV1,
        sidecar: VheSidecarV1,
        *,
        active_clock_origin_ns: int | None = None,
    ) -> BrainvisionRuntime:
        try:
            if configuration.lifecycle_status == LIFECYCLE_ACTIVE:
                clock = VisualClock.from_active(
                    committed_active_time_ns=sidecar.committed_active_time_ns,
                    monotonic_ns_source=self._monotonic_ns_source,
                    process_local_origin_ns=active_clock_origin_ns,
                )
            elif configuration.lifecycle_status == LIFECYCLE_SUSPENDED:
                clock = VisualClock.from_frozen(
                    committed_active_time_ns=sidecar.committed_active_time_ns,
                    monotonic_ns_source=self._monotonic_ns_source,
                )
            else:
                raise BrainvisionLifecycleError(
                    "lifecycle_status", "invalid_lifecycle_transition"
                )
            return BrainvisionRuntime(
                configuration=configuration,
                vhe_state=sidecar.vhe_state,
                visual_clock=clock,
            )
        except BrainvisionLifecycleError:
            raise
        except Exception as error:
            raise BrainvisionLifecycleError(
                "runtime", "runtime_allocation_failure"
            ) from error

    def _runtime_matches(
        self,
        runtime: BrainvisionRuntime,
        configuration: BrainvisionConfigurationV1,
        sidecar: VheSidecarV1,
    ) -> bool:
        expected_accumulating = configuration.lifecycle_status == LIFECYCLE_ACTIVE
        return (
            runtime.configuration == configuration
            and runtime.vhe_state == sidecar.vhe_state
            and runtime.visual_clock.committed_active_time_ns
            == sidecar.committed_active_time_ns
            and runtime.visual_clock.is_accumulating == expected_accumulating
        )

    def _recover_locked(
        self,
        workspace_id: str,
        agent_id: str,
        key: tuple[str, str],
    ) -> BrainvisionConfigurationV1 | None:
        """Reconcile durable artifacts and construct only lawful runtime state."""

        configuration, sidecar = self._load_artifacts_locked(workspace_id, agent_id)
        if configuration is None:
            self._runtimes.pop(key, None)
            self._initialized_runtime_keys.discard(key)
            if sidecar is None:
                return None
            raise BrainvisionLifecycleError("sidecar", "sidecar_integrity_failure")

        if configuration.lifecycle_status == LIFECYCLE_DISABLED:
            self._runtimes.pop(key, None)
            self._initialized_runtime_keys.discard(key)
            if sidecar is None:
                return configuration
            try:
                relation = validate_configuration_sidecar_compatibility(
                    configuration, sidecar
                )
            except Exception as error:
                raise BrainvisionLifecycleError(
                    "sidecar", "sidecar_integrity_failure"
                ) from error
            if relation == SIDECAR_AHEAD:
                configuration = self._repair_watermark_locked(
                    workspace_id, agent_id, configuration, sidecar
                )
            try:
                self._delete_contained_file(
                    self._sidecar_path(workspace_id, agent_id), missing_ok=False
                )
            except Exception as error:
                raise BrainvisionLifecycleError(
                    "sidecar",
                    "durability_failure",
                    durable_committed=relation == SIDECAR_AHEAD,
                ) from error
            return configuration

        if sidecar is None:
            self._runtimes.pop(key, None)
            raise BrainvisionLifecycleError("sidecar", "sidecar_missing")

        try:
            relation = validate_configuration_sidecar_compatibility(configuration, sidecar)
        except Exception as error:
            self._runtimes.pop(key, None)
            raise BrainvisionLifecycleError(
                "configuration_sidecar", "configuration_sidecar_incompatible"
            ) from error

        if relation == CONFIG_AHEAD:
            self._runtimes.pop(key, None)
            raise BrainvisionLifecycleError("sequence", "config_ahead")
        if relation == SIDECAR_AHEAD:
            configuration = self._repair_watermark_locked(
                workspace_id, agent_id, configuration, sidecar
            )

        runtime = self._runtimes.get(key)
        if runtime is None or not self._runtime_matches(runtime, configuration, sidecar):
            self._runtimes.pop(key, None)
            active_clock_origin_ns = (
                self._manager_reconstruction_epoch_ns
                if (
                    configuration.lifecycle_status == LIFECYCLE_ACTIVE
                    and key not in self._initialized_runtime_keys
                )
                else None
            )
            runtime = self._build_runtime(
                configuration,
                sidecar,
                active_clock_origin_ns=active_clock_origin_ns,
            )
            self._runtimes[key] = runtime
            self._initialized_runtime_keys.add(key)
        return configuration

    def _require_configuration(
        self,
        configuration: BrainvisionConfigurationV1 | None,
    ) -> BrainvisionConfigurationV1:
        if configuration is None:
            raise BrainvisionLifecycleError("configuration", "configuration_absent")
        return configuration

    def _stage_active_runtime(
        self,
        runtime: BrainvisionRuntime,
    ) -> tuple[VisualClock, VheState, int, int]:
        if not runtime.visual_clock.is_accumulating:
            raise BrainvisionLifecycleError(
                "lifecycle_status", "invalid_lifecycle_transition"
            )
        old_time = runtime.visual_clock.committed_active_time_ns
        staged_clock = VisualClock(
            committed_active_time_ns=old_time,
            process_local_origin_ns=runtime.visual_clock.process_local_origin_ns,
            monotonic_ns_source=self._monotonic_ns_source,
        )
        cutoff = staged_clock.resolve_and_rebase()
        delta = cutoff - old_time
        if delta < 0:
            raise BrainvisionLifecycleError("clock", "recovery_required")
        return (
            staged_clock,
            evolve_vhe_state_as_of(runtime.vhe_state, delta),
            cutoff,
            delta,
        )

    def configure_brainvision(
        self,
        workspace_id: str,
        agent_id: str,
        stream_identity: str,
        adapter_contract_id: str,
        theta: int,
    ) -> BrainvisionConfigurationV1:
        with self._locked_known_agent(workspace_id, agent_id) as key:
            configuration = self._recover_locked(workspace_id, agent_id, key)
            if configuration is not None:
                raise BrainvisionLifecycleError(
                    "configuration", "configuration_already_exists"
                )
            if key in self._runtimes:
                raise BrainvisionLifecycleError("runtime", "recovery_required")
            candidate = fresh_disabled_brainvision_configuration(
                stream_identity=stream_identity,
                adapter_contract_id=adapter_contract_id,
                theta=theta,
            )
            try:
                write_brainvision_configuration(
                    self._data_dir, workspace_id, agent_id, candidate
                )
            except Exception as error:
                raise BrainvisionLifecycleError(
                    "configuration", "durability_failure"
                ) from error
            return candidate

    def delete_brainvision_configuration(
        self,
        workspace_id: str,
        agent_id: str,
    ) -> None:
        with self._locked_known_agent(workspace_id, agent_id) as key:
            configuration = self._require_configuration(
                self._recover_locked(workspace_id, agent_id, key)
            )
            if configuration.lifecycle_status != LIFECYCLE_DISABLED:
                raise BrainvisionLifecycleError(
                    "lifecycle_status", "invalid_lifecycle_transition"
                )
            if key in self._runtimes:
                raise BrainvisionLifecycleError("runtime", "recovery_required")
            try:
                self._delete_contained_file(
                    self._configuration_path(workspace_id, agent_id), missing_ok=False
                )
            except Exception as error:
                raise BrainvisionLifecycleError(
                    "configuration", "durability_failure"
                ) from error

    def reconfigure_disabled_profile(
        self,
        workspace_id: str,
        agent_id: str,
        theta: int,
    ) -> BrainvisionConfigurationV1:
        with self._locked_known_agent(workspace_id, agent_id) as key:
            configuration = self._require_configuration(
                self._recover_locked(workspace_id, agent_id, key)
            )
            if configuration.lifecycle_status != LIFECYCLE_DISABLED or key in self._runtimes:
                raise BrainvisionLifecycleError(
                    "lifecycle_status", "invalid_lifecycle_transition"
                )
            candidate = replace(
                configuration,
                theta=theta,
                modulation_profile_id=modulation_profile_id(theta),
            )
            try:
                validate_configuration_replacement(configuration, candidate)
                write_brainvision_configuration(
                    self._data_dir, workspace_id, agent_id, candidate
                )
            except Exception as error:
                raise BrainvisionLifecycleError(
                    "configuration", "durability_failure"
                ) from error
            return candidate

    def enable(self, workspace_id: str, agent_id: str) -> BrainvisionConfigurationV1:
        with self._locked_known_agent(workspace_id, agent_id) as key:
            configuration = self._require_configuration(
                self._recover_locked(workspace_id, agent_id, key)
            )
            if configuration.lifecycle_status == LIFECYCLE_SUSPENDED:
                raise BrainvisionLifecycleError(
                    "lifecycle_status", "invalid_lifecycle_transition"
                )
            if configuration.lifecycle_status == LIFECYCLE_ACTIVE:
                return configuration
            if key in self._runtimes:
                raise BrainvisionLifecycleError("runtime", "recovery_required")

            sidecar = fresh_vhe_sidecar(configuration)
            try:
                write_vhe_sidecar(self._data_dir, workspace_id, agent_id, sidecar)
            except Exception as error:
                raise BrainvisionLifecycleError("sidecar", "durability_failure") from error

            active_configuration = replace(
                configuration, lifecycle_status=LIFECYCLE_ACTIVE
            )
            try:
                validate_configuration_replacement(configuration, active_configuration)
                write_brainvision_configuration(
                    self._data_dir, workspace_id, agent_id, active_configuration
                )
            except Exception as error:
                raise BrainvisionLifecycleError(
                    "configuration", "durability_failure", durable_committed=True
                ) from error
            try:
                self._runtimes[key] = self._build_runtime(active_configuration, sidecar)
                self._initialized_runtime_keys.add(key)
            except BrainvisionLifecycleError as error:
                self._runtimes.pop(key, None)
                raise BrainvisionLifecycleError(
                    error.field,
                    error.reason,
                    durable_committed=True,
                ) from error
            return active_configuration

    def suspend(self, workspace_id: str, agent_id: str) -> BrainvisionConfigurationV1:
        with self._locked_known_agent(workspace_id, agent_id) as key:
            configuration = self._require_configuration(
                self._recover_locked(workspace_id, agent_id, key)
            )
            if configuration.lifecycle_status == LIFECYCLE_DISABLED:
                raise BrainvisionLifecycleError(
                    "lifecycle_status", "invalid_lifecycle_transition"
                )
            if configuration.lifecycle_status == LIFECYCLE_SUSPENDED:
                return configuration
            runtime = self._runtimes[key]
            staged_clock, staged_state, cutoff, _ = self._stage_active_runtime(runtime)
            staged_sidecar = self._sidecar_for(
                configuration=configuration,
                vhe_state=staged_state,
                committed_active_time_ns=cutoff,
                accepted_source_sequence=configuration.last_accepted_source_sequence,
            )
            try:
                write_vhe_sidecar(
                    self._data_dir, workspace_id, agent_id, staged_sidecar
                )
            except Exception as error:
                raise BrainvisionLifecycleError("sidecar", "durability_failure") from error

            suspended_configuration = replace(
                configuration, lifecycle_status=LIFECYCLE_SUSPENDED
            )
            try:
                validate_configuration_replacement(configuration, suspended_configuration)
                write_brainvision_configuration(
                    self._data_dir, workspace_id, agent_id, suspended_configuration
                )
            except Exception as error:
                runtime.vhe_state = staged_state
                runtime.visual_clock = staged_clock
                raise BrainvisionLifecycleError(
                    "configuration", "durability_failure", durable_committed=True
                ) from error

            runtime.configuration = suspended_configuration
            runtime.vhe_state = staged_state
            runtime.visual_clock = VisualClock.from_frozen(
                committed_active_time_ns=cutoff,
                monotonic_ns_source=self._monotonic_ns_source,
            )
            return suspended_configuration

    def resume(self, workspace_id: str, agent_id: str) -> BrainvisionConfigurationV1:
        with self._locked_known_agent(workspace_id, agent_id) as key:
            configuration = self._require_configuration(
                self._recover_locked(workspace_id, agent_id, key)
            )
            if configuration.lifecycle_status != LIFECYCLE_SUSPENDED:
                raise BrainvisionLifecycleError(
                    "lifecycle_status", "invalid_lifecycle_transition"
                )
            active_configuration = replace(
                configuration, lifecycle_status=LIFECYCLE_ACTIVE
            )
            try:
                validate_configuration_replacement(configuration, active_configuration)
                write_brainvision_configuration(
                    self._data_dir, workspace_id, agent_id, active_configuration
                )
            except Exception as error:
                raise BrainvisionLifecycleError(
                    "configuration", "durability_failure"
                ) from error
            try:
                sidecar = load_vhe_sidecar(self._data_dir, workspace_id, agent_id)
            except Exception as error:
                self._runtimes.pop(key, None)
                raise BrainvisionLifecycleError(
                    "sidecar", "runtime_allocation_failure", durable_committed=True
                ) from error
            if sidecar is None:
                self._runtimes.pop(key, None)
                raise BrainvisionLifecycleError(
                    "sidecar", "runtime_allocation_failure", durable_committed=True
                )
            try:
                self._runtimes[key] = self._build_runtime(active_configuration, sidecar)
                self._initialized_runtime_keys.add(key)
            except BrainvisionLifecycleError as error:
                self._runtimes.pop(key, None)
                raise BrainvisionLifecycleError(
                    error.field,
                    error.reason,
                    durable_committed=True,
                ) from error
            return active_configuration

    def reset(self, workspace_id: str, agent_id: str) -> BrainvisionConfigurationV1:
        with self._locked_known_agent(workspace_id, agent_id) as key:
            configuration = self._require_configuration(
                self._recover_locked(workspace_id, agent_id, key)
            )
            if configuration.lifecycle_status == LIFECYCLE_DISABLED:
                raise BrainvisionLifecycleError(
                    "lifecycle_status", "invalid_lifecycle_transition"
                )
            sidecar = fresh_vhe_sidecar(configuration)
            try:
                write_vhe_sidecar(self._data_dir, workspace_id, agent_id, sidecar)
            except Exception as error:
                raise BrainvisionLifecycleError("sidecar", "durability_failure") from error
            try:
                self._runtimes[key] = self._build_runtime(configuration, sidecar)
                self._initialized_runtime_keys.add(key)
            except BrainvisionLifecycleError as error:
                self._runtimes.pop(key, None)
                raise BrainvisionLifecycleError(
                    error.field,
                    error.reason,
                    durable_committed=True,
                ) from error
            return configuration

    def disable(self, workspace_id: str, agent_id: str) -> BrainvisionConfigurationV1:
        with self._locked_known_agent(workspace_id, agent_id) as key:
            configuration = self._require_configuration(
                self._recover_locked(workspace_id, agent_id, key)
            )
            if configuration.lifecycle_status == LIFECYCLE_DISABLED:
                return configuration
            sidecar = load_vhe_sidecar(self._data_dir, workspace_id, agent_id)
            if sidecar is None:
                self._runtimes.pop(key, None)
                raise BrainvisionLifecycleError("sidecar", "sidecar_missing")
            if configuration.last_accepted_source_sequence < sidecar.accepted_source_sequence:
                raise BrainvisionLifecycleError("sequence", "config_ahead")
            disabled_configuration = replace(
                configuration, lifecycle_status=LIFECYCLE_DISABLED
            )
            try:
                validate_configuration_replacement(configuration, disabled_configuration)
                write_brainvision_configuration(
                    self._data_dir, workspace_id, agent_id, disabled_configuration
                )
            except Exception as error:
                raise BrainvisionLifecycleError(
                    "configuration", "durability_failure"
                ) from error

            try:
                self._delete_contained_file(
                    self._sidecar_path(workspace_id, agent_id), missing_ok=False
                )
            except Exception as error:
                self._runtimes.pop(key, None)
                raise BrainvisionLifecycleError(
                    "sidecar", "durability_failure", durable_committed=True
                ) from error
            self._runtimes.pop(key, None)
            self._initialized_runtime_keys.discard(key)
            return disabled_configuration

    @contextmanager
    def active_transaction(
        self,
        workspace_id: str,
        agent_id: str,
    ) -> Iterator[BrainvisionActiveTransaction]:
        """Yield one lock-held Phase-11 successor-commit transaction."""

        with self._locked_known_agent(workspace_id, agent_id) as key:
            configuration = self._require_configuration(
                self._recover_locked(workspace_id, agent_id, key)
            )
            if configuration.lifecycle_status != LIFECYCLE_ACTIVE:
                raise BrainvisionLifecycleError(
                    "lifecycle_status", "invalid_lifecycle_transition"
                )
            runtime = self._runtimes[key]
            staged_clock, _, cutoff, delta = self._stage_active_runtime(runtime)
            transaction = BrainvisionActiveTransaction(
                manager=self,
                key=key,
                configuration=configuration,
                base_vhe_state=runtime.vhe_state,
                prior_committed_active_time_ns=runtime.visual_clock.committed_active_time_ns,
                cutoff_active_time_ns=cutoff,
                elapsed_active_time_ns=delta,
                replay_watermark=configuration.last_accepted_source_sequence,
                staged_clock=staged_clock,
            )
            try:
                yield transaction
            finally:
                transaction._close()

    def _commit_successor_locked(
        self,
        *,
        transaction: BrainvisionActiveTransaction,
        successor_vhe_state: VheState,
        accepted_source_sequence: int,
    ) -> BrainvisionRuntimeSnapshot:
        if type(successor_vhe_state) is not VheState:
            raise TypeError("successor_vhe_state must be VheState")
        configuration = transaction.configuration
        candidate = replace(
            configuration,
            last_accepted_source_sequence=accepted_source_sequence,
        )
        try:
            validate_configuration_replacement(configuration, candidate)
        except Exception as error:
            raise BrainvisionLifecycleError(
                "accepted_source_sequence", "invalid_successor"
            ) from error
        sidecar = self._sidecar_for(
            configuration=configuration,
            vhe_state=successor_vhe_state,
            committed_active_time_ns=transaction.cutoff_active_time_ns,
            accepted_source_sequence=accepted_source_sequence,
        )
        workspace_id, agent_id = transaction._key
        try:
            write_vhe_sidecar(self._data_dir, workspace_id, agent_id, sidecar)
        except Exception as error:
            raise BrainvisionLifecycleError("sidecar", "durability_failure") from error

        try:
            write_brainvision_configuration(
                self._data_dir, workspace_id, agent_id, candidate
            )
        except Exception as error:
            self._runtimes.pop(transaction._key, None)
            raise BrainvisionLifecycleError(
                "configuration", "recovery_required", durable_committed=True
            ) from error

        runtime = self._runtimes.get(transaction._key)
        if runtime is None:
            raise BrainvisionLifecycleError("runtime", "recovery_required")
        runtime.configuration = candidate
        runtime.vhe_state = successor_vhe_state
        runtime.visual_clock = transaction._staged_clock
        return BrainvisionRuntimeSnapshot(
            configuration=candidate,
            vhe_state=successor_vhe_state,
            active_time_ns=transaction.cutoff_active_time_ns,
        )

    def runtime_snapshot(
        self,
        workspace_id: str,
        agent_id: str,
    ) -> BrainvisionRuntimeSnapshot:
        """Return a pure internal snapshot; it does not project or persist."""

        with self._locked_known_agent(workspace_id, agent_id) as key:
            configuration = self._require_configuration(
                self._recover_locked(workspace_id, agent_id, key)
            )
            if configuration.lifecycle_status == LIFECYCLE_DISABLED:
                raise BrainvisionLifecycleError(
                    "lifecycle_status", "invalid_lifecycle_transition"
                )
            runtime = self._runtimes[key]
            if configuration.lifecycle_status == LIFECYCLE_ACTIVE:
                active_time_ns = runtime.visual_clock.read_active_time_ns()
                delta = active_time_ns - runtime.visual_clock.committed_active_time_ns
                state = evolve_vhe_state_as_of(runtime.vhe_state, delta)
            else:
                active_time_ns = runtime.visual_clock.committed_active_time_ns
                state = runtime.vhe_state
            return BrainvisionRuntimeSnapshot(
                configuration=configuration,
                vhe_state=state,
                active_time_ns=active_time_ns,
            )

    def shutdown(self) -> None:
        """Best-effort non-throwing flush and teardown for all local runtimes."""

        for key in list(self._runtimes):
            workspace_id, agent_id = key
            try:
                with self._locked_known_agent(workspace_id, agent_id):
                    runtime = self._runtimes.get(key)
                    if runtime is None:
                        continue
                    if runtime.configuration.lifecycle_status == LIFECYCLE_ACTIVE:
                        try:
                            staged_clock, staged_state, cutoff, _ = (
                                self._stage_active_runtime(runtime)
                            )
                            sidecar = self._sidecar_for(
                                configuration=runtime.configuration,
                                vhe_state=staged_state,
                                committed_active_time_ns=cutoff,
                                accepted_source_sequence=(
                                    runtime.configuration.last_accepted_source_sequence
                                ),
                            )
                            write_vhe_sidecar(
                                self._data_dir, workspace_id, agent_id, sidecar
                            )
                        except Exception as error:
                            _LOG.error(
                                "Brainvision shutdown sidecar flush failed for %s/%s: %s",
                                workspace_id,
                                agent_id,
                                error,
                            )
                    self._runtimes.pop(key, None)
            except Exception as error:
                _LOG.error(
                    "Brainvision shutdown failed for %s/%s: %s",
                    workspace_id,
                    agent_id,
                    error,
                )
                self._runtimes.pop(key, None)


__all__ = (
    "BrainvisionActiveTransaction",
    "BrainvisionLifecycleError",
    "BrainvisionLifecycleManager",
    "BrainvisionRuntime",
    "BrainvisionRuntimeSnapshot",
)
