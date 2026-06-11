# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline triage of a generated layout: blocks, outliers, stability."""
import os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
from mcl_sdk import triage_content

rng = random.Random(0)
level = {f"room{i:02d}": [rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 1)]
         for i in range(15)}
level["room99"] = [5.0, 5.0, 0.1]   # structurally novel room
r = triage_content(level, encoders=("spatial",))
print("blocks:", [len(b) for b in r["partition_family"]["spatial"]])
print("outliers (novel under this geometry):", r["structural_outliers"])
print("spectrum:", r["stability_spectrum"]["spatial"])
