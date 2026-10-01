"""Real-Data Qualification Workstream.

This package houses the qualification harness, source projection layer,
reconciliation accounting, invariant checking, metamorphic testing,
and sampling frameworks for Project ORBIT.

Governing principle:
All qualification code lives OUTSIDE src/shadow_orbit/.
The CSE-1 engine at commit 6d82d12 is frozen and must never be altered
to accommodate real data anomalies.
"""

__version__ = "0.1.0"
FROZEN_ENGINE_COMMIT = "6d82d12"
