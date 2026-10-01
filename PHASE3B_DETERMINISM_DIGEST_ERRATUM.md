# ORBIT Phase 3B Erratum — Determinism Digest Discrepancy

**Date:** 2026-09-30  
**Scope:** Phase 3B research artifact only  
**Production semantic impact:** None

The Phase 3B machine-readable determinism artifact and the formal Phase 3B report contain different digest strings.

| Artifact | Bundle digest | Evaluation digest |
|---|---|---|
| `phase3b_determinism.json` | `504b2f03d86090cf40e23b76f8c46123b07dc222275aeea9ac081460b3420bed` | `7fc973824bd228b8db298d4a26d3ae310e4cd3987f3f10183c568d75fa7222a0` |
| `phase3b_report.md` | `504b2f03d86090cfb2e617d911b3bc58b292e9dbba068f230da37197b0a701df` | `7fc973824bd228b8cf5b2cbfe665d95d430c5e3170e28fcf52243d4c3a2688ca` |

The machine-readable artifact reports deterministic repeated and permuted execution. The formal report's digest strings do not match that artifact.

The discrepancy is classified as a **reporting/documentation artifact defect**, not an engine semantic defect and not evidence that the deterministic evaluator failed.

The original `phase3b_report.md` must remain unchanged unless a separately regenerated report is produced and the Phase 3B hash manifest is correspondingly regenerated. Phase 4A therefore records this erratum rather than mutating the frozen Phase 3B artifact.

**Authoritative execution-result values for future canonical references:** use the values recorded in `phase3b_determinism.json`, while retaining the original report as historical evidence of what was issued at Phase 3B completion.
