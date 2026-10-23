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
- **Train/serve parity** — the classifier consumes the email **body text
  only**, at training *and* at serving (`ai-engine/inference/predict.py`).
  Sender and header evidence are handled by the bounded sender/auth/BEC
  analyzers in the decision engine, never concatenated into the vectorizer
  input. Consequence: the published metrics describe exactly the input the
  deployed classifier sees. If sender were appended at serving time only, the
  model would be scored on a distribution it was neither trained nor measured
  on, and the reported numbers would no longer apply.
- `datasets/final/dataset_manifest.json` records provenance, class balance,
  dedup method (SHA-256 of normalized full text), conflicting-label counts,
  and source list.
- Artifact integrity: training prints SHA-256 of both `.pkl` files;
  `/ready` verifies their presence at serving time.

## Current numbers

Release `phase4` (2026-10-14 retrain, 195,740 mails; train 156,592 / test
39,148; sklearn 1.9.0) — see `trained_models/model_metadata.json`:

| Metric | Value |
|---|---|
| CV F1-macro (5-fold, Pipeline) | 0.9814 ± 0.0006 |
| Test accuracy | 0.9825 |
| Phishing precision / recall / F1 | 0.9783 / 0.9838 / 0.9810 |
| False-positive / false-negative rate | 0.0185 / 0.0162 |
| Log loss / Brier score | 0.0857 / 0.0181 |
| Confusion [[TN, FP], [FN, TP]] | [[20786, 392], [292, 17678]] |

Policy verdicts at thresholds 75/45 on the same holdout (text-only,
`reports/policy_validation.json`): precision 0.9947, recall 0.9329, FPR
0.0042, FNR 0.0671. The policy is deliberately conservative — it catches
fewer phishes than the raw model (recall 93.3% vs 98.4%) in exchange for a
0.4% false-positive rate. Re-validate before moving thresholds; the holdout
must not be used for tuning.

Historical headline claims predating the Pipeline-CV fix are retired; do not
cite them. Source-separated (unseen-campaign) estimates require a dataset
build with the `source` column — run `source_split_eval.py` after
`build_final_dataset.py` and attach its report to the release.

## Adversarial and difficult negatives

`tests/fixtures/adversarial.jsonl` (12 cases) covers legitimate password
resets, invoices, security notices, newsletters, OTPs versus credential
lures, quiet BEC, punycode, shorteners, IP URLs, gift-card fraud, and
subdomain spoofing. Baseline: 7/7 phishing caught; 3/5 tricky-legitimate
mails over-flagged as Phishing. `test_adversarial.py` locks this as a
no-regression ceiling — the legitimate-mail false-positive gap is the top
detection-quality item, ahead of any new features.
