# Workflow

## 1. Scan pasted text (primary flow)

```
Scanner page → POST /api/v1/predict { email_text, sender, ... }
  → sanitize + validate → detect_phishing()
  → deterministic signals (+ optional AI summary)
  → upsert scan_history by email_hash
  → PredictionCard: verdict badge, model vs risk scores, evidence list
```

- Empty text → `422` with a field-level message (no fake result).
- Backend down / non-2xx → the scanner shows an explicit unavailable error
  and clears any previous result. No silent heuristic substitution.
- Rescanning identical content bumps `scan_count` instead of duplicating rows.

## 2. Scan an uploaded file (forensic flow)

```
UploadEmail → POST /api/v1/upload (multipart file)
  → type check (.eml/.txt) → 2MB cap → parse_raw_email()
  → { sender, subject, reply_to, return_path, body, urls, attachments, errors }
  → sender/body pre-fill the scanner; reply_to/return_path flow into the
    scan as header evidence (also editable under Advanced headers)
  → user presses Scan → flow 1
```

- If the backend parser is unreachable, the component falls back to raw-text
  handling **with a visible warning** that accuracy may be reduced.
- Malformed MIME never crashes parsing: partial results + `errors[]`.

## 3. Review analytics

```
Dashboard page → GET /api/v1/dashboard + GET /api/v1/history (X-API-Key)
  → stat cards (unique emails vs scan events kept distinct)
  → threat-distribution + risk-level charts → filterable history table
```

- If the API is unreachable, the dashboard renders clearly badged **Demo
  Mode** numbers. Demo data is never written to the database or mixed into
  live KPIs.

## 4. Analyst feedback

```
Analyst disputes a verdict → POST /api/v1/feedback { email_hash, verdict_correct: false, ... }
  → stored in scan_feedback → GET /api/v1/feedback/stats monitors error rate
```

Feedback is kept out of the training path until a human review step promotes
it. It measures the system; it does not silently retrain it.

## 5. Retrain and release a model (offline)

```
datasets/raw/* → build_final_dataset.py → datasets/final/final_emails.csv (+ manifest)
  → train_model.py → trained_models/{phishing_model.pkl, tfidf_vectorizer.pkl, model_metadata.json}
  → evaluate_model.py / source_split_eval.py → reports
  → mount artifacts into backend → /ready flips to 200 → serve
```

- Rebuilds preserve the `source` column so source-separated evaluation can
  hold out entire campaigns (the realistic generalization test).
- Every release carries `model_metadata.json` (config, split, CV scores,
  test metrics, sklearn version) — see
  [Model Evaluation](model_evaluation.md).
- Never compare headline accuracy across projects without reproducing each
  evaluation protocol; the datasets and splits differ.
