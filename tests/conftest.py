"""Shared pytest configuration.

Marker `model`: tests requiring serialized artifacts in `trained_models/`
(which are gitignored). CI runs `pytest -m "not model"` on fresh checkouts;
the full suite runs wherever artifacts exist (see README / RETRAIN notes).
"""
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "model: requires trained_models artifacts (skipped in CI)"
    )
