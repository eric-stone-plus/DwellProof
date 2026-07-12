"""Shared numerical helpers for the legacy analysis scripts."""

from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np


def best_lag_correlation(
    reference: Iterable[float],
    target: Iterable[float],
    max_lag: int = 6,
) -> Tuple[int, float]:
    """Return the lag with the largest finite absolute correlation.

    A correlation of ``-1`` is a valid result, so it cannot be used as the
    initial sentinel.  The previous scripts did that and consequently never
    updated their result.
    """
    reference_values = np.asarray(list(reference), dtype=float)
    target_values = np.asarray(list(target), dtype=float)
    if reference_values.shape != target_values.shape:
        raise ValueError("reference and target must have the same length")

    best_lag = 0
    best_corr = None
    for lag in range(-max_lag, max_lag + 1):
        if lag > 0:
            left = reference_values[lag:]
            right = target_values[:-lag]
        elif lag < 0:
            left = reference_values[:lag]
            right = target_values[-lag:]
        else:
            left = reference_values
            right = target_values

        valid = np.isfinite(left) & np.isfinite(right)
        if valid.sum() < 3:
            continue
        corr = float(np.corrcoef(left[valid], right[valid])[0, 1])
        if not np.isfinite(corr):
            continue
        if best_corr is None or abs(corr) > abs(best_corr):
            best_lag = lag
            best_corr = corr

    if best_corr is None:
        return 0, float("nan")
    return best_lag, best_corr
