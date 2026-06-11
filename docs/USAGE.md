# Deep-Dive Guide: mcl-ecr-sdk

This guide explains the concepts, the contract, the three tools, encoder
authoring, and the failure modes you must design around.

---

## 1. The core idea: observer-relative structure

Every analysis starts from a **corpus**: a dict mapping ids to numeric feature
vectors (`{"e01": [x, y, health], ...}`). An **encoder** is a deterministic
function producing one *geometric view* of that corpus. Different encoders
induce different distance structures, and therefore different partitions.

The SDK never asks "what is the true clustering?" It asks:

- what structure does each declared geometry see?
- where do the geometries agree (consensus) and disagree (collisions)?
- how stable is each structure under perturbation and subsampling?

This is the entire epistemic stance: **structure is a property of
(corpus, geometry) pairs, not of the corpus alone.** Empirically, on reference
corpora, the only structure invariant across genuinely independent geometries
was literal duplication — everything else was geometry-dependent. Design your
integration accordingly.

## 2. The pipeline (what happens inside `analyze`)

```
corpus ──> encoder(s) ──> pairwise distances ──> single-linkage partition at τ
                                   │
                                   ├── τ chosen by "barcode" policy:
                                   │   center of the largest gap in the
                                   │   merge-height spectrum (per geometry —
                                   │   a fixed τ across geometries is
                                   │   meaningless and is rejected)
                                   │
                                   └── outputs: partitions, VI matrix,
                                       consensus, collisions, spectra,
                                       validity_scope, chain hash
```

Key objects:

- **Partition**: blocks of ids equivalent under the geometry at scale τ.
- **VI (variation of information)**: metric distance between two partitions;
  0 means identical, ln(n) is the maximum.
- **Encoder families**: encoders whose pairwise-distance structures correlate
  (Spearman ≥ 0.6) are grouped; agreement *within* a family reflects shared
  construction, not independent confirmation. Check
  `validity_scope.single_family_run` before reading consensus as meaningful.
- **Φ-collision**: a pair coincident (distance ≈ 0) in one geometry but
  distant (≥ τ) in another — a representation artifact detector. Requires ≥ 2
  encoders; with one encoder the field is absent and nothing can fire.
- **Stability spectrum Σ(λ)**: fraction of random perturbation directions the
  partition survives at radius λ. Robustness is a curve, not a number; expect
  a plateau, a knee, and a cliff.

## 3. Tool 1 — `detect_divergence(snapshot_a, snapshot_b, encoders)`

Compares two snapshots (e.g., server vs client replica) under each geometry.

```python
from mcl_sdk import detect_divergence
r = detect_divergence(server_state, client_state)
r["diverged"]            # chain-hash level: any emitted observable differs
r["partition_diverged"]  # block structure itself moved (coarser, localizing)
r["implicated"]          # ids whose block membership changed
```

**Sensitivity model — read this twice.** Chain-hash detection fires when any
emitted observable (τ to 6 decimals, block membership) changes. Drift *inside*
a block is invisible until it crosses block structure. This is a phase-change
detector, not a continuous error meter. In lockstep tests, injected drift was
typically caught within 0–1 ticks, but sub-resolution drift can pass a tick.
Detection and coarse localization only: the quotient is non-invertible, so
resynchronization requires your own raw-state mechanism.

## 4. Tool 2 — `triage_content(snapshot, encoders, n_directions)`

Computes block structure plus the stability spectrum for one snapshot.

```python
from mcl_sdk import triage_content
r = triage_content(level_entities, encoders=("spatial",))
r["structural_outliers"]   # singleton blocks: novel under this geometry
r["stability_spectrum"]    # survival vs perturbation radius
```

Intended use: offline curation queues. A generated level whose entities form
a new singleton block relative to your reference corpus is *novel under the
declared geometry* — route it to review. The SDK asserts nothing about
quality; that judgment needs ground truth the geometry does not contain.

## 5. Tool 3 — `analyze_trajectory(frames, encoders)` and the LLM adapter

Per-step partition VI plus cross-geometry collisions over a frame sequence.

```python
from mcl_sdk import LLMTrajectoryObserver
obs = LLMTrajectoryObserver(reference_snapshot)
for action in session:
    apply(action)                      # YOUR engine, YOUR validation
    obs.observe(current_snapshot())    # adapter only watches
report = obs.report()                  # post-hoc drift analysis
```

The adapter is strictly analytical: it has no veto and no callback into the
action loop. Two reasons this is a design decision and not a missing feature:
(1) per-action legality is an O(1) domain predicate in your engine — cheaper
and more correct than any geometric test; (2) lossy quotients can certify
semantically different states as equivalent, so a geometric gate would pass
exactly the states you most need to block. Use the adapter for what it
measures well: session-level behavioral drift relative to a reference corpus.

## 6. Authoring encoders

```python
from mcl_sdk import register_encoder
register_encoder("velocity", lambda native, raw: {k: v[2:] for k, v in native.items()})
```

Rules (violations raise `ForbiddenTransformation` or fail tests):
deterministic; total over the corpus; any randomness seeded by a declared
constant; no I/O beyond declared inputs. The runtime records each encoder's
source hash in output provenance. To detect representation artifacts, declare
encoders from *different families* — e.g., a feature-derived view and a raw
structural view. Two projections of the same features will agree by
construction and teach you nothing.

## 7. Determinism, provenance, audit

Given identical corpus bytes, encoder list, and seeds, outputs are identical.
Set `SOURCE_DATE_EPOCH=0` (or any fixed epoch) to pin timestamps for
byte-level reproducibility. Every output carries: kernel fingerprint, encoder
source hashes, seed registry, chain hash over all sections, and a
`validity_scope` block declaring what the result does and does not certify.
A chain hash proves the artifact was not altered after compilation; it does
not prove the computation answered the right question.

## 8. Failure modes to design around

| Anti-pattern | Why it fails | What to do instead |
|---|---|---|
| geometric legality gate | quotients collapse semantically distinct states | explicit domain predicates |
| single-encoder "collision" checks | collisions need ≥ 2 geometries; field is absent | declare a second, independent family |
| reading consensus as truth | within-family agreement is construction, not confirmation | check `single_family_run` |
| treating ε* as global robustness | adversarial radius is event-specific (merge direction) | use the spectrum triple: plateau / median / adversarial |
| real-time per-frame analysis in Python | O(n²) per call | batch, sample, or port the kernel |
| trusting `valid: true` as "trustworthy" | gate certifies structural admissibility only | external validation against your ground truth |

## 9. Minimal glossary

**Quotient / partition** — grouping of ids by within-τ connectivity.
**τ (tau)** — scale parameter; "barcode" policy picks it per geometry from the
merge spectrum. **VI** — distance between partitions. **Family** — encoders
sharing distance structure. **Φ-collision** — cross-geometry identity
disagreement. **Σ(λ)** — survival curve under perturbation. **Chain hash** —
integrity certificate over all output sections.
