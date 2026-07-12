"""v2.66 repaired-control tiny synthetic target + CHEAP BASELINES ONLY.

OFFLINE / QUARANTINED research code.

NO Brainvision-style reading is implemented, imported, or run here. Generator, repaired positive
control, cheap baselines B1-B7, and the preregistered decision rule -- and nothing else.

All constants are FROZEN by v2.66 and were fixed BEFORE any new data existed. FRESH SEEDS are used:
the v2.65 target-task scores were seen, so that data may not be reused as if unseen.

Declared modifications (v2.66 s4), both in the CONSERVATIVE direction -- they only make cheap
baselines STRONGER, which makes the task HARDER to reach eligibility:
  M1 -- B6 (cheap relational): repaired element identity handling. Chained assignment across the
        clip, wrap-aware centre-of-mass refinement, and merged frames dropped. The v2.65
        implementation could not tell a relation from its swapped counterpart when the two blobs
        overlapped, which is a CAPABILITY DEFECT, not a tuning choice.
  M2 -- B5 (simple spectral): repaired capability -- fuller temporal spectra (mean-intensity and
        frame-difference-energy bands). THE 0.90 BAR IS NOT LOWERED; the baseline is raised to it.

Repaired positive control (v2.66 s3): the relation is NOT lockstep and does NOT survive swapping the
two elements (phi = pi/2, which is neither 0 nor pi); the two elements are kept DISTINCT throughout by
rejection sampling on minimum separation (R1); and matching is switched off ONLY on axes irrelevant to
the certified capability (class TWO brightness and speed), never on the relational geometry and never
on element distinctness.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# --------------------------------------------------- preregistered constants (v2.66; FROZEN) -------
N_PER_CLASS = 200
T_FRAMES = 16
FRAME_H = 32
FRAME_W = 32
BLOB_SIGMA = 2.0

SPEED = 3.0
AMPLITUDE = 1.0
PHI_RELATION = math.pi / 2.0          # neither 0 nor pi: not lockstep, not swap-invariant

EASY_SPEED_CLASS_TWO = 0.8            # matching switched off on IRRELEVANT axes only
EASY_AMP_CLASS_TWO = 0.6
EASY_MIN_SEPARATION = 4.0 * BLOB_SIGMA    # v2.66 R1: elements remain DISTINCT in the control
EASY_MAX_TRIES = 200

SEED_DATA_TARGET = 20660001           # FRESH seeds -- v2.65 target scores were seen
SEED_DATA_EASY = 20660011
SEED_SPLIT = 20660002
SEED_B4 = 20660003

TRAIN_FRACTION = 0.5
DEAD_AT = 0.65
AMBIGUITY_LOW = 0.60
POSITIVE_CONTROL_AT = 0.90
B4_CHANCE_LOW = 0.40
B4_CHANCE_HIGH = 0.60

CHEAP_BASELINES = ("B1", "B2", "B3", "B5", "B6", "B7")   # B4 = random control, excluded from the rule


# ------------------------------------------------------------------------------- generator ---------
def _wrap_delta(p, q):
    return (p - q + FRAME_H / 2.0) % FRAME_H - FRAME_H / 2.0


def _render(pa, pb, amp):
    ys = np.arange(FRAME_H)[:, None]
    xs = np.arange(FRAME_W)[None, :]

    def blob(p):
        dy = np.minimum(np.abs(ys - p[0]), FRAME_H - np.abs(ys - p[0]))
        dx = np.minimum(np.abs(xs - p[1]), FRAME_W - np.abs(xs - p[1]))
        return np.exp(-(dy ** 2 + dx ** 2) / (2.0 * BLOB_SIGMA ** 2))

    return (amp * (blob(pa) + blob(pb))).astype(np.float32)


def _tracks(rng, related, speed_two, phi):
    pa = rng.uniform(0, FRAME_H, size=2)
    pb = rng.uniform(0, FRAME_H, size=2)
    tha = rng.uniform(0, 2 * math.pi, size=T_FRAMES)
    thb = tha + phi if related else rng.uniform(0, 2 * math.pi, size=T_FRAMES)
    sb = SPEED if related else speed_two
    A, B = [], []
    for t in range(T_FRAMES):
        A.append(pa.copy())
        B.append(pb.copy())
        pa = (pa + SPEED * np.array([math.sin(tha[t]), math.cos(tha[t])])) % FRAME_H
        pb = (pb + sb * np.array([math.sin(thb[t]), math.cos(thb[t])])) % FRAME_H
    return np.array(A), np.array(B)


def _min_sep(A, B):
    return float(min(np.linalg.norm(_wrap_delta(a, b)) for a, b in zip(A, B)))


def _clip(rng, related, variant):
    if variant == "easy":
        for _ in range(EASY_MAX_TRIES):                       # R1: keep the two elements DISTINCT
            A, B = _tracks(rng, related, EASY_SPEED_CLASS_TWO, PHI_RELATION)
            if _min_sep(A, B) >= EASY_MIN_SEPARATION:
                break
        amp = AMPLITUDE if related else EASY_AMP_CLASS_TWO
    else:
        A, B = _tracks(rng, related, SPEED, PHI_RELATION)
        amp = AMPLITUDE
    return np.stack([_render(A[t], B[t], amp) for t in range(T_FRAMES)])


def generate(variant: str):
    """variant: 'target' (matched) or 'easy' (repaired positive control)."""
    if variant == "target":
        rng = np.random.default_rng(SEED_DATA_TARGET)
    elif variant == "easy":
        rng = np.random.default_rng(SEED_DATA_EASY)
    else:
        raise ValueError(variant)
    clips, labels = [], []
    for lbl in (1, 0):                      # 1 = class ONE (related), 0 = class TWO (independent)
        for _ in range(N_PER_CLASS):
            clips.append(_clip(rng, bool(lbl), variant))
            labels.append(lbl)
    return np.stack(clips), np.asarray(labels)


# ------------------------------------------------------ cheap baselines B1-B7 (preregistered) ------
def b1_colour_intensity(c):
    return np.array([c.mean(), c.std()])


def b2_frame_difference(c):
    d = np.abs(np.diff(c, axis=0)).mean(axis=(1, 2))
    return np.array([d.mean(), d.std()])


def b3_static_single_frame(c):
    f = c[0]
    return np.array([f.mean(), f.std(), f.max()])


def b4_random_control(_c, idx):
    return np.array([np.random.default_rng(SEED_B4 + idx).normal()])


def b5_spectral(c):
    """M2: strengthened -- fuller temporal spectra of mean intensity and frame-difference energy."""
    s = c.mean(axis=(1, 2))
    d = np.abs(np.diff(c, axis=0)).mean(axis=(1, 2))
    ps = np.abs(np.fft.rfft(s - s.mean())) ** 2
    pd = np.abs(np.fft.rfft(d - d.mean())) ** 2
    return np.concatenate([ps[1:8], pd[1:7]])


def _two_centroids(frame):
    """M1: two blob centroids with wrap-aware centre-of-mass refinement, plus a merged flag."""
    f = frame.copy()
    i0 = np.unravel_index(np.argmax(f), f.shape)
    v0 = f[i0]
    ys = np.arange(FRAME_H)[:, None]
    xs = np.arange(FRAME_W)[None, :]

    def com(idx):
        dy = _wrap_delta(ys.astype(float), float(idx[0]))
        dx = _wrap_delta(xs.astype(float), float(idx[1]))
        mask = (dy ** 2 + dx ** 2) <= (2.0 * BLOB_SIGMA) ** 2
        w = np.clip(frame, 0, None) * mask
        tot = w.sum()
        if tot <= 0:
            return np.array(idx, float)
        return np.array([(idx[0] + (w * dy).sum() / tot) % FRAME_H,
                         (idx[1] + (w * dx).sum() / tot) % FRAME_W])

    dy = np.minimum(np.abs(ys - i0[0]), FRAME_H - np.abs(ys - i0[0]))
    dx = np.minimum(np.abs(xs - i0[1]), FRAME_W - np.abs(xs - i0[1]))
    f[(dy ** 2 + dx ** 2) < (3 * BLOB_SIGMA) ** 2] = -1.0
    i1 = np.unravel_index(np.argmax(f), f.shape)
    v1 = f[i1]
    merged = bool(v1 < 0.3 * v0)
    return com(i0), com(i1), merged


def b6_cheap_relational(c):
    """M1: chained identity across the clip; merged frames dropped. No Brainvision machinery."""
    pts = [_two_centroids(fr) for fr in c]
    prev = None
    ang = []
    for t in range(len(pts) - 1):
        a0, b0, m0 = pts[t]
        a1, b1, m1 = pts[t + 1]
        if m0 or m1:
            prev = None
            continue
        if prev is not None:
            if (np.linalg.norm(_wrap_delta(a0, prev[0])) + np.linalg.norm(_wrap_delta(b0, prev[1]))) > (
                np.linalg.norm(_wrap_delta(b0, prev[0])) + np.linalg.norm(_wrap_delta(a0, prev[1]))
            ):
                a0, b0 = b0, a0
        if (np.linalg.norm(_wrap_delta(a1, a0)) + np.linalg.norm(_wrap_delta(b1, b0))) > (
            np.linalg.norm(_wrap_delta(b1, a0)) + np.linalg.norm(_wrap_delta(a1, b0))
        ):
            a1, b1 = b1, a1
        da, db = _wrap_delta(a1, a0), _wrap_delta(b1, b0)
        prev = (a1, b1)
        if np.linalg.norm(da) < 1e-6 or np.linalg.norm(db) < 1e-6:
            continue
        ang.append(math.atan2(db[0], db[1]) - math.atan2(da[0], da[1]))
    if not ang:
        return np.array([0.0, 0.0])
    a = np.asarray(ang)
    return np.array([float(np.abs(np.mean(np.exp(1j * a)))), len(a) / float(T_FRAMES - 1)])


BASELINES = {
    "B1": "colour / intensity",
    "B2": "frame-difference",
    "B3": "static single-frame descriptor",
    "B4": "random / control",
    "B5": "simple spectral (FFT)",
    "B6": "cheap relational",
    "B7": "combined cheap baseline",
}


def features(clips):
    out = {k: [] for k in ("B1", "B2", "B3", "B4", "B5", "B6")}
    for i, c in enumerate(clips):
        out["B1"].append(b1_colour_intensity(c))
        out["B2"].append(b2_frame_difference(c))
        out["B3"].append(b3_static_single_frame(c))
        out["B4"].append(b4_random_control(c, i))
        out["B5"].append(b5_spectral(c))
        out["B6"].append(b6_cheap_relational(c))
    for key in list(out):
        out[key] = np.stack(out[key])
    out["B7"] = np.concatenate([out[k] for k in ("B1", "B2", "B3", "B4", "B5", "B6")], axis=1)
    return out


# ----------------------------------------------- simple fit: TRAIN ONLY, applied unchanged to TEST -
def balanced_accuracy(y, yhat):
    y, yhat = np.asarray(y), np.asarray(yhat)
    tpr = float((yhat[y == 1] == 1).mean()) if (y == 1).any() else 0.0
    tnr = float((yhat[y == 0] == 0).mean()) if (y == 0).any() else 0.0
    return 0.5 * (tpr + tnr)


def _fit_apply(xtr, ytr, xte):
    xtr = np.atleast_2d(xtr).astype(float)
    xte = np.atleast_2d(xte).astype(float)
    mu, sd = xtr.mean(0), xtr.std(0)
    sd[sd < 1e-12] = 1.0
    ztr, zte = (xtr - mu) / sd, (xte - mu) / sd
    m1, m0 = ztr[ytr == 1].mean(0), ztr[ytr == 0].mean(0)
    cov = np.atleast_2d(np.cov(ztr.T, bias=True)) + 1e-3 * np.eye(ztr.shape[1])
    w = np.linalg.solve(cov, (m1 - m0))
    ptr, pte = ztr @ w, zte @ w
    cands = np.unique(ptr)
    grid = (cands[:-1] + cands[1:]) / 2.0 if len(cands) > 1 else cands
    thr, best = float(grid[0]), -1.0
    for c in grid:
        acc = balanced_accuracy(ytr, (ptr > c).astype(int))
        if acc > best:
            best, thr = acc, float(c)
    return (pte > thr).astype(int)


def split_indices(n):
    idx = np.random.default_rng(SEED_SPLIT).permutation(n)
    k = int(round(TRAIN_FRACTION * n))
    return idx[:k], idx[k:]


@dataclass
class Run:
    variant: str
    scores: dict


def evaluate(variant: str) -> Run:
    clips, y = generate(variant)
    feats = features(clips)
    tr, te = split_indices(len(y))
    scores = {}
    for key in ("B1", "B2", "B3", "B4", "B5", "B6", "B7"):
        scores[key] = round(balanced_accuracy(y[te], _fit_apply(feats[key][tr], y[tr], feats[key][te])), 4)
    return Run(variant, scores)


# ------------------------------------------------- preregistered decision rule (v2.66; FROZEN) -----
def b4_at_chance(scores: dict) -> bool:
    return B4_CHANCE_LOW <= scores["B4"] <= B4_CHANCE_HIGH


def positive_control_verdict(easy: dict) -> tuple[bool, str]:
    if not b4_at_chance(easy):
        return False, (
            "HARNESS BROKEN: B4 random control is off chance on the repaired control "
            f"({easy['B4']:.4f} outside [{B4_CHANCE_LOW}, {B4_CHANCE_HIGH}])"
        )
    failed = [k for k in CHEAP_BASELINES if easy[k] < POSITIVE_CONTROL_AT]
    if failed:
        return False, f"BROKEN BASELINE(S) on the repaired positive control: {', '.join(failed)}"
    return True, "all cheap baselines pass the repaired positive control; B4 sits at chance"


def decision(target: dict, control_ok: bool) -> tuple[str, str]:
    if not b4_at_chance(target):
        return (
            "UNINFORMATIVE",
            "HARNESS BROKEN: B4 random control is off chance on the target task "
            f"({target['B4']:.4f} outside [{B4_CHANCE_LOW}, {B4_CHANCE_HIGH}]); stop this run",
        )
    if not control_ok:
        return (
            "UNINFORMATIVE",
            "the repaired positive control failed; stop this run, do not bank the failure",
        )
    best_k = max(CHEAP_BASELINES, key=lambda k: target[k])
    best = target[best_k]
    if best >= DEAD_AT:
        return "DEAD", f"{best_k} reached {best:.4f} >= {DEAD_AT}: solved by a cheap baseline"
    if best >= AMBIGUITY_LOW:
        return "NO CONCLUSION", f"best cheap baseline {best_k} = {best:.4f} lies in the ambiguity band"
    return "ELIGIBLE", f"all cheap baselines < {AMBIGUITY_LOW} (best {best_k} = {best:.4f})"


def main() -> None:
    easy = evaluate("easy").scores
    control_ok, why = positive_control_verdict(easy)
    target = evaluate("target").scores
    verdict, reason = decision(target, control_ok)
    print("REPAIRED CONTROL :", easy)
    print("POSITIVE CHECK   :", control_ok, "--", why)
    print("TARGET TASK      :", target)
    print("VERDICT          :", verdict, "--", reason)


if __name__ == "__main__":
    main()
