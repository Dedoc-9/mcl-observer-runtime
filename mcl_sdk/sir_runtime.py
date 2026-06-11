#!/usr/bin/env python3
# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
SIR Analyzer Runtime (SIR-RT-1.0). Implements SIR_RUNTIME_SPEC.md.
The LLM/user-facing surface: analyze(corpus, encoders, tau_policy, outputs).
Deterministic. Geometry-tagged. Hard-fails on forbidden transformations.
"""
import hashlib, inspect, json, math, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mcl_kernel import q_tau, vi, merge_heights, perturb, KERNEL_VERSION
from separability_engine import SeparabilityEngine, euclidean_distance

RUNTIME = "SIR-RT-1.0"
COINCIDENT_TOL = 1e-9
FAMILY_SPEARMAN = 0.6
SEEDS = {"spectrum_seed": 0, "randproj_seed": 42}

class ForbiddenTransformation(Exception):
    pass

# ---------------- builtin encoders (Layer C plug surface) ----------------

def _enc_native(native, raw):
    return native

def _enc_mss4(native, raw):
    return {t["trace_id"]: [t["layer_consistency"]["l1_l2"],
                            t["coherence_rupture"]["magnitude"],
                            t["regime"]["entropy"],
                            t["regime"]["spectral_condition"]] for t in raw}

def _enc_rank(native, raw):
    ids = sorted(native); d = len(native[ids[0]])
    out = {i: [0.0]*d for i in ids}
    for k in range(d):
        for r, i in enumerate(sorted(ids, key=lambda i: native[i][k])):
            out[i][k] = r / max(len(ids) - 1, 1)
    return out

def _enc_randproj6(native, raw):
    rng = random.Random(SEEDS["randproj_seed"])
    ids = sorted(native); d = len(native[ids[0]])
    M = [[rng.gauss(0, 1/math.sqrt(6)) for _ in range(d)] for _ in range(6)]
    return {i: [sum(M[r][k]*native[i][k] for k in range(d)) for r in range(6)]
            for i in ids}

_REGISTRY = {"native": _enc_native, "mss4": _enc_mss4,
             "rank": _enc_rank, "randproj6": _enc_randproj6}

def register_encoder(name, fn):
    """Custom encoders must be deterministic (spec section 2)."""
    _REGISTRY[name] = fn

# ---------------- runtime ----------------

def _spearman(x, y):
    def rank(v):
        r = [0.0]*len(v)
        for pos, i in enumerate(sorted(range(len(v)), key=lambda i: v[i])):
            r[i] = pos
        return r
    rx, ry = rank(x), rank(y)
    mx, my = sum(rx)/len(rx), sum(ry)/len(ry)
    num = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))
    return num/den if den else 0.0

def _h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()
                          ).hexdigest()[:16]

def analyze(corpus, encoders=("native",), tau_policy="barcode",
            outputs=("partition_family", "vi_matrix", "consensus_CU",
                     "phi_collisions"),
            n_directions=30):
    # ---- corpus ingestion ----
    if isinstance(corpus, str):
        with open(corpus) as fh:
            raw = json.load(fh)
    elif isinstance(corpus, list):
        raw = corpus
    else:  # raw signature dict
        raw = None
    if raw is not None:
        eng = SeparabilityEngine(); eng.extract_signatures(raw)
        native = eng.signatures
    else:
        native = dict(corpus)

    # ---- F1/F7 enforcement ----
    for e in encoders:
        if e not in _REGISTRY:
            raise ForbiddenTransformation(f"F1: undeclared encoder '{e}'")
    if tau_policy.startswith("fixed:") and len(encoders) > 1:
        raise ForbiddenTransformation("F7: fixed tau with multiple encoders")

    sigs, enc_meta = {}, {}
    for e in sorted(encoders):
        s = _REGISTRY[e](native, raw or [])
        if set(s) != set(native):
            raise ForbiddenTransformation(f"F2/totality: encoder '{e}' not total")
        if tau_policy == "barcode":
            hs = merge_heights(s)
            if len(hs) >= 2:
                a, b = max(zip(hs, hs[1:]), key=lambda g: g[1]-g[0])
                tau = (a + b) / 2
            else:
                tau = (hs[0] if hs else 1.0) * 0.99
        else:
            tau = float(tau_policy.split(":")[1])
        sigs[e] = s
        P = q_tau(s, set(s), tau)
        src = inspect.getsource(_REGISTRY[e])
        enc_meta[e] = {"tau": round(tau, 6), "sizes": [len(b) for b in P],
                       "source_hash": hashlib.sha256(src.encode()).hexdigest()[:16]}
        enc_meta[e]["_partition"] = P

    ids = sorted(native)
    pairs = [(a, b) for i, a in enumerate(ids) for b in ids[i+1:]]
    names = sorted(encoders)

    # families by distance-structure correlation (F13 mechanism)
    dv = {e: [euclidean_distance(sigs[e][a], sigs[e][b]) for a, b in pairs]
          for e in names}
    fam = {names[0]: 0}; next_id = 1
    for e in names[1:]:
        for f, fid in list(fam.items()):
            if _spearman(dv[e], dv[f]) >= FAMILY_SPEARMAN:
                fam[e] = fid; break
        else:
            fam[e] = next_id; next_id += 1

    result = {"runtime": RUNTIME, "kernel_version": KERNEL_VERSION,
              "kernel_fingerprint": hashlib.sha256(
                  open(os.path.join(HERE, "mcl_kernel.py"), "rb").read()
                  ).hexdigest()[:16],
              "encoders": {e: {k: v for k, v in m.items() if k != "_partition"}
                           for e, m in enc_meta.items()},
              "families": {e: f"family_{fam[e]}" for e in names},
              "seeds": dict(SEEDS)}

    if "partition_family" in outputs:
        result["partition_family"] = {e: enc_meta[e]["_partition"] for e in names}
    if "vi_matrix" in outputs:
        result["vi_matrix"] = [
            {"a": a, "b": b,
             "vi": round(vi(enc_meta[a]["_partition"], enc_meta[b]["_partition"]), 6),
             "same_family": fam[a] == fam[b]}  # F3: mandatory annotation
            for i, a in enumerate(names) for b in names[i+1:]]
    if "consensus_CU" in outputs:
        agree = {p: 0 for p in pairs}
        for e in names:
            look = {x: j for j, blk in enumerate(enc_meta[e]["_partition"])
                    for x in blk}
            for p in pairs:
                if look[p[0]] == look[p[1]]: agree[p] += 1
        C = sorted(list(p) for p, c in agree.items() if c == len(names))
        hist = {}
        for c in agree.values(): hist[str(c)] = hist.get(str(c), 0) + 1
        c_identity = all(
            euclidean_distance(native[a], native[b]) < COINCIDENT_TOL
            for a, b in C) if C else True
        result["consensus"] = {"C_pairs": C, "U_count":
                               sum(1 for c in agree.values() if c >= 1),
                               "n_pairs": len(pairs),
                               "agreement_histogram": dict(sorted(hist.items()))}
        result.setdefault("validity_scope", {})[
            "consensus_is_identity_relation"] = c_identity
    if "phi_collisions" in outputs and len(names) >= 2:
        cols = []
        for a, b in pairs:
            coin = [e for e in names
                    if euclidean_distance(sigs[e][a], sigs[e][b]) < COINCIDENT_TOL]
            dist = [e for e in names
                    if euclidean_distance(sigs[e][a], sigs[e][b]) >= enc_meta[e]["tau"]]
            if coin and dist:
                cols.append({"pair": [a, b], "coincident_in": coin,
                             "distant_in": dist,
                             "d_distant": round(max(
                                 euclidean_distance(sigs[e][a], sigs[e][b])
                                 for e in dist), 6)})
        result["phi_collisions"] = cols
    if "stability_spectrum" in outputs:
        spec = {}
        for e in names:
            t = enc_meta[e]["tau"]; P0 = enc_meta[e]["_partition"]
            spec[e] = []
            for frac in (0.2, 0.5, 1.0):
                lam = frac * t
                surv = sum(1 for s in range(n_directions)
                           if vi(P0, q_tau(perturb(sigs[e], lam,
                                                   SEEDS["spectrum_seed"] + s),
                                           set(ids), t)) == 0.0) / n_directions
                spec[e].append({"lambda": round(lam, 6), "survival": surv})
        result["stability_spectrum"] = spec

    vs = result.setdefault("validity_scope", {})
    vs.update({"geometry_relative": True,
               "certifies": "structural_admissibility_only",
               "single_family_run": len(set(fam.values())) == 1,
               "consensus_meaning": ("within_family_only"
                                     if len(set(fam.values())) == 1
                                     else "cross_family"),
               "unmeasured_axes": ["external_validity", "semantic_correctness"]})
    result["chain_hash"] = _h({k: v for k, v in sorted(result.items())
                               if k != "chain_hash"})
    return result

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--encoders", default="native,mss4,rank,randproj6")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    r = analyze(a.input, encoders=a.encoders.split(","),
                outputs=("partition_family", "vi_matrix", "consensus_CU",
                         "phi_collisions", "stability_spectrum"))
    with open(a.output, "w") as fh:
        json.dump(r, fh, indent=2, sort_keys=True)
    print(f"[SIR-RT] chain={r['chain_hash']} encoders={list(r['encoders'])} "
          f"families={r['families']} collisions={len(r.get('phi_collisions', []))}")
