# Model Evaluation

## What we measure (and why accuracy alone is not enough)

Phishing detection is cost-asymmetric: a missed phish (false negative) hurts
more than a false alarm, but too many false alarms destroy trust. Every
evaluation therefore reports the full suite:

| Metric | Answers | Target direction |
|---|---|---|
| Accuracy | Overall correctness | Informational only on imbalanced data |
| Precision (phishing) | Of flagged mail, how much is really phishing? | High (avoid alert fatigue) |
| Recall (phishing) | Of real phishes, how many caught? | High (avoid missed threats) |
| F1 (phishing) | Precision/recall trade-off | Primary single-number summary |
| False-positive rate | Legitimate mail flagged | As low as tolerable |
| False-negative rate | Phishes missed | As low as tolerable |
| Log loss / Brier score | Do probabilities match outcomes? | Required before showing `%` |
| CV F1-macro | Stability across folds | Should match holdout closely |

## Protocol

1. **Pipeline-correct CV** — `train_model.py` cross-validates a
   `Pipeline(TFIDF → ensemble)` on raw text (5-fold stratified, F1-macro),
   so each fold fits its own vocabulary/IDF. Fitting TF-IDF before splitting
   leaks validation data into preprocessing and inflates scores.
2. **Stratified holdout** — 80/20 split, `random_state=42`, reporting the
   table above plus the confusion matrix.
3. **Source-separated holdout** — `source_split_eval.py` holds out entire
   dataset sources/campaigns when the `source` column exists. This is the
   realistic generalization estimate; expect it below the random-split score.
   Safeguards: seeded source order (`SOURCE_SEED`), minimum 50 rows per class
   in the holdout, exact sources + class counts recorded in the report,
   duplicate-group (`group_id`) disjointness enforced so identical texts from
   multiple sources cannot leak across, and the holdout is never used for
   threshold selection.
4. **Frozen test data** — the final test split is never used for model or
   threshold selection. Thresholds (75/45) must be re-validated here, not
   tuned here.
5. **Calibration** — log loss and Brier score are printed by both training
   and evaluation scripts. A `%` shown in the UI is only a probability claim
   if calibration supports it; otherwise it is a policy score (see the
   `model_confidence` vs `risk_score` contract in
   [API Documentation](API_Documentation.md)).

## Reproducibility

- `trained_models/model_metadata.json` records model type, TF-IDF config,
  split strategy, CV statistics, test metrics, sklearn version, and dataset
  row counts for every release.
- `datasets/final/dataset_manifest.json` records provenance, class balance,
  dedup method (SHA-256 of normalized full text), conflicting-label counts,
  and source list.
- Artifact integrity: training prints SHA-256 of both `.pkl` files;
  `/ready` verifies their presence at serving time.

## Current numbers

Regenerating from the current pipeline — see
`trained_models/model_metadata.json` in a release for the authoritative
figures. Historical headline claims predating the Pipeline-CV fix are
retired; do not cite them.
