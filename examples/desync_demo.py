# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lockstep replica divergence: inject drift, detect, localize."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
from mcl_sdk import detect_divergence
from mcl_sdk.simulation import entity_sim

server = entity_sim(seed=7, ticks=40)
client = entity_sim(seed=7, ticks=40, drift_tick=30, drift_entity="e05", drift=0.3)
for t in range(40):
    r = detect_divergence(server[t], client[t])
    if r["diverged"]:
        print(f"divergence at tick {t}; partition-level: {r['partition_diverged']}; "
              f"implicated: {r['implicated'] or 'sub-block (hash only)'}")
        break
else:
    print("no divergence detected (drift below quotient resolution)")
