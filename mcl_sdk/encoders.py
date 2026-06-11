# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License v3 or later.
# See LICENSE for details.
"""Encoder registry. Encoders are deterministic callables
(native, raw) -> {id: vector}, total over the corpus."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sir_runtime import register_encoder  # noqa: F401

register_encoder("fullstate", lambda native, raw: native)
register_encoder("spatial", lambda native, raw: {k: v[:2] for k, v in native.items()})
