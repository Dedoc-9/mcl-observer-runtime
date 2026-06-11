# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License v3 or later.
# See LICENSE for details.
"""Optional LLM adapter — STRICTLY ANALYTICAL.

Treats an LLM-driven agent as an observed process: you feed state snapshots
produced while the agent acts; the adapter reports structural drift relative
to a reference corpus. It exposes no veto, no gate, no callback into the
agent's action loop. If you need action validation, write explicit domain
predicates in your engine; this module cannot and will not do that."""
from .drift_monitor import analyze_trajectory, detect_divergence
from .utils import tag


class LLMTrajectoryObserver:
    def __init__(self, reference_snapshot, encoders=("fullstate", "spatial")):
        self.reference = reference_snapshot
        self.encoders = tuple(encoders)
        self.frames = []

    def observe(self, snapshot):
        """Record one post-action snapshot. Returns nothing actionable."""
        self.frames.append({k: list(v) for k, v in snapshot.items()})

    def report(self):
        """Post-hoc drift report over the observed session."""
        out = analyze_trajectory(self.frames, encoders=self.encoders)
        out["vs_reference"] = detect_divergence(
            self.reference, self.frames[-1], encoders=self.encoders
        ) if self.frames else None
        return tag(out)
