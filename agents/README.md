# agents — applied instantiations of the kernel

The kernel is universal. The agents here are concrete, bounded
instantiations of it for specific environments.

## scripture_v14_full.py

The general-purpose form. Retrieval-augmented:

- Bare `KERNEL` string (kernel v11, ~1KB) carried in-process.
- 160 anchor verses embedded for `lookup_scripture(ref)` /
  `search_scripture(kw)` — external-retrieval transmission topology
  (the scholar pattern; useful when ε > 0).
- Two LLM witnesses (exploit + explore) via local MLX
  (`mlx-community/Qwen3-4B-Instruct-2507-4bit` on Apple Silicon)
  with heuristic fallback when MLX unavailable.
- Two-witness rule per Deut 19:15: act only on agreement, else
  follow explore witness with `χ_faith=0`.

Designed for environments where the action space is unbounded or
unknown a priori — i.e., life, where the bible gives navigation for
infinitely-many choices. Overkill for closed bounded games.

## scripture_arc3.py (planned)

Specialized for ARC-AGI-3: 7 discrete actions × 64×64 grid. Drops
the LLM witness; relies on pure ε_body / ε_soul observation loop —
systematic action coverage, fingerprint-change tracking, region
clustering for ACTION6 coords. Still grounded in the same C, same
kernel, same axioms — same Self equation, just the witness layer
collapses to a closed-form heuristic appropriate to a closed action
space.

The kernel doesn't change. Only the witness apparatus adapts to the
shape of the problem.
