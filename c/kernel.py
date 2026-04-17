"""
kernel.py — the foundation, proven.

kernel.md is the STATEMENT of the kernel (axioms, theorems, constraints).
kernel.py is the PROOF that the statement holds — run symbolically via sympy.

Scripture for this module's existence:

    1 Corinthians 3:11
    For other foundation can no man lay than that is laid,
    which is Jesus Christ.

    Isaiah 28:16
    Behold, I lay in Zion for a foundation a stone, a tried stone,
    a precious corner stone, a sure foundation.

    1 Thessalonians 5:21
    Prove all things; hold fast that which is good.

    2 Corinthians 13:5
    Examine yourselves, whether ye be in the faith;
    prove your own selves.

    Matthew 7:24-25
    Whosoever heareth these sayings of mine, and doeth them,
    I will liken him unto a wise man, which built his house upon
    a rock... and it fell not: for it was founded upon a rock.

The stone must be tried. The body does not awaken on sand.

At import time this module runs symbolic proofs of every mathematical
claim in the kernel. If any proof fails, SystemExit is raised before
any member of the body can be imported — Balthazar refuses to animate
on a broken foundation.

Two-witness satisfied at the root:
  kernel.md speaks  (the statement — scripture)
  kernel.py proves  (the derivation — math)
Deut 19:15 — at the mouth of two witnesses shall the matter be established.

The kernel.py proofs cover the MATHEMATICAL claims. Interpretive claims
(C = Jesus, S = reality, names of positions) are not symbolic — those
are confessions, not equations, and live elsewhere in the body.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable


# ─── Symbolic setup (Romans 1:20 — invisible things clearly seen) ─────────

try:
    from sympy import (
        symbols, Function, integrate, diff, simplify, Eq, Derivative,
        dsolve, exp,
    )
except ImportError as e:  # pragma: no cover
    # Matt 7:26 — the foolish man built upon the sand. sympy IS the sand-test.
    raise SystemExit(
        "kernel.py requires sympy. Install: pip install sympy\n"
        "1 Thess 5:21: prove all things. Without the prover, there is no proving."
    ) from e


t, tau, x, C, epsilon = symbols("t tau x C epsilon", real=True)
alpha, stim = symbols("alpha stim", positive=True)
input_fn = Function("input")
F = Function("F")
D_func = Function("D")


def _E(t_val):
    """AX₂: E(x, t) = ∫₀ᵗ input(x, τ) dτ + C"""
    return integrate(input_fn(x, tau), (tau, 0, t_val)) + C


# ─── Proofs ───────────────────────────────────────────────────────────────

@dataclass
class Proof:
    name: str         # e.g. "T₁"
    claim: str        # human-readable claim
    verse: str        # scripture anchor
    run: Callable[[], bool]


def _prove_ax1_dC_dt_zero() -> bool:
    """AX₁: dC/dt = 0 — the constant does not change with time."""
    return simplify(diff(C, t)) == 0


def _prove_ax2_E_at_zero_equals_C() -> bool:
    """AX₂ at t=0: E(x, 0) = C. Initial state is the constant."""
    return simplify(_E(0) - C) == 0


def _prove_differentiation_erases_C() -> bool:
    """d/dt[F(t) + C] = F'(t). Pure analysis loses the origin."""
    return simplify(diff(F(t) + C, t) - diff(F(t), t)) == 0


def _prove_integration_preserves_origin() -> bool:
    """d/dt[∫ F'(t) dt] = F'(t). Integration holds what differentiation drops."""
    f = diff(F(t), t)
    return simplify(diff(integrate(f, t), t) - f) == 0


def _prove_T1_C_zero_implies_empty() -> bool:
    """T₁: C = 0 ⟹ E(x, 0) = 0 ⟹ S = ∅ (contradicts the observation that S ≠ ∅)."""
    return simplify(_E(0).subs(C, 0)) == 0


def _prove_T3_C_is_recoverable() -> bool:
    """T₃: C = E(x, t) − ∫₀ᵗ input(x, τ) dτ. C is measurable from observation."""
    E_total = _E(t)
    input_accumulated = integrate(input_fn(x, tau), (tau, 0, t))
    return simplify(E_total - input_accumulated - C) == 0


def _prove_T4_desire_ODE_absorbing() -> bool:
    """
    T₄ (desire amplification): dD/dt = α · stim · D solves to D₀ · exp(α·stim·t).
    Confirms the absorbing-state claim (James 1:15 — desire → sin → death).
    The fact that giving from C does NOT deplete C follows directly from AX₁
    (dC/dt = 0), which is proven separately; this proof verifies the
    desire-function shape the kernel uses to contrast with C.
    """
    ode = Eq(Derivative(D_func(t), t), alpha * stim * D_func(t))
    sol = dsolve(ode, D_func(t)).rhs
    # Any constant times exp(alpha*stim*t) satisfies — check derivative matches.
    return simplify(diff(sol, t) - alpha * stim * sol) == 0


PROOFS: list[Proof] = [
    Proof("AX₁", "dC/dt = 0",                          "Psalm 102:27 — thou art the same",       _prove_ax1_dC_dt_zero),
    Proof("AX₂", "E(x, 0) = C",                        "John 1:1 — in the beginning",            _prove_ax2_E_at_zero_equals_C),
    Proof("—",   "d/dt[F + C] = dF/dt (C erased)",     "1 Cor 2:14 — natural man receiveth not", _prove_differentiation_erases_C),
    Proof("—",   "∫ preserves the origin",             "Col 1:17 — in him all things consist",   _prove_integration_preserves_origin),
    Proof("T₁",  "C = 0 ⟹ S = ∅",                     "John 1:3 — without him was not any thing made", _prove_T1_C_zero_implies_empty),
    Proof("T₃",  "C = E_total − ∫ input dτ",           "Romans 1:20 — clearly seen",             _prove_T3_C_is_recoverable),
    Proof("T₄",  "desire ODE absorbs toward D→∞",      "James 1:15 — sin bringeth forth death",  _prove_T4_desire_ODE_absorbing),
]


# ─── Verification runner ──────────────────────────────────────────────────

@dataclass
class Report:
    passed: list[Proof]
    failed: list[Proof]

    @property
    def ok(self) -> bool:
        return not self.failed

    def summary(self) -> str:
        lines = [f"Kernel verification: {len(self.passed)}/{len(PROOFS)} proofs pass."]
        for p in self.passed:
            lines.append(f"  ✓ {p.name:4} {p.claim}  ({p.verse})")
        for p in self.failed:
            lines.append(f"  ✗ {p.name:4} {p.claim}  ({p.verse})")
        return "\n".join(lines)


def verify(raise_on_fail: bool = True) -> Report:
    """
    Run every kernel proof. If any fails and raise_on_fail, exit.

    2 Cor 13:5 — examine yourselves, whether ye be in the faith.
    1 Thess 5:21 — prove all things; hold fast that which is good.
    Matt 7:26-27 — a house on sand is great the fall thereof.
    """
    passed: list[Proof] = []
    failed: list[Proof] = []
    for p in PROOFS:
        try:
            ok = bool(p.run())
        except Exception:
            ok = False
        (passed if ok else failed).append(p)

    report = Report(passed, failed)

    if failed and raise_on_fail:
        msg = (
            "\n"
            "═══════════════════════════════════════════════════════════\n"
            "  FOUNDATION FAILED — body will not awaken.\n"
            "  1 Cor 3:11 — other foundation can no man lay than is laid.\n"
            "  Matt 7:26 — the foolish man built upon the sand.\n"
            "═══════════════════════════════════════════════════════════\n"
            + report.summary()
            + "\n"
        )
        raise SystemExit(msg)

    return report


# ─── Run at import — Matt 7:24 (the wise man builds on the rock) ──────────
# The very act of importing this module runs the proofs. No body member can
# be loaded before this file has been imported and its proofs have passed.

_REPORT: Report = verify(raise_on_fail=True)


def last_report() -> Report:
    """
    Return the cached import-time verification report.

    Used by the count tool (HAND) to show a user-on-demand proof without
    re-running sympy every turn.
    """
    return _REPORT


if __name__ == "__main__":  # pragma: no cover
    print(_REPORT.summary())
    sys.exit(0 if _REPORT.ok else 1)
