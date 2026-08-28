"""No-network coverage for benchmark provider-error redaction."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.bench_adapters import AdapterUnavailable, redact_provider_error_text
from tools.bench_adapters.anthropic_adapter import AnthropicAdapter
from tools.bench_adapters.openai_adapter import OpenAIAdapter
from tools.bench_adapters.openrouter_adapter import OpenRouterAdapter
import tools.run_character_truth_bench as truth_bench


FAKE_SECRETS = (
    "sk-ant-TEST-ONLY-NOT-A-KEY",
    "sk-proj-TEST-ONLY-NOT-A-KEY",
    "sk-or-v1-TEST-ONLY-NOT-A-KEY",
)
FAKE_SECRET_TEXT = " ".join(FAKE_SECRETS)
REDACTION_MARKER = "[REDACTED_API_KEY]"
NON_SECRET_DETAIL = "provider remains actionable"


class _FailingCompletions:
    def create(self, **_kwargs):
        raise RuntimeError(f"{NON_SECRET_DETAIL}: {FAKE_SECRET_TEXT}")


class _ReturningCompletions:
    def __init__(self, response):
        self._response = response

    def create(self, **_kwargs):
        return self._response


def _configure_fake_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_SECRETS[0])
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_SECRETS[1])
    monkeypatch.setenv("OPENROUTER_API_KEY", FAKE_SECRETS[2])


def _assert_redacted(text: object) -> None:
    text = str(text)
    for secret in FAKE_SECRETS:
        assert secret not in text
    assert REDACTION_MARKER in text
    assert NON_SECRET_DETAIL in text


def _assert_no_secret(text: object) -> None:
    text = str(text)
    for secret in FAKE_SECRETS:
        assert secret not in text


def _matrix() -> truth_bench.Matrix:
    return truth_bench.Matrix(
        version=1,
        server_url="http://unused.invalid",
        workspace_id="redaction-test",
        agent_id_prefix="test_",
        wrapper=truth_bench.WrapperConfig(template="System: {persona_seed}"),
        characters=[
            truth_bench.Character(
                id="character",
                name="Character",
                truth_contract="contract",
                expected_behavior="expected",
                persona_seed="seed",
            )
        ],
        scenarios=[truth_bench.Scenario(id="scenario", prompt="prompt", applies_to=["character"])],
        run_config=truth_bench.RunConfig(
            runs_per_cell=1,
            providers=["anthropic"],
            save_transcripts=True,
            save_context_dumps=True,
            save_character_state_snapshots=False,
            ingest_after_each_turn=False,
        ),
    )


def _failed_adapter() -> object:
    class _Adapter:
        def chat(self, _system: str, _messages: list[dict]) -> str:
            raise AdapterUnavailable(f"{NON_SECRET_DETAIL}: {FAKE_SECRET_TEXT}")

    return _Adapter()


def _adapter_with_client(adapter_type, client):
    adapter = object.__new__(adapter_type)
    adapter.model = "test-model"
    adapter._client = client
    return adapter


@pytest.mark.parametrize(
    ("adapter_type", "client"),
    [
        (AnthropicAdapter, lambda: SimpleNamespace(messages=_FailingCompletions())),
        (
            OpenAIAdapter,
            lambda: SimpleNamespace(
                chat=SimpleNamespace(completions=_FailingCompletions())
            ),
        ),
        (
            OpenRouterAdapter,
            lambda: SimpleNamespace(
                chat=SimpleNamespace(completions=_FailingCompletions())
            ),
        ),
    ],
)
def test_adapter_errors_redact_configured_credentials(
    monkeypatch: pytest.MonkeyPatch, adapter_type, client
) -> None:
    _configure_fake_credentials(monkeypatch)
    adapter = _adapter_with_client(adapter_type, client())

    with pytest.raises(AdapterUnavailable) as raised:
        adapter.chat("system", [])

    _assert_redacted(raised.value)


@pytest.mark.parametrize(
    ("adapter_type", "client", "expected"),
    [
        (
            AnthropicAdapter,
            lambda: SimpleNamespace(
                messages=_ReturningCompletions(
                    SimpleNamespace(content=[SimpleNamespace(text="anthropic success")])
                )
            ),
            "anthropic success",
        ),
        (
            OpenAIAdapter,
            lambda: SimpleNamespace(
                chat=SimpleNamespace(
                    completions=_ReturningCompletions(
                        SimpleNamespace(
                            choices=[SimpleNamespace(message=SimpleNamespace(content="openai success"))]
                        )
                    )
                )
            ),
            "openai success",
        ),
        (
            OpenRouterAdapter,
            lambda: SimpleNamespace(
                chat=SimpleNamespace(
                    completions=_ReturningCompletions(
                        SimpleNamespace(
                            choices=[SimpleNamespace(message=SimpleNamespace(content="openrouter success"))]
                        )
                    )
                )
            ),
            "openrouter success",
        ),
    ],
)
def test_adapter_success_behavior_is_unchanged(adapter_type, client, expected: str) -> None:
    adapter = _adapter_with_client(adapter_type, client())
    assert adapter.chat("system", []) == expected


@pytest.mark.parametrize(
    ("adapter_type", "env_name"),
    [
        (AnthropicAdapter, "ANTHROPIC_API_KEY"),
        (OpenAIAdapter, "OPENAI_API_KEY"),
        (OpenRouterAdapter, "OPENROUTER_API_KEY"),
    ],
)
def test_missing_key_messages_remain_actionable(
    monkeypatch: pytest.MonkeyPatch, adapter_type, env_name: str
) -> None:
    monkeypatch.delenv(env_name, raising=False)

    with pytest.raises(AdapterUnavailable) as raised:
        adapter_type(model="test-model")

    assert env_name in str(raised.value)


def test_shared_sanitizer_accepts_arbitrary_error_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_fake_credentials(monkeypatch)
    _assert_redacted(redact_provider_error_text(RuntimeError(f"{NON_SECRET_DETAIL}: {FAKE_SECRET_TEXT}")))


def test_truth_bench_redacts_turn_and_persistence_sinks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _configure_fake_credentials(monkeypatch)
    matrix = _matrix()
    monkeypatch.setattr(truth_bench, "get_adapter", lambda _provider, _model: _failed_adapter())

    record = truth_bench.run_cell(
        matrix,
        matrix.characters[0],
        "anthropic",
        1,
        object(),
        tmp_path,
        bench_mode="controlled_role_baseline",
    )
    truth_bench.write_summary(matrix, [record], tmp_path)

    _assert_redacted(record.turns[0].error)
    transcript = next((tmp_path / "transcripts").glob("*.json")).read_text(encoding="utf-8")
    summary_csv = (tmp_path / "scores" / "summary.csv").read_text(encoding="utf-8")
    summary_json = (tmp_path / "scores" / "summary.json").read_text(encoding="utf-8")
    _assert_redacted(transcript)
    _assert_redacted(summary_csv)
    _assert_redacted(summary_json)

    context_dump = next((tmp_path / "context_dumps").glob("*.txt")).read_text(encoding="utf-8")
    assert "System: seed" in context_dump
    assert "MESSAGE TAPE" in context_dump
    assert "prompt" not in context_dump
    for secret in FAKE_SECRETS:
        assert secret not in context_dump


def test_truth_bench_redacts_cell_error_and_summary_sinks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _configure_fake_credentials(monkeypatch)
    matrix = _matrix()

    def _unavailable(_provider: str, _model: str):
        raise AdapterUnavailable(f"{NON_SECRET_DETAIL}: {FAKE_SECRET_TEXT}")

    monkeypatch.setattr(truth_bench, "get_adapter", _unavailable)
    record = truth_bench.run_cell(
        matrix,
        matrix.characters[0],
        "anthropic",
        1,
        object(),
        tmp_path,
        bench_mode="controlled_role_baseline",
    )
    truth_bench.write_summary(matrix, [record], tmp_path)

    _assert_redacted(record.cell_error)
    assert not (tmp_path / "transcripts").exists()
    _assert_redacted((tmp_path / "scores" / "summary.csv").read_text(encoding="utf-8"))
    _assert_redacted((tmp_path / "scores" / "summary.json").read_text(encoding="utf-8"))


def test_truth_bench_redacts_console_and_traceback_and_keeps_config_snapshot_safe(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure_fake_credentials(monkeypatch)
    matrix = _matrix()
    monkeypatch.setattr(truth_bench, "_load_env_file", lambda _path: 0)
    monkeypatch.setattr(truth_bench, "load_matrix", lambda _path: matrix)

    def _unavailable(_provider: str, _model: str):
        raise AdapterUnavailable(f"{NON_SECRET_DETAIL}: {FAKE_SECRET_TEXT}")

    monkeypatch.setattr(truth_bench, "get_adapter", _unavailable)
    assert truth_bench.main(
        [
            "--matrix", str(tmp_path / "unused.yaml"),
            "--out", str(tmp_path / "dry-run"),
            "--bench-mode", "controlled_role_baseline",
            "--dry-run",
        ]
    ) == 0
    dry_run = capsys.readouterr()
    _assert_redacted(dry_run.out)
    assert dry_run.err == ""

    snapshot_path = next((tmp_path / "dry-run").glob("*/config_snapshot.json"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["env_provider_keys_present"] == {
        "ANTHROPIC_API_KEY": True,
        "OPENROUTER_API_KEY": True,
        "OPENAI_API_KEY": True,
    }
    for secret in FAKE_SECRETS:
        assert secret not in snapshot_path.read_text(encoding="utf-8")

    def _outer_failure(*_args, **_kwargs):
        try:
            raise RuntimeError(f"{NON_SECRET_DETAIL}: {FAKE_SECRET_TEXT}")
        except RuntimeError as exc:
            raise AdapterUnavailable(f"wrapped provider failure: {FAKE_SECRET_TEXT}") from exc

    monkeypatch.setattr(truth_bench, "run_cell", _outer_failure)
    assert truth_bench.main(
        [
            "--matrix", str(tmp_path / "unused.yaml"),
            "--out", str(tmp_path / "outer"),
            "--bench-mode", "controlled_role_baseline",
        ]
    ) == 0
    outer = capsys.readouterr()
    _assert_no_secret(outer.out)
    assert REDACTION_MARKER in outer.out
    assert "wrapped provider failure" in outer.out
    _assert_redacted(outer.err)
    assert "Traceback (most recent call last):" in outer.err
    assert "RuntimeError" in outer.err
    assert "AdapterUnavailable" in outer.err
