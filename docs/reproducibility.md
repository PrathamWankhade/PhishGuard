# Reproducibility

Model artifacts (`trained_models/*.pkl`), the built dataset
(`datasets/final/*.csv`), and raw sources (`datasets/raw/`) are gitignored:
they are large, partly licensed, and regenerated — not source code. A clean
clone therefore cannot serve predictions until artifacts exist. This is
expected; what matters is that producing them is deterministic.

## The reproducible path

```
datasets/raw/*  (documented sources, see README dataset table)
  ->  python ai-engine/training/build_final_dataset.py
      datasets/final/final_emails.csv + dataset_manifest.json
  ->  python ai-engine/training/train_model.py
      trained_models/{phishing_model.pkl, tfidf_vectorizer.pkl, model_metadata.json}
  ->  python ai-engine/training/source_split_eval.py
      reports/source_split_eval.json
  ->  curl localhost:8000/ready   # 200 with model_classes
```

- `build_final_dataset.py` — full-text SHA-256 dedup, conflicting-label
  counts, `source` provenance column retained for source-separated eval.
- `train_model.py` — Pipeline-correct CV, holdout metrics, calibration
  scores, `model_metadata.json` (config, split, sklearn version), artifact
  SHA-256 printed for release notes.
- Every release should publish `model_metadata.json` + the eval report next
  to the artifact version so metrics are checkable without retraining.

## Verifying a checkout

```
python scripts/verify_setup.py
```

Checks deps, dataset, artifacts (including actual load), and metadata, and
prints the exact producing command for anything missing. Exit 0 means
inference can run. Wire it into onboarding docs and deployment preflight —
it is the executable version of this guide.

## What is intentionally NOT in git

- Raw email corpora (license/size) — acquisition per source docs.
- Built CSVs and `.pkl` binaries — regenerated via the path above.
- `model_metadata.json` / reports — force-add (`git add -f`) the release
  copies so each tagged version carries its own metrics.

## Known gap

There is no hosted versioned-artifact download yet. Until one exists, the
supported routes are local retrain (above) or mounting a released artifact
directory into `trained_models/` (see `docker-compose.yml`). Contributors:
do not commit binaries to the main history; attach them to GitHub Releases.
