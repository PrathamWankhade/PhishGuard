# Validation / Test Data

Holdout test sets for model evaluation. Created from `datasets/final/final_emails.csv` via a stratified 80/20 train-test split, preserving the class distribution from the full dataset.

## Files

| File | Rows | Description |
|---|---|---|
| `test_data.csv` | 39,148 | 21,178 legitimate + 17,970 phishing emails (holdout set) |

## Usage

Used by `train_model.py` for evaluation after training and by `test_model_accuracy.py` for benchmarking.

The 20% holdout is stratified — meaning the ratio of phishing to legitimate emails in the test set matches the full dataset (54% legit / 46% phishing).

## Regeneration

There is no `--split` flag on `build_final_dataset.py` (and never was). The
holdout is produced by `ai-engine/training/train_model.py`, which splits the
dataset inline:

```python
train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
```

Because the split is seeded, re-running it on the same `final_emails.csv`
reproduces this file exactly. Two consequences worth knowing:

- Rebuild `final_emails.csv` and the split moves, so this file (and any
  metrics reported against it) becomes stale until train_model.py is re-run.
  The dataset and `trained_models/` are a matched pair.
- This file has only `email_text,label` — no `source` column — so it cannot
  support unseen-campaign evaluation. Use
  `ai-engine/training/source_split_eval.py`, which splits by source instead.
