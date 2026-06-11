# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License v3 or later.
# See LICENSE for details.
"""Tool 2: block structure + stability spectrum of one snapshot.
Offline/async. Flags structural outliers (novelty), never quality or fun."""
from .analyze import analyze
from .utils import tag
from . import encoders  # noqa: F401


def triage_content(snapshot, encoders=("spatial",), n_directions=30):
    r = analyze(snapshot, encoders=encoders,
                outputs=("partition_family", "stability_spectrum"),
                n_directions=n_directions)
    e = sorted(encoders)[0]
    singletons = [b[0] for b in r["partition_family"][e] if len(b) == 1]
    return tag({"partition_family": r["partition_family"],
                "stability_spectrum": r["stability_spectrum"],
                "structural_outliers": singletons,
                "validity_scope": r["validity_scope"],
                "chain_hash": r["chain_hash"]})
