# Copyright (C) 2026 Daniel Dillberg <bigdilly95@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""SDK contract + behavior tests (pytest-compatible; runnable directly)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["SOURCE_DATE_EPOCH"] = "0"
from mcl_sdk import (detect_divergence, triage_content, analyze_trajectory,
                     LLMTrajectoryObserver, analyze, ForbiddenTransformation)
from mcl_sdk.simulation import entity_sim

A = {f"e{i}": [i * 0.1, 0.0, 1.0] for i in range(8)}
B = {k: list(v) for k, v in A.items()}; B["e5"][0] += 0.35


def test_divergence_detects_and_tags():
    r = detect_divergence(A, B)
    assert r["diverged"] and r["claim_class"] == "observer_agreement_only"
    assert "valid" not in r and "accept" not in r          # no verdict surface


def test_identity_is_clean():
    r = detect_divergence(A, {k: list(v) for k, v in A.items()})
    assert not r["diverged"] and not r["partition_diverged"]


def test_triage_outputs_scoped():
    r = triage_content(A)
    assert r["validity_scope"]["certifies"] == "structural_admissibility_only"
    assert r["claim_class"] == "observer_agreement_only"


def test_trajectory_drift_ticks():
    frames = entity_sim(seed=7, ticks=8, drift_tick=4, drift_entity="e05", drift=0.5)
    r = analyze_trajectory(frames)
    assert r["claim_class"] == "observer_agreement_only"
    assert isinstance(r["drift_ticks"], list)


def test_llm_adapter_has_no_gate():
    frames = entity_sim(seed=3, ticks=4, n=8)
    obs = LLMTrajectoryObserver(frames[0])
    for f in frames:
        assert obs.observe(f) is None                      # observer returns nothing actionable
    rep = obs.report()
    assert rep["claim_class"] == "observer_agreement_only"
    assert not any(k in rep for k in ("blocked", "rejected", "veto"))


def test_forbidden_transformations():
    try:
        analyze(A, encoders=("nope",)); assert False
    except ForbiddenTransformation:
        pass
    try:
        analyze(A, encoders=("fullstate", "spatial"), tau_policy="fixed:0.25")
        assert False
    except ForbiddenTransformation:
        pass


def test_universe_mismatch_raises():
    try:
        detect_divergence(A, {"other": [0.0, 0.0, 1.0]}); assert False
    except ValueError as e:
        assert "universe_mismatch" in str(e)


def test_determinism():
    r1, r2 = detect_divergence(A, B), detect_divergence(A, B)
    assert r1 == r2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"{len(fns)}/{len(fns)} passed")
