"""Limit-state function abstraction."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

import numpy as np
from numpy.typing import ArrayLike, NDArray


class Model(Protocol):
    """Structural interface implemented by external deterministic models."""

    def evaluate(self, x: ArrayLike) -> Any:
        """Evaluate model outputs for one point or a sample matrix."""
        ...


class LimitStateFunction:
    """Wrap an analytical function or external model using ``g(X)`` semantics.

    Positive values are safe and values less than or equal to zero are failure.
    External models must expose an ``evaluate(X)`` method.
    """

    def __init__(
        self, function: Callable[[Any], Any] | Any, *, name: str | None = None
    ):
        if callable(function):
            self._evaluate = function
        elif callable(getattr(function, "evaluate", None)):
            self._evaluate = function.evaluate
        else:
            raise TypeError("function must be callable or expose evaluate(X)")
        self.name = name or getattr(function, "__name__", function.__class__.__name__)

    def evaluate(self, x: ArrayLike) -> float | NDArray[np.float64]:
        """Evaluate the signed safety margin at one point or a sample matrix."""
        values = np.asarray(x, dtype=float)
        result = np.asarray(self._evaluate(values), dtype=float)
        if result.ndim == 0:
            return float(result)
        return result

    def evaluate_samples(self, samples: ArrayLike) -> NDArray[np.float64]:
        """Evaluate rows, falling back to scalar calls for non-vectorized models."""
        values = np.asarray(samples, dtype=float)
        if values.ndim != 2:
            raise ValueError("samples must have shape (n_samples, dimension)")
        try:
            result = np.asarray(self._evaluate(values), dtype=float).reshape(-1)
            if result.size == values.shape[0]:
                return result
        except (TypeError, ValueError, IndexError):
            pass
        return np.asarray([self._evaluate(row) for row in values], dtype=float).reshape(
            -1
        )

    __call__ = evaluate


__all__ = ["LimitStateFunction", "Model"]
