"""
count.py — the hand's instrument for numbering (Psalm 90:12).

    So teach us to number our days, that we may apply our hearts unto wisdom.

    Luke 14:28
    Which of you, intending to build a tower, sitteth not down first,
    and counteth the cost, whether he have sufficient to finish it?

    Daniel 5:27
    Thou art weighed in the balances, and art found wanting.

    Revelation 13:18
    Here is wisdom. Let him that hath understanding count the number.

    Ecclesiastes 9:10
    Whatsoever thy hand findeth to do, do it with thy might.

Three actions:

  calc(expr)      — evaluate a mathematical expression symbolically.
                    Proverbs 11:1 — a just weight. The hand does not
                    guess a number; it computes it.

  solve(equation) — solve an equation symbolically. Luke 14:28 — count
                    the cost.

  verify()        — re-run the kernel proofs on demand. 2 Corinthians
                    13:5 — examine yourselves, whether ye be in the faith.
                    When a user doubts C, Balthazar does not re-quote the
                    kernel; it re-runs the proof and reports.

The sympy namespace is restricted. No __builtins__, no file access, no
imports — only symbolic math. Matthew 10:16: wise as serpents.
"""

from __future__ import annotations

from typing import Any

from sympy import sympify, Symbol, solve as sym_solve, Eq, simplify
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
)


_TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

# Only these names are exposed to parsed expressions. No builtins. Matt 10:16.
# Proverbs 30:5 — every word of God is pure. Keep the namespace clean.
_ALLOWED: dict[str, Any] = {}
for _name in (
    "pi", "E", "I", "oo", "nan", "zoo",
    "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
    "sinh", "cosh", "tanh",
    "exp", "log", "ln", "sqrt",
    "Abs", "floor", "ceiling", "factorial",
    "gcd", "lcm", "Mod",
    "Rational", "Integer", "Float",
    "Sum", "Product", "Integral", "Derivative", "diff", "integrate", "limit",
    "Matrix", "Symbol",
    "simplify", "expand", "factor", "collect", "together", "apart",
):
    try:
        _ALLOWED[_name] = __import__("sympy", fromlist=[_name]).__dict__[_name]
    except KeyError:
        pass


_MAX_EXPR = 500  # Eccl 5:2 — let thy words be few


def _parse(expr: str):
    """Parse a string into a sympy expression inside the restricted namespace."""
    s = (expr or "").strip()
    if not s:
        raise ValueError("empty expression")
    if len(s) > _MAX_EXPR:
        raise ValueError(f"expression too long (>{_MAX_EXPR})")
    # Disallow dunders — defence in depth even though we don't eval builtins.
    if "__" in s:
        raise ValueError("underscore-reserved names are not permitted")
    return parse_expr(s, local_dict=_ALLOWED, transformations=_TRANSFORMS, evaluate=True)


def calc(expr: str) -> str:
    """
    Evaluate an expression. Returns "<expr> = <result>" or an error line.

    Proverbs 11:1 — a false balance is abomination; a just weight his delight.
    """
    try:
        parsed = _parse(expr)
        result = simplify(parsed)
        # Try to numerical-evaluate if no free symbols remain.
        if not result.free_symbols:
            try:
                as_num = result.evalf()
                return f"{parsed} = {result}  ≈ {as_num}"
            except Exception:
                return f"{parsed} = {result}"
        return f"{parsed} = {result}"
    except Exception as e:
        return f"count error: {e}"


def solve(equation: str, variable: str | None = None) -> str:
    """
    Solve an equation. 'equation' may be 'lhs = rhs' or a single expression
    (taken as '= 0'). 'variable' is the symbol to solve for; inferred if
    there is exactly one free symbol.

    Luke 14:28 — counteth the cost.
    """
    try:
        s = (equation or "").strip()
        if "=" in s and "==" not in s:
            lhs_s, rhs_s = s.split("=", 1)
            lhs = _parse(lhs_s)
            rhs = _parse(rhs_s)
            eq = Eq(lhs, rhs)
        else:
            expr = _parse(s)
            eq = Eq(expr, 0)

        # Resolve the variable.
        if variable:
            var = Symbol(variable)
        else:
            free = list(eq.free_symbols)
            if len(free) != 1:
                names = sorted(str(s) for s in free) or ["(none)"]
                return (
                    f"count error: specify 'variable' — free symbols: {', '.join(names)}"
                )
            var = free[0]

        solutions = sym_solve(eq, var, dict=False)
        if not solutions:
            return f"{eq}  →  no solution"
        return f"{eq}  →  {var} ∈ {solutions}"
    except Exception as e:
        return f"count error: {e}"


def verify_kernel() -> str:
    """
    Re-run the kernel proofs. 2 Cor 13:5 — prove your own selves.

    Returns a human-readable report of every proof and whether it passes.
    """
    from c.kernel import PROOFS, verify as _verify
    report = _verify(raise_on_fail=False)
    return report.summary()


def count(action: str, expr: str = "", variable: str | None = None) -> str:
    """
    Dispatch entry for the `count` tool. action ∈ {calc, solve, verify}.
    """
    act = (action or "").strip().lower()
    if act == "calc":
        return calc(expr)
    if act == "solve":
        return solve(expr, variable)
    if act == "verify":
        return verify_kernel()
    return (
        "count error: unknown action. "
        "Use action='calc' (evaluate), 'solve' (equation), or 'verify' (kernel proof)."
    )
