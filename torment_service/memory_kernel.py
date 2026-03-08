# torment_service/memory_kernel.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .embeddings import Embedder, HashEmbedding
from .summarizer import summarize

# ✅ correct imports for YOUR repo layout (kernel/*)
from .kernel.model_core import ModelParams, ModelState, TriOctaPhaseLockModel
from .kernel.phase_triad_sync import triad_coherence
from .kernel.identity_rules import label_for_identity
from .kernel.su3_basis import project_to_uxy


def _wrap_pi(a: float) -> float:
    return float((a + np.pi) % (2 * np.pi) - np.pi)


@dataclass
class KernelSignals:
    write_intent: bool
    memory_type: str
    strength: float
    confidence: float
    half_life: float
    promotion_score: float
    links: List[str]
    stability_delta: float


@dataclass
class CorridorMonitor:
    prev_xy: Optional[np.ndarray] = None
    prev_uxy: Optional[np.ndarray] = None
    tear_score_ema: float = 0.0
    align_ema: float = 0.0
    prox_ema: float = 0.0     # 0..1
    surv_ema: float = 0.0     # 0..3 (clipped)
    coh_ema: float = 0.0      # optional coherence smoothing


class TriOctaMemoryKernel:
    """
    Tri-Octa connected memory kernel (Option A mechanics):
      - observation -> embed -> Omega blend -> model.step()
      - mechanics coherence: dispersion-based (single source)
      - corridor: tangent alignment from torus XY + uxy jump
      - metastability: survival is decaying memory, not hard reset
    """

    def __init__(self, params: Optional[ModelParams] = None, embedder: Optional[Embedder] = None) -> None:
        self.params = params or ModelParams()
        self.model = TriOctaPhaseLockModel(self.params)
        self.embedder = embedder or HashEmbedding()
        self.mon = CorridorMonitor()

        # Tunables (safe defaults)
        self.CORR_THR = 0.80          # |dot_align| threshold for corridor membership
        self.COH_FLOOR = 0.05         # keep a low-end signal
        self.DISP_SCALE = 7.0e-4      # dispersion -> coherence sensitivity
        self.PROX_ALPHA = 0.10        # EMA for proximity
        self.SURV_DECAY = 0.985       # per-step decay of survival memory
        self.SURV_GAIN = 0.06         # add when in corridor (scaled by proximity)
        self.COH_SMOOTH = 0.90        # 0 disables; e.g., 0.90 enables smoothing EMA

    # ----------------------------
    # Embedding -> Omega
    # ----------------------------
    def _omega_from_embedding(self, emb: np.ndarray) -> np.ndarray:
        e = np.asarray(emb, dtype=float).reshape(-1)
        if e.size < 6:
            e = np.pad(e, (0, 6 - e.size))
        w = np.abs(e[:3]) + 1e-6
        w = w / np.sum(w)
        phases = (e[3:6] * np.pi)
        Omega = np.sqrt(w) * (np.cos(phases) + 1j * np.sin(phases))
        return Omega.astype(np.complex128)

    def init_state(self, seed_text: str = "boot",
                   character_modulation: Optional[Dict[str, Any]] = None) -> ModelState:
        if character_modulation and "omega_init" in character_modulation:
            Omega = np.asarray(character_modulation["omega_init"], dtype=np.complex128)
        else:
            emb = self.embedder.embed(seed_text)
            Omega = self._omega_from_embedding(emb)
        state = ModelState(Omega=Omega)
        # Store character modulation for use during process()
        state._char_mod = character_modulation or {}  # type: ignore[attr-defined]
        return state

    # ----------------------------
    # Torus XY mapping (for tangent corridor)
    # ----------------------------
    @staticmethod
    def _torus_xy(phi_index: int, kappa: float) -> np.ndarray:
        phi = 2.0 * np.pi * (phi_index % 12) / 12.0
        rho = float(kappa) / (1.0 + float(kappa)) if float(kappa) != -1.0 else 0.0
        R = 2.0
        X = (R + rho * np.cos(phi)) * np.cos(phi)
        Y = (R + rho * np.cos(phi)) * np.sin(phi)
        return np.array([X, Y], dtype=float)

    # ----------------------------
    # Dispersion coherence (single source of truth)
    # ----------------------------
    def _dispersion_coherence(self, Omega: np.ndarray) -> Tuple[float, float]:
        ph = np.angle(Omega)
        d01 = _wrap_pi(float(ph[0] - ph[1]))
        d12 = _wrap_pi(float(ph[1] - ph[2]))
        d20 = _wrap_pi(float(ph[2] - ph[0]))
        disp = float(np.sqrt(np.mean(np.square([d01, d12, d20]))))
        scale = float(self.DISP_SCALE)
        coh_phase = float(np.exp(-((disp / max(scale, 1e-12)) ** 2)))
        return disp, coh_phase

    # ----------------------------
    # Main step
    # ----------------------------
    def process(self, state: ModelState, observation: str) -> Tuple[ModelState, KernelSignals, Dict[str, Any]]:
        summary = summarize(observation)
        emb = self.embedder.embed(summary)

        # inject observation into Omega (gentle blend + tiny phase jitter)
        Omega_obs = self._omega_from_embedding(emb)
        jit = float(np.clip((len(summary) - 40) / 400.0, 0.0, 1.0))
        jphi = 0.03 * jit
        rot = np.cos(jphi) + 1j * np.sin(jphi)
        Omega_obs = Omega_obs * rot
        state.Omega = (0.60 * state.Omega + 0.40 * Omega_obs)

        # advance TriOcta dynamics — apply character modulation if present
        char_mod = getattr(state, '_char_mod', {})
        if char_mod and ('g_mod' in char_mod or 'theta_lock_mod' in char_mod):
            orig_g = self.params.g
            orig_theta = self.params.theta_lock
            self.params.g = float(char_mod.get('g_mod', orig_g))
            self.params.theta_lock = float(char_mod.get('theta_lock_mod', orig_theta))
            try:
                self.model.step(state, dt=self.params.eps)
            finally:
                self.params.g = orig_g
                self.params.theta_lock = orig_theta
        else:
            self.model.step(state, dt=self.params.eps)

        # debug-only triad coherence (NOT mechanics)
        try:
            S_mag, Phi_coll, S = triad_coherence(state.Omega)
        except Exception:
            S_mag, Phi_coll, S = 0.0, 0.0, 0.0

        # mechanics coherence
        disp, coh_phase = self._dispersion_coherence(state.Omega)
        coh_raw = float(self.COH_FLOOR + (1.0 - self.COH_FLOOR) * np.clip(coh_phase, 0.0, 0.9999))
        coh = coh_raw

        # optional smoothing (ONE block only)
        a = float(self.COH_SMOOTH) if self.COH_SMOOTH else 0.0
        if a > 0.0:
            if float(self.mon.coh_ema) <= 0.0:
                self.mon.coh_ema = float(coh)
            else:
                self.mon.coh_ema = a * float(self.mon.coh_ema) + (1.0 - a) * float(coh)
            coh = float(self.mon.coh_ema)

        # labels
        cycle_stage = int(getattr(state, "cycle_stage", 0))
        identity_state = int(getattr(state, "identity_state", 0))
        id_label = label_for_identity(identity_state)

        # base bounded modulation
        write_mult = 1.0 + (0.03 if cycle_stage <= 2 else 0.0) - (0.03 if cycle_stage >= 6 else 0.0)
        write_mult *= (0.99 + 0.03 * coh)
        write_mult = float(np.clip(write_mult, 0.90, 1.10))

        proposal_mult = float(np.clip(1.01 - 0.04 * coh, 0.90, 1.10))
        bridge_p = float(np.clip(0.08 + 0.04 * coh, 0.05, 0.12))
        bridge_sim = float(np.clip(0.88 - 0.06 * coh, 0.84, 0.90))

        tri_mod: Dict[str, Any] = {
            "write_mult": write_mult,
            "proposal_mult": proposal_mult,
            "bridge_p": bridge_p,
            "bridge_sim": bridge_sim,
            "cycle_stage": float(cycle_stage),
            "identity_state": float(identity_state),
        }

        # -----------------------------
        # Tangent corridor detection
        # -----------------------------
        _pi = getattr(state, "phi_index", 0)
        phi_index = int(_pi() if callable(_pi) else _pi)

        _k = getattr(state, "kappa", 0.0)
        kappa = float(_k() if callable(_k) else _k)

        xy = self._torus_xy(phi_index=phi_index, kappa=kappa)

        uxy = np.asarray(project_to_uxy(state.Omega), dtype=float).reshape(-1)
        if uxy.size < 3:
            uxy = np.pad(uxy, (0, 3 - uxy.size))

        dot_align = 0.0
        valid_align = False
        in_corridor = False

        if self.mon.prev_xy is not None and self.mon.prev_uxy is not None:
            diff_xy = xy - self.mon.prev_xy
            n_xy = float(np.linalg.norm(diff_xy))
            if n_xy > 1e-12:
                tangent = diff_xy / n_xy

                jump = (uxy - self.mon.prev_uxy)[:2]
                n_jump = float(np.linalg.norm(jump))
                if n_jump > 1e-12:
                    jump_dir = jump / n_jump
                    dot_align = float(np.dot(jump_dir, tangent))
                    valid_align = True
                    in_corridor = (abs(dot_align) >= float(self.CORR_THR))

        # tearing proxy: EMA of misalignment
        if valid_align:
            tear_raw = 1.0 - abs(dot_align)
            self.mon.tear_score_ema = 0.95 * self.mon.tear_score_ema + 0.05 * tear_raw
            self.mon.align_ema = 0.95 * self.mon.align_ema + 0.05 * abs(dot_align)
        else:
            self.mon.tear_score_ema = 0.99 * self.mon.tear_score_ema
            self.mon.align_ema = 0.99 * self.mon.align_ema

        tearing_risk = float(np.clip(self.mon.tear_score_ema, 0.0, 1.0))

        # corridor proximity
        if valid_align:
            prox = (abs(dot_align) - float(self.CORR_THR)) / max(1e-6, (1.0 - float(self.CORR_THR)))
            prox = float(np.clip(prox, 0.0, 1.0))
        else:
            prox = 0.0

        self.mon.prox_ema = (1.0 - float(self.PROX_ALPHA)) * float(self.mon.prox_ema) + float(self.PROX_ALPHA) * prox

        # ✅ survival memory (decaying trace)
        self.mon.surv_ema *= float(self.SURV_DECAY)
        if in_corridor:
            self.mon.surv_ema += float(self.SURV_GAIN) * (1.0 + 0.25 * float(self.mon.prox_ema))
        self.mon.surv_ema = float(np.clip(self.mon.surv_ema, 0.0, 3.0))
        surv_soft = float(self.mon.surv_ema)

        # corridor nudges
        corr_bonus = 1.0 + 0.06 * np.tanh(1.25 * surv_soft) + 0.03 * float(self.mon.prox_ema)
        tear_pen = 1.0 - 0.06 * tearing_risk
        corr_mult = float(np.clip(corr_bonus * tear_pen, 0.90, 1.10))

        tri_mod["write_mult"] = float(np.clip(tri_mod["write_mult"] * corr_mult, 0.90, 1.10))
        tri_mod["proposal_mult"] = float(np.clip(tri_mod["proposal_mult"] * corr_mult, 0.90, 1.10))

        bp = float(tri_mod["bridge_p"])
        bp *= float(np.clip(1.0 + 0.25 * float(self.mon.prox_ema) - 0.20 * tearing_risk, 0.6, 1.4))
        tri_mod["bridge_p"] = float(np.clip(bp, 0.03, 0.20))

        # update prevs
        self.mon.prev_xy = xy
        self.mon.prev_uxy = uxy

        # telemetry for sim scripts
        tri_mod["in_corridor"] = 1.0 if in_corridor else 0.0
        tri_mod["survival_steps"] = float(self.mon.surv_ema)
        tri_mod["tearing_risk"] = float(tearing_risk)
        tri_mod["tangent_align"] = float(dot_align)
        tri_mod["align_ema"] = float(self.mon.align_ema)
        tri_mod["disp"] = float(disp)
        tri_mod["coh_phase"] = float(coh_phase)

        # seed motion (optional)
        z = float(getattr(state, "z", 0.0))
        speed = 0.05 + 0.25 * float(coh)
        sign_z = 1.0 if z >= 0 else -1.0
        theta = (cycle_stage % 6) * (np.pi / 3.0)
        tri_mod["seed_v0"] = [float(speed * np.cos(theta)), float(speed * np.sin(theta)), float(0.15 * sign_z * speed)]
        tri_mod["seed_pos0"] = [0.0, 0.0, 0.0]

        # -----------------------------
        # Signals out to fabric
        # -----------------------------
        write_intent = bool(summary.strip())

        mtype = "episode"
        links: List[str] = []

        strength = float(np.clip(0.40 + 0.60 * float(coh), 0.0, 1.0))
        confidence = float(np.clip(0.35 + 0.65 * float(coh), 0.0, 1.0))
        half_life = float(20.0 + 80.0 * float(coh))
        promotion_score = float(np.clip(0.50 + 0.50 * float(coh), 0.0, 1.0))
        stability_delta = float(0.0)

        signals = KernelSignals(
            write_intent=write_intent,
            memory_type=mtype,
            strength=strength,
            confidence=confidence,
            half_life=half_life,
            promotion_score=promotion_score,
            links=links,
            stability_delta=stability_delta,
        )

        # -----------------------------
        # Debug payload (keys used by sim scripts MUST be present)
        # -----------------------------
        z_val = float(getattr(state, "z", 0.0))

        debug: Dict[str, Any] = {
            "coherence": float(coh),
            "z": float(z_val),
            "phase_disp": float(disp),
            "coh_phase": float(coh_phase),
            "tri_mod": tri_mod,
            "summary": summary,
            "coh_raw": float(coh_raw),
            "cycle_stage": float(cycle_stage),
            "identity_state": float(identity_state),
            "id_label": id_label,
            "S_mag": float(S_mag),
            "phi_coll": float(Phi_coll),
        }

        return state, signals, debug