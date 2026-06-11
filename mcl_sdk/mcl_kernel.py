#!/usr/bin/env python3
# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
MCL KERNEL — the single canonical math kernel for the SIR stack.

RULE (enforced by test_sir_stack.py firewall): no other module in the active
compiler/analysis path may define q_tau, vi, project, refines, merge_heights,
perturb, or the defect predicate. Everything imports from here.

Sealed exceptions (frozen-spec-bound, grandfathered, not in the active path):
  sheaf_layer.py (SPEC 233dd39e44b917a7), persistence_observer.py.

Metric authority: euclidean_distance is imported from the frozen
separability_engine — the kernel does not redefine the metric.

Determinism contract: every stochastic function takes an explicit seed.
There are NO module-level RNG instances and NO unseeded calls.

Numeric contract: VI < KERNEL_TOL is exactly 0.0 (float-residue ghost, L4/S4).
"""
import math
import random

from separability_engine import euclidean_distance, CLUSTER_THRESHOLD

KERNEL_VERSION = "1.0"
KERNEL_TOL = 1e-12


def q_tau(sig, idset, tau):
    """Single-linkage partition at tau (strict: d < tau). Deterministic."""
    ids = sorted(idset)
    parent = {x: x for x in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if euclidean_distance(sig[a], sig[b]) < tau:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)
    blocks = {}
    for x in ids:
        blocks.setdefault(find(x), []).append(x)
    return sorted((sorted(v) for v in blocks.values()), key=lambda b: (-len(b), b[0]))


def project(P, V):
    """Restriction by slicing: P|_V."""
    V = set(V)
    return sorted((sorted(set(b) & V) for b in P if set(b) & V),
                  key=lambda b: (-len(b), b[0]))


def vi(P, Q):
    """Variation of information; exact zero under KERNEL_TOL."""
    n = sum(len(b) for b in P)
    assert n == sum(len(b) for b in Q), "partitions over different universes"
    if n == 0:
        return 0.0
    Ps, Qs = [set(b) for b in P], [set(b) for b in Q]
    H = lambda R: -sum(len(b) / n * math.log(len(b) / n) for b in R if b)
    I = sum(len(b & c) / n * math.log(n * len(b & c) / (len(b) * len(c)))
            for b in Ps for c in Qs if b & c)
    v = H(Ps) + H(Qs) - 2 * I
    return 0.0 if v < KERNEL_TOL else v


def refines(P, Q):
    """True iff every block of P lies inside one block of Q (fixed universe)."""
    look = {x: i for i, q in enumerate(Q) for x in q}
    return all(len({look[x] for x in p}) == 1 for p in P)


def is_defect(P_global, V, sig, tau):
    """THE defect predicate: VI(P_global|_V, Q_tau(V)) > 0."""
    return vi(project(P_global, V), q_tau(sig, V, tau)) > 0


def merge_heights(sig):
    """Single-linkage merge spectrum (H0 barcode events), ascending."""
    ids = sorted(sig)
    edges = sorted((euclidean_distance(sig[a], sig[b]), a, b)
                   for i, a in enumerate(ids) for b in ids[i + 1:])
    parent = {x: x for x in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    hs = []
    for d, a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
            hs.append(d)
    return hs


def perturb(sig, eps, seed):
    """Isotropic perturbation, norm eps per point. Seed is REQUIRED."""
    rng = random.Random(seed)
    out = {}
    for k, v in sorted(sig.items()):
        d = [rng.gauss(0, 1) for _ in v]
        n = math.sqrt(sum(c * c for c in d)) or 1.0
        out[k] = [a + eps * c / n for a, c in zip(v, d)]
    return out


def restriction_battery(sig, tau, f, B, seed):
    """Defect rate and max VI under B seeded random restrictions at retention f."""
    rng = random.Random(seed)
    ids = sorted(sig)
    P = q_tau(sig, set(ids), tau)
    m = max(2, round(f * len(ids)))
    ds = []
    for _ in range(B):
        V = set(rng.sample(ids, m))
        ds.append(vi(project(P, V), q_tau(sig, V, tau)))
    pos = [d for d in ds if d > 0]
    return {"defect_rate": len(pos) / B, "max_D": max(ds), "B": B, "f": f}
