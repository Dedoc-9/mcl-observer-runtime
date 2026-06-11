# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License v3 or later.
# See LICENSE for details.
"""Core entrypoint: deterministic, contract-enforcing analyze()."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sir_runtime import analyze, ForbiddenTransformation  # noqa: F401
