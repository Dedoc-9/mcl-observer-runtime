#!/usr/bin/env python3
"""
MCL-Ω: Separability Engine (Pure-Python Canonical)

Copyright (c) 2026 MCL Project Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

================================================================================
MCL-Ω SEPARABILITY ENGINE (Pure Python, Deterministic, Canonical)

Consumes MCL-ECR JSON outputs.
Computes empirical separability and equivalence classes.
Frozen, deterministic, non-invasive, portable.

PRINCIPLES:
  - Deterministic: identical input → identical output
  - Pure Python: no external dependencies
  - LLM-callable: can be invoked from any environment
  - Empirical only: no universal claims, finite-sample analysis

CONFIGURATION (LOCKED):
  - Distance metric: Euclidean
  - Cluster threshold: 0.25 (collapse threshold)
  - Blind spot ratio: 0.5 (overlap threshold)
================================================================================
"""

import json
import math
from datetime import datetime, timezone
from collections import defaultdict
from typing import Dict, List, Any, Tuple


# ============================================================================
# CONFIGURATION (LOCKED)
# ============================================================================

DISTANCE_METRIC = "euclidean"
CLUSTER_THRESHOLD = 0.25      # collapse distance for equivalence classes
BLIND_SPOT_RATIO = 0.5        # fraction of overlap defining blind spot
NORMALIZATION_EPSILON = 1e-9


# ============================================================================
# UTILITY FUNCTIONS (Deterministic)
# ============================================================================

def _omega_timestamp():
    """B1: reproducible-builds convention; SOURCE_DATE_EPOCH pins timestamp."""
    import os
    e = os.environ.get("SOURCE_DATE_EPOCH")
    t = datetime.fromtimestamp(int(e), tz=timezone.utc) if e else datetime.now(timezone.utc)
    return t.isoformat().replace("+00:00", "Z")

def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute Euclidean distance between two vectors (deterministic).

    Args:
        vec1, vec2: Lists of floats

    Returns:
        Distance (float)
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vector lengths must match")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


def normalize_vector(vec: List[float]) -> List[float]:
    """
    Normalize vector to unit length (deterministic).

    Args:
        vec: List of floats

    Returns:
        Normalized vector
    """
    norm = math.sqrt(sum(x**2 for x in vec))
    if norm < NORMALIZATION_EPSILON:
        return vec
    return [x / norm for x in vec]


def compute_mean(values: List[float]) -> float:
    """Compute mean of values."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def compute_std(values: List[float]) -> float:
    """Compute standard deviation of values."""
    if len(values) < 2:
        return 0.0
    mean = compute_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


# ============================================================================
# CORE SEPARABILITY ENGINE
# ============================================================================

class SeparabilityEngine:
    """
    Compute empirical separability structure of MCL-ECR signature space.

    Pure Python, deterministic, frozen.
    """

    def __init__(self):
        """Initialize engine with locked parameters."""
        self.signatures = {}              # trace_id → normalized vector
        self.classes = defaultdict(list)  # class label → trace_ids
        self.equivalence_classes = []     # list of clusters
        self.blind_spots = []             # list of overlap regions
        self.centroids = {}               # class label → centroid vector
        self.spreads = {}                 # class label → spread (float)

    def extract_signatures(self, mcl_outputs: List[Dict[str, Any]]) -> None:
        """
        Convert MCL-ECR outputs to signature vectors.

        Each signature is an 11-dimensional vector of MCL-ECR metrics.

        Args:
            mcl_outputs: List of MCL-ECR JSON output dicts
        """
        self.signatures = {}
        self.classes = defaultdict(list)

        for trace in mcl_outputs:
            trace_id = trace.get("trace_id", f"trace_{len(self.signatures)}")

            # Extract components (raw)
            layer_consistency = trace.get("layer_consistency", {})
            rupture = trace.get("coherence_rupture", {})
            regime = trace.get("regime", {})

            # Build raw vector
            raw_vec = [
                float(layer_consistency.get("l1_l2", 0.5)),
                float(layer_consistency.get("l2_l3", 0.5)),
                float(layer_consistency.get("l3_l4", 0.5)),
                float(layer_consistency.get("l4_l5", 0.5)),
                float(rupture.get("magnitude", 0.0)),
                float(rupture.get("confidence", 0.5)),
                float(regime.get("entropy", 0.0)),
                float(regime.get("spectral_condition", 1.0)),
                1.0 if rupture.get("detected", False) else 0.0,
                compute_mean([layer_consistency.get(k, 0.5) for k in ["l1_l2", "l2_l3", "l3_l4", "l4_l5"]]),
                compute_std([layer_consistency.get(k, 0.5) for k in ["l1_l2", "l2_l3", "l3_l4", "l4_l5"]])
            ]

            # Normalize
            normalized_vec = normalize_vector(raw_vec)
            self.signatures[trace_id] = normalized_vec

            # Assign to observed class
            classification = regime.get("classification", "UNKNOWN")
            self.classes[classification].append(trace_id)

    def cluster_equivalence_classes(self) -> None:
        """
        Single-linkage clustering with fixed threshold (deterministic).

        Clusters signatures by Euclidean distance in normalized space.
        Two traces belong to same equivalence class if distance < CLUSTER_THRESHOLD.
        """
        unvisited = set(self.signatures.keys())
        clusters = []

        while unvisited:
            # Start new cluster with arbitrary unvisited trace
            seed = next(iter(unvisited))
            unvisited.remove(seed)
            cluster = [seed]

            # Grow cluster: single-linkage
            added = True
            while added:
                added = False
                to_remove = []

                for other in unvisited:
                    # Check if other is close to ANY member of cluster
                    for member in cluster:
                        dist = euclidean_distance(
                            self.signatures[other],
                            self.signatures[member]
                        )
                        if dist < CLUSTER_THRESHOLD:
                            cluster.append(other)
                            to_remove.append(other)
                            added = True
                            break

                for tid in to_remove:
                    unvisited.remove(tid)

            clusters.append(cluster)

        self.equivalence_classes = clusters

    def compute_centroids_and_spreads(self) -> None:
        """
        Compute centroid and spread for each observed class (deterministic).
        """
        self.centroids = {}
        self.spreads = {}

        for class_label, trace_ids in self.classes.items():
            if not trace_ids:
                continue

            # Collect vectors
            vecs = [self.signatures[tid] for tid in trace_ids]

            # Compute centroid
            centroid = [
                compute_mean([v[i] for v in vecs])
                for i in range(len(vecs[0]))
            ]

            # Compute spread
            distances = [
                euclidean_distance(v, centroid) for v in vecs
            ]
            spread = compute_mean(distances) if distances else 0.0

            self.centroids[class_label] = centroid
            self.spreads[class_label] = spread

    def detect_blind_spots(self) -> None:
        """
        Identify clusters where multiple MCL classes overlap (deterministic).

        A blind spot is where MCL-ECR cannot distinguish genuinely different
        input classes because their output signatures collapse.
        """
        self.blind_spots = []

        # Map each trace to its input class
        class_map = {}
        for class_label, trace_ids in self.classes.items():
            for tid in trace_ids:
                class_map[tid] = class_label

        # Check each equivalence cluster
        for cluster in self.equivalence_classes:
            # Which input classes are in this cluster?
            cluster_classes = set()
            for tid in cluster:
                if tid in class_map:
                    cluster_classes.add(class_map[tid])

            # If multiple input classes → blind spot
            if len(cluster_classes) > 1:
                overlap_ratio = len(cluster_classes) / max(len(cluster), 1)
                if overlap_ratio >= BLIND_SPOT_RATIO:
                    self.blind_spots.append({
                        "cluster": cluster,
                        "overlap_classes": sorted(list(cluster_classes)),
                        "severity": float(overlap_ratio)
                    })

    def compute_resolution_frontier(self) -> float:
        """
        Estimate minimal perturbation magnitude for class separation (deterministic).

        Returns:
            Minimal distance threshold
        """
        return float(CLUSTER_THRESHOLD)

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate locked-schema JSON report (deterministic).

        Returns:
            Report dict matching output_schema.json
        """
        # Compute statistics
        self.compute_centroids_and_spreads()
        self.detect_blind_spots()

        # Format equivalence classes
        equivalence = []
        # B1: canonical class order (by size desc, then lexicographic first member)
        _ordered = sorted(self.equivalence_classes, key=lambda c: (-len(c), sorted(c)[0] if c else ""))
        for i, cluster in enumerate(_ordered):
            equivalence.append({
                "class_id": f"equiv_{i}",
                "members": sorted(cluster),  # B1: stable serialization order
                "size": len(cluster)
            })

        # Format blind spots
        blind_spots = []
        for spot in self.blind_spots:
            blind_spots.append({
                "overlap_classes": spot["overlap_classes"],
                "severity": spot["severity"],
                "interpretation": (
                    f"MCL-ECR cannot distinguish {' from '.join(spot['overlap_classes'])} "
                    f"(overlap severity: {spot['severity']:.2f})"
                )
            })

        # Build report
        report = {
            "version": "1.0",
            "timestamp": _omega_timestamp(),
            "class_statistics": {
                label: {
                    "centroid": self.centroids.get(label, []),
                    "spread": self.spreads.get(label, 0.0),
                    "size": len(self.classes.get(label, []))
                }
                for label in self.classes.keys()
            },
            "equivalence_classes": equivalence,
            "blind_spots": blind_spots,
            "resolution_frontier": self.compute_resolution_frontier(),
            "interpretation": "Empirical separability mapping; does not predict events",
            "epistemic_boundary": "Ω measures MCL-ECR output space only, never D0 reality"
        }

        return report

    def run(self, mcl_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run complete separability analysis (deterministic).

        Args:
            mcl_outputs: MCL-ECR JSON outputs

        Returns:
            Separability report
        """
        self.extract_signatures(mcl_outputs)
        self.cluster_equivalence_classes()
        return self.generate_report()
