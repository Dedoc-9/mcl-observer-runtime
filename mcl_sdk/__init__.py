# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License v3 or later.
# See LICENSE for details.
"""mcl-ecr-sdk: observer-relative structure diagnostics.

Contract: all outputs are statements about agreement between observers,
never about validity of the underlying state."""
from .analyze import analyze, ForbiddenTransformation
from .encoders import register_encoder
from .drift_monitor import detect_divergence, analyze_trajectory
from .procedural_triage import triage_content
from .llm_adapter import LLMTrajectoryObserver

__version__ = "1.0.0"
__all__ = ["analyze", "register_encoder", "detect_divergence",
           "analyze_trajectory", "triage_content", "LLMTrajectoryObserver",
           "ForbiddenTransformation"]
