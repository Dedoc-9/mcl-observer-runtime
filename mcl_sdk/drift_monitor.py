# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License v3 or later.
# See LICENSE for details.
"""Tool 1 & 3: divergence detection (two snapshots) and trajectory drift
(frame series). Diagnostic only: detection requires drift to cross emitted
observables; sub-block drift is invisible by design. Never gates actions."""
from .analyze import analyze
from .utils import vi, tag
from . import encoders  # noqa: F401  (registers builtins)


def detect_divergence(snapshot_a, snapshot_b, encoders=("fullstate", "spatial")):
    if set(snapshot_a) != set(snapshot_b):
        raise ValueError("universe_mismatch: snapshots must share the same id set; "
                         "comparison across different universes is undefined")
    ra = analyze(snapshot_a, encoders=encoders, outputs=("partition_family",))
    rb = analyze(snapshot_b, encoders=encoders, outputs=("partition_family",))
    per_geom, implicated = {}, set()
    for e in sorted(encoders):
        v = vi(ra["partition_family"][e], rb["partition_family"][e])
        per_geom[e] = round(v, 6)
        if v > 0:
            la = {x: i for i, b in enumerate(ra["partition_family"][e]) for x in b}
            lb = {x: i for i, b in enumerate(rb["partition_family"][e]) for x in b}
            implicated |= {x for x in la
                           if {y for y in la if la[y] == la[x]}
                           != {y for y in lb if lb[y] == lb[x]}}
    return tag({"diverged": ra["chain_hash"] != rb["chain_hash"],
                "partition_diverged": any(v > 0 for v in per_geom.values()),
                "vi_per_geometry": per_geom, "implicated": sorted(implicated),
                "chain_hashes": [ra["chain_hash"], rb["chain_hash"]],
                "validity_scope": ra["validity_scope"]})


def analyze_trajectory(frames, encoders=("fullstate", "spatial")):
    steps, prev = [], None
    for t, frame in enumerate(frames):
        r = analyze(frame, encoders=encoders,
                    outputs=("partition_family", "phi_collisions"))
        step = {"t": t, "chain_hash": r["chain_hash"],
                "collisions": len(r.get("phi_collisions", []))}
        if prev is not None:
            step["vi_from_prev"] = {e: round(vi(prev["partition_family"][e],
                                                r["partition_family"][e]), 6)
                                    for e in sorted(encoders)}
        steps.append(step)
        prev = r
    drift = [s["t"] for s in steps
             if any(v > 0 for v in s.get("vi_from_prev", {}).values())]
    return tag({"steps": steps, "drift_ticks": drift,
                "validity_scope": prev["validity_scope"] if prev else {}})
