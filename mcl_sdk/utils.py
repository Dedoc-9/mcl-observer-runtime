# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License v3 or later.
# See LICENSE for details.
"""Shared helpers re-exported from the frozen kernel."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcl_kernel import q_tau, project, vi, refines, merge_heights, perturb  # noqa: F401

CLAIM = "observer_agreement_only"

def tag(d):
    d["claim_class"] = CLAIM
    return d
