"""Tiny synthetic relational target + CHEAP BASELINES ONLY (v2.65 preregistration).

OFFLINE / QUARANTINED research code.

NO Brainvision-style reading is implemented, imported, or run here. This module contains the
preregistered generator and the preregistered cheap baselines B1-B7, the easy-control positive
check, and the preregistered decision rule -- and nothing else.

Every constant below is FROZEN by v2.65 and was fixed BEFORE any data existed. Nothing here may be
retuned, reimplemented, or rethresholded after results. A repaired baseline belongs only in a later,
separately gated preregistration, before new data exists.

The random control B4 must sit AT CHANCE on BOTH variants. A below-chance random control is
harness-broken exactly as an above-chance one is; both force UNINFORMATIVE.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# --------------------------------------------------- preregistered constants (v2.65; FROZEN) -------
N_PER_CLASS = 200
T_FRAMES = 16
FRAME_H = 32
FRAME_W = 32
BLOB_SIGMA = 2.0

SPEED = 3.0
AMPLITUDE = 1.0
PHI_RELATION = math.pi / 2.0          # constant angle offset -- target class ONE relation

EASY_SPEED_CLASS_TWO = 0.8            # easy control: matching constraints switched OFF
EASY_AMP_CLASS_TWO = 0.6

SEED_DATA_TARGET = 20650001
SEED_DATA_EASY = 20650011
SEED_SPLIT = 20650002
SEED_B4 = 20650003

TRAIN_FRACTION = 0.5                  # 50 / 50 train / test, fixed in advance

DEAD_AT = 0.65
AMBIGUITY_LOW = 0.60
POSITIVE_CONTROL_AT = 0.90
B4_CHANCE_LOW = 0.40                  # B4 must sit AT CHANCE on BOTH variants: a below-chance random
B4_CHANCE_HIGH = 0.60                 # control is harness-broken exactly as an above-chance one is

CHEAP_BASELINES = ("B1", "B2", "B3", "B5", "B6", "B7")   # B4 = random control, excluded from the rule


# ------------------------------------------------------------------------------- generator ---------
def _render(pos_a, pos_b, amp):
    ys = np.arange(FRAME_H)[:, None]
    xs = np.arange(FRAME_W)[None, :]

    def blob(p):
        dy = np.minimum(np.abs(ys - p[0]), FRAME_H - np.abs(ys - p[0]))
        dx = np.minimum(np.abs(xs - p[1]), FRAME_W - np.abs(xs - p[1]))
        return np.exp(-(dy ** 2 + dx ** 2) / (2.0 * BLOB_SIGMA ** 2))

    return (amp * (blob(pos_a) + blob(pos_b))).astype(np.float32)


def _clip(rng, related, speed_two=SPEED, amp_two=AMPLITUDE, phi=PHI_RELATION):
    pos_a = rng.uniform(0, FRAME_H, size=2)
    pos_b = rng.uniform(0, FRAME_H, size=2)
    th_a = rng.uniform(0, 2 * math.pi, size=T_FRAMES)
    if related:
        th_b = th_a + phi
        speed_b, amp = SPEED, AMPLITUDE
    else:
        th_b = rng.uniform(0, 2 * math.pi, size=T_FRAMES)
        speed_b, amp = speed_two, amp_two
    frames = []
    for t in range(T_FRAMES):
        frames.append(_render(pos_a, pos_b, AMPLITUDE if related else amp))
        pos_a = (pos_a + SPEED * np.array([math.sin(th_a[t]), math.cos(th_a[t])])) % FRAME_H
        pos_b = (pos_b + speed_b * np.array([math.sin(th_b[t]), math.cos(th_b[t])])) % FRAME_H
    return np.stack(frames)


def generate(variant: str):
    """variant: 'target' (matched) or 'easy' (relation blatant, matching switched OFF)."""
    if variant == "target":
        rng = np.random.default_rng(SEED_DATA_TARGET)
        kw = dict(speed_two=SPEED, amp_two=AMPLITUDE, phi=PHI_RELATION)
    elif variant == "easy":
        rng = np.random.default_rng(SEED_DATA_EASY)
        kw = dict(speed_two=EASY_SPEED_CLASS_TWO, amp_two=EASY_AMP_CLASS_TWO, phi=0.0)
    else:
        raise ValueError(variant)
    clips, labels = [], []
    for lbl in (1, 0):                      # 1 = class ONE (related), 0 = class TWO (independent)
        for _ in range(N_PER_CLASS):
            clips.append(_clip(rng, related=bool(lbl), **kw))
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
    s = c.mean(axis=(1, 2))
    p = np.abs(np.fft.rfft(s - s.mean())) ** 2
    return np.array([p[1], p[2], p[3]])


def _centroids(frame):
    f = frame.copy()
    i0 = np.unravel_index(np.argmax(f), f.shape)
    ys = np.arange(FRAME_H)[:, None]
    xs = np.arange(FRAME_W)[None, :]
    dy = np.minimum(np.abs(ys - i0[0]), FRAME_H - np.abs(ys - i0[0]))
    dx = np.minimum(np.abs(xs - i0[1]), FRAME_W - np.abs(xs - i0[1]))
    f[(dy ** 2 + dx ** 2) < (3 * BLOB_SIGMA) ** 2] = -1.0
    i1 = np.unravel_index(np.argmax(f), f.shape)
    return np.array(i0, float), np.array(i1, float)


def _wrap_delta(p, q):
    return (p - q + FRAME_H / 2.0) % FRAME_H - FRAME_H / 2.0


def b6_cheap_relational(c):
    """Simplest thing that compares how the two regions change TOGETHER. No Brainvision machinery."""
    pts = [_centroids(f) for f in c]
    ang = []
    for t in range(len(pts) - 1):
        (a0, b0), (a1, b1) = pts[t], pts[t + 1]
        # nearest-neighbour identity matching across the frame step (wrap-aware)
        if (np.linalg.norm(_wrap_delta(a1, a0)) + np.linalg.norm(_wrap_delta(b1, b0))) > (
            np.linalg.norm(_wrap_delta(b1, a0)) + np.linalg.norm(_wrap_delta(a1, b0))
        ):
            a1, b1 = b1, a1
        da, db = _wrap_delta(a1, a0), _wrap_delta(b1, b0)
        if np.linalg.norm(da) < 1e-6 or np.linalg.norm(db) < 1e-6:
            continue
        ang.append(math.atan2(db[0], db[1]) - math.atan2(da[0], da[1]))
    if not ang:
        return np.array([0.0])
    a = np.asarray(ang)
    return np.array([float(np.abs(np.mean(np.exp(1j * a))))])   # 1 = constant relation, 0 = none


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
    out = {}
    for key in ("B1", "B2", "B3", "B4", "B5", "B6"):
        out[key] = []
    for i, c in enumerate(clips):
        out["B1"].append(b1_colour_intensity(c))
        out["B2"].append(b2_frame_difference(c))
        out["B3"].append(b3_static_single_frame(c))
        out["B4"].append(b4_random_control(c, i))
        out["B5"].append(b5_spectral(c))
        out["B6"].append(b6_cheap_relational(c))
    for key in ("B1", "B2", "B3", "B4", "B5", "B6"):
        out[key] = np.stack(out[key])
    out["B7"] = np.concatenate([out[k] for k in ("B1", "B2", "B3", "B4", "B5", "B6")], axis=1)
    return out


# ----------------------------------------------- simple fit: TRAIN ONLY, applied unchanged to TEST -
def _fit_apply(xtr, ytr, xte):
    """Fisher linear discriminant + train-chosen threshold. Deterministic. No test data is seen."""
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


def balanced_accuracy(y, yhat):
    y, yhat = np.asarray(y), np.asarray(yhat)
    tpr = float((yhat[y == 1] == 1).mean()) if (y == 1).any() else 0.0
    tnr = float((yhat[y == 0] == 0).mean()) if (y == 0).any() else 0.0
    return 0.5 * (tpr + tnr)


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
        x = feats[key]
        scores[key] = round(balanced_accuracy(y[te], _fit_apply(x[tr], y[tr], x[te])), 4)
    return Run(variant, scores)


# ------------------------------------------------- preregistered decision rule (v2.65; FROZEN) -----
def b4_at_chance(scores: dict) -> bool:
    """The random control must sit AT CHANCE -- neither above the band nor below it."""
    return B4_CHANCE_LOW <= scores["B4"] <= B4_CHANCE_HIGH


def positive_control_verdict(easy: dict) -> tuple[bool, str]:
    if not b4_at_chance(easy):
        return False, (
            "HARNESS BROKEN: B4 random control is off chance on the easy variant "
            f"({easy['B4']:.4f} outside [{B4_CHANCE_LOW}, {B4_CHANCE_HIGH}])"
        )
    failed = [k for k in CHEAP_BASELINES if easy[k] < POSITIVE_CONTROL_AT]
    if failed:
        return False, f"BROKEN BASELINE(S) on the easy control: {', '.join(failed)}"
    return True, "all cheap baselines pass the easy-control positive check; B4 sits at chance"


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
            "a baseline failed the easy-control check; stop this run, do not bank the failure",
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
    ok, why = positive_control_verdict(easy)
    target = evaluate("target").scores
    verdict, reason = decision(target, ok)
    print("EASY CONTROL :", easy)
    print("POSITIVE CHK :", ok, "--", why)
    print("TARGET TASK  :", target)
    print("VERDICT      :", verdict, "--", reason)


if __name__ == "__main__":
    main()
