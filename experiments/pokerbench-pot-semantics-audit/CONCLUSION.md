# TRAIN-only pot semantics audit

No converter rounding defect was found. The original cached records contain only instruction/output/source_index; there is no richer numeric pot field. Three original TRAIN literals already disagree with canonical contribution sums by half a chip:21.0vs21.5(HJ),38.0vs38.5(BTN),70.0vs70.5(BB). Exact Decimal scaling maps them to42vs43,76vs77,140vs141. The integer conversion is guarded by an integrality check and introduces no rounding.

All2439off-one scaled cases match a half-chip-down discrepancy in the original printed state.1667also coincide with excluding folded-player dead contributions, so the text alone cannot distinguish a printer/flooring defect from simplified source pot semantics. The other597larger mismatches are not explained by the active-only contribution sum; they remain quarantined. A TRAIN example with both blinds active produces canonical80versusprinted70, demonstrating that omitted dead blinds alone is insufficient.

The4096source TRAIN positions are BB1429/SB424/HJ710/BTN1015/UTG323/CO195. Requiring exact canonical pot leaves BB647/SB386/HJ12/BTN11/UTG4/CO0, explaining V4's97.45%blind-position scope. Current V4 training remains fixed; its intended claim is narrow blind-position knowledge transfer rather than broad tournament coverage.

Recomputing a printed pot from the stated actions and forced blinds would not invent actions and need not change the expert action label mechanically. It would, however, change the expert's stated pot odds; without the original solver state or richer numeric source field there is no proof that the unchanged label is still optimal. No data repair, upload, retraining or current-job change was performed.

A separate exposure incident is documented precisely: a broad source search emitted up to20original source rows, conservatively exposing2retained V3FINAL source rows. Their entire scenario groups are excluded from every future V4/V5final via `future-final-exclusions.json`. Metadata-only joining finds1affected row in original V4FINAL, leaving388unexposed rows across291groups. Original final files/hashes are unchanged; no final model calls occurred. Those extra source rows were not used for this audit, selection or model choice. Do not claim the exposed final rows remained unseen.

Evidence: `scaling-trace.json`, `report.json`, `exposure-audit.json`, `future-final-exclusions.json`. Exact few original TRAIN examples are retained locally under ignored `raw/`.
