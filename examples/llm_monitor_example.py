# SPDX-License-Identifier: AGPL-3.0-or-later
"""LLM-agent session monitoring: observer only, post-hoc report."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
from mcl_sdk import LLMTrajectoryObserver
from mcl_sdk.simulation import entity_sim

reference = entity_sim(seed=1, ticks=1, n=10)[0]
obs = LLMTrajectoryObserver(reference)
# pretend an LLM-driven agent produced these states (drift at tick 5)
for frame in entity_sim(seed=1, ticks=10, n=10, drift_tick=5,
                        drift_entity="e03", drift=0.6):
    obs.observe(frame)        # the adapter never blocks anything
rep = obs.report()
print("drift ticks:", rep["drift_ticks"])
print("vs reference diverged:", rep["vs_reference"]["diverged"])
print("claim class:", rep["claim_class"])
