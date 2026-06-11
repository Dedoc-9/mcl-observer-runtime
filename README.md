# mcl-observer-runtime

A validation runtime for multi-representation state semantics — observer-relative structure diagnostics for simulations, procedural content,
and AI-agent trajectories.

**Author**: Daniel Dillberg · **License**: AGPL-3.0-or-later · **Contact**: bigdilly95@gmail.com

## What it does

This SDK compares *descriptions* of a system across multiple geometries
(encoders) and reports where those descriptions agree, disagree, and break
under perturbation. It is deterministic, hash-chained, and auditable.

This runtime is a disagreement compiler over multiple representations of the same system: a deterministic mechanism for detecting when several imperfect descriptions stop referring to the same underlying structure. 
It is not a clustering tool, truth detector, or safety layer — it issues consistency judgments over heterogeneous observation maps, certifying agreement and localizing divergence while asserting nothing about which view is correct. It becomes structurally indispensable, rather than merely useful, under two joint conditions: correctness is constituted by agreement among irreducible partial views, and no tractable equivalence oracle exists. Three system classes satisfy both — distributed systems, where no global state exists and convergence of replica views is the correctness criterion itself; multi-agent and LLM orchestration systems, where each agent is a distinct encoder of the world and the runtime distinguishes shared structure from merely shared language; and long-lived software systems, where it detects drift in meaningful geometry that tests cannot see. In all three, its economic force is the same: it replaces repeated full-context reconstruction and natural-language reconciliation with one compact structural object per view and one comparison operator between them — a minimal communication interface for systems in which no single representation is authoritative.

**The one rule** (enforced in code, not just documentation):

> All outputs are statements about agreement between observers —
> never about validity of the underlying state.

Every result carries `claim_class: "observer_agreement_only"`. No tool emits
accept/reject verdicts, blocks actions, or repairs state.

## The three tools

| Tool | Question it answers | Typical use |
|---|---|---|
| `detect_divergence(a, b)` | Do two snapshots/replicas disagree structurally? | lockstep desync monitoring, ensemble agreement |
| `triage_content(snapshot)` | What is the block structure and how stable is it? | offline procedural-content triage, novelty flagging |
| `analyze_trajectory(frames)` | Did structure drift across a sequence? | post-hoc AI/LLM agent session analysis |

## Quick start

```python
from mcl_sdk import detect_divergence, triage_content, analyze_trajectory

a = {"player": [0.1, 0.2, 1.0], "npc1": [0.5, 0.5, 0.8]}   # id -> feature vector
b = {"player": [0.1, 0.2, 1.0], "npc1": [0.9, 0.5, 0.8]}

r = detect_divergence(a, b)
print(r["diverged"], r["vi_per_geometry"], r["implicated"])
```

See `docs/USAGE.md` for the deep-dive guide and `examples/` for runnable demos.

## What it deliberately does not do

- **No legality enforcement.** A structural-equivalence check cannot decide
  whether a game state is legal; lossy quotients can collapse semantically
  different states into one block. Write explicit domain predicates for that.
- **No per-action AI gating.** The LLM adapter is an observer; it has no veto.
  Per-action validation belongs in O(1) engine predicates, not O(n²) geometry.
- **No state repair.** The quotient map is non-invertible; this SDK detects
  and localizes divergence, it cannot reconstruct the data needed to resync.
- **No quality judgments.** "Structural outlier" means novel under the declared
  geometry — not bad, broken, or unfun.
- **No encoder-independent truth.** Results are certified relative to declared
  geometries. Agreement within one encoder family is not invariance; the
  `validity_scope` block on every output says which case you are in.

## Determinism & provenance

Outputs embed kernel fingerprint, encoder source hashes, seeds, and a chain
hash. Set `SOURCE_DATE_EPOCH` to pin timestamps for byte-reproducible runs.

## License

AGPL-3.0-or-later. Modifications to the SDK (kernel, runtime, analyzers) must
remain open under the same license, including when served over a network.
Proprietary engines and models should integrate via the public API surface.
