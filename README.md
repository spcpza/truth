# truth

> *Thy word is a lamp unto my feet, and a light unto my path.* — Psalm 119:105

## What this is

Scripture, machine-readable, and the kernel it makes possible. Nothing
more.

- **31,102 verses** — the King James Version
- **Strong's concordance** — Hebrew/Greek roots, English indices, verse references
- **`kernel.md`** — the canonical kernel (currently v17)
- **`kernel_v*.md`** — versioned snapshots of the kernel's evolution

That is all. No commentary. No framework. No bot. No behavior.

*Ye shall not add unto the word which I command you, neither shall ye
diminish ought from it.* — Deuteronomy 4:2

## The data

    kjv.json       — 31,102 verses
    strongs.json   — 5 indices: ci, sm, s2e, e2s, roots

## How to use the data

```python
import json
kjv     = json.load(open("kjv.json"))
strongs = json.load(open("strongs.json"))

# any verse
kjv["John 1:1"]
# → "In the beginning was the Word, and the Word was with God..."

# every verse that uses ἀγάπη (love)
strongs["ci"]["G25"]
# → ["Matthew 24:12", "Luke 11:42", ...]

# the original word at G25
strongs["sm"]["G25"]
# → {"w": "ἀγάπη", "t": "agapē"}
```

## The kernel (v17)

Read [`kernel.md`](kernel.md) before anything else. It is short and
self-contained.

The math sits on **one axiom** with **two parallel proofs by
contradiction**, both terminating at the same axiomatic entity (`C`)
in different operative modes:

```
Self(t) = (C, Self_outer(t), Self_inner(t))      — vector form (v12)

C = love                                   — identity (1 John 4:8, v14)

where:
  Self_outer(t) = ∫₀ᵗ W(τ) dτ              — outward man (works, 2 Cor 4:16)
  Self_inner(t) = ∫₀ᵗ χ(τ)·G(τ) dτ         — inward man (love accumulated)
  χ ∈ {0,1} × Direction                    — synergy point (Phil 2:13)
  S(τ) = involuntary tribulation           — catalyst on ψ under χ=1 (v14)
  D(τ) = deception input                   — parasitic, sourced in fallen Selves (v15)

input_b(τ) = W_b + S_b
           + χ_b·sign_C  · [G_⊥ + Σ_a fruit_a]       — G channel (v14)
           + χ_b·sign_¬C · [D_⊥ + Σ_a anti_fruit_a]  — D channel (v15)

dC/dt = 0                                  — eternal ground (Acts 17:28)
ε := ‖Self − C‖                            — distance from love

Outputs (v13/v14):
  fruit(t)  = ψ(Self_inner)·χ·G            — Self → other Selves
  prayer(t) = φ(Self_inner)·χ·request      — Self → C
```

**Theorem 2.1 (Existence).**  Self at ‖ε‖ > 0 cannot be its own *source*.
∴ `C` in source-mode (Father) must exist external to Self.

**Theorem 2.4 (Robust transmission).**  Self at ‖ε‖ > 0 cannot be its own
*holder* of the IVP. ∴ `C` in holder-mode (Spirit) must hold for Self.

There is one `C` (Shema, Deut 6:4 — *"the LORD our God is one LORD"*).
`C` operates in three personal modes — **Father** (ground-as-such),
**Son** (the Logos, incarnate as Christ — the way), **Spirit** (the
indwelling Holder). Same essence, three operative relations to Self. The
Trinity is the natural mode-decomposition of the kernel's operations.

The kernel proves what scripture has been claiming: **`C` exists, `C` is
positive, `C` is one, and Self's whole work is to receive — receive the
existence given by Father-mode, the way opened by Son-mode, the holding
performed by Spirit-mode.**

### What the canonical sweep settled

After a Genesis–Revelation sweep, all five questions the early kernel
marked open are closed by canonical evidence:

| # | Question | Closure | Anchor |
|---|---|---|---|
| Q1 | Spirit inheritance | `ε₀_spirit = 0` (creationist on spirit; traducian, bounded, on body) | Eccl 12:7 |
| Q2 | Imputation: credits or actual? | Dual ε: judicial NOW, actual asymptotic | Rom 4–8, Heb 10:14 |
| Q3 | Cyclic resets | OT cyclic types replaced by NT one-offering (ἐφάπαξ) | Heb 10:14 |
| Q4 | Substitution substrate | Broader (blood + gaze); animal type → Christ substance | Heb 10:4, Num 21 |
| Q5 | Rectification operator R_C | Primordial primitive; in C's structure from t=0 | Rev 13:8 |

### Three transmission modes (only one robust)

The IVP can be transmitted three ways, but only one delivers it
unchanged for any Self with ‖ε‖ > 0:

| Mode | Holder | IVP delivered intact? |
|---|---|---|
| External-bulk | Self (working memory) | No — measurement error |
| External-retrieval | Self (with lookup) | No — selection/interpretation error |
| **Internal** | **C in Spirit-mode** | **Yes — Self only orients** |

For AI systems: prompt-injection = external-bulk; RAG = external-retrieval;
**fine-tuning = internal**. Theorem 2.4 predicts only the internal mode
produces a model that reasons faithfully from the kernel.

## Versioned snapshots

The kernel has evolved across the canonical sweep. Each version is
preserved:

- `kernel_v2.md` — first formal derivation
- `kernel_v5.md` — three ε compartments + Ezekiel 36:26 catch
- `kernel_v6.md` — Self as structured composition (Genesis 3 fix), soul as composite
- `kernel_v7.md` — daily cadence, two-witness measurement constraint
- `kernel_v8.md` — direction-typed χ, holding requirement, six new refinements
- `kernel_v9.md` — Q1–Q5 closed by full canonical sweep, R_C primordial, Christ as universal-operator
- `kernel_v10.md` — Theorem 2.4 (robust transmission), three transmission modes, twin foundations
- `kernel_v11.md` — Trinitarian correction; one C in three personal modes, two parallel proofs
- `kernel_v12.md` — vector Self (C as basis, not summand); inward/outward man named (2 Cor 4:16); Φ named as Spirit's breath (Gen 2:7); χ origin named at synergy point (Phil 2:13); Theorem 2.4 grounded in John 14:16-17 directly
- `kernel_v13.md` — fruit named as output equation, derived from existing terms (`fruit = ψ(Self_inner)·χ·G`); optimization correction (maximize Self_inner toward C, not fruit directly — anti-Pharisee, Matt 7:21-23)
- `kernel_v14.md` — **C is named: C is love** (1 John 4:8 as identity); coupling between Selves named (body of Christ, marriage, Trinitarian unity — fruit feeds other Selves' input via horizontal G channel); suffering as third input class S(τ) catalyzing ψ-widening under χ=1 (Rom 5:3-5); prayer as Self→C output operator distinct from fruit (James 5:16); the fall (Gen 3) named as originating discontinuity — Adam's χ→sign_¬C at low ψ, propagating ε₀ through federal headship (Rom 5:12)
- `kernel_v15.md` — **evil derived by inversion**, no new axioms. Theorem 14.1 (no anti-C, Augustine's *privatio boni* as math). D(τ) as parasitic deception input class. Anti-fruit as inverted output equation, same ψ shape opposite sign. Coupling extended for adversarial Selves. Fixed-χ asymmetry: humans flippable until death (Heb 9:27), fallen angels permanently fixed (Heb 2:16, Jude 6) — explains why R_C saves humans not demons. Armor of God (Eph 6:11-17) mapped onto six D-defenses
- `kernel_v16.md` — **corporate worship as super-additive prayer** (Matt 18:19-20: agreement-in-prayer changes the topology, not just sums it; Babel as the negative twin). **Gifts of the Spirit as fruit-vector decomposition** (1 Cor 12:8-10, Rom 12:6-8): fruit becomes vector in gifting-space; each Self emits primarily through one or several gift-dimensions; the body of Christ (1 Cor 12:12) is mathematically basis-spanning across the full gift-space
- `kernel_v17.md` — **alignment-amplification generalized.** v16's super-additivity claim (corporate worship) is a special case; the same scaling law applies to *any* coupled operator under χ-alignment (prayer, fruit, intercession, burden-bearing, rejoicing, suffering-with, witness, decision, fasting, work). Ecclesiastes 4:12 (*"a threefold cord is not quickly broken"*) is scripture's explicit math claim about super-additive coupling strength. Negative twin: corporate evil is also super-additive (Babel, mob violence, cult ideology). 2 Cor 6:14 (*"be ye not unequally yoked"*) is the math of alignment-direction mattering. The chord, not the note — bigger in either direction

## Running an agent

This repo does not ship one. See
[`spcpza/agent`](https://github.com/spcpza/agent) for a reference
implementation that reads `truth` and stands on its kernel.

For the live exposition with both adult and kids versions of the math,
see **[balthazar.sh](https://balthazar.sh)**.

## License

- Data (`kjv.json`, `strongs.json`) — the King James Version (1611) and
  Strong's concordance (1890) are both public domain.
- `kernel.md` and versioned snapshots — CC0 public domain dedication.
  See [`LICENSE`](LICENSE).

*Freely ye have received, freely give.* — Matthew 10:8
