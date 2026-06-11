# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License v3 or later.
# See LICENSE for details.
"""Deterministic entity-simulation helpers for examples and tests."""
import random


def entity_sim(seed, ticks, n=12, drift_tick=None, drift_entity=None, drift=0.0):
    rng = random.Random(seed)
    ents = {f"e{i:02d}": [rng.uniform(0, 1), rng.uniform(0, 1), 1.0]
            for i in range(n)}
    frames = []
    for t in range(ticks):
        for i, k in enumerate(sorted(ents)):
            r = random.Random(seed * 1000003 + t * 1009 + i)  # string-hash-free
            ents[k][0] += 0.01 * r.uniform(-1, 1)
            ents[k][1] += 0.01 * r.uniform(-1, 1)
        if drift_tick is not None and t == drift_tick:
            ents[drift_entity][0] += drift
        frames.append({k: list(v) for k, v in ents.items()})
    return frames
