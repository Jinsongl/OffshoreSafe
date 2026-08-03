"""Engineering post-processing operations."""

from offshoresafe.postprocessing.extreme import (
    ExtremeValueFit,
    Peak,
    PeakResult,
    extract_peaks,
    fit_extreme_distribution,
    return_period_response,
)
from offshoresafe.postprocessing.fatigue import (
    FatigueDamageResult,
    RainflowCycle,
    RainflowResult,
    SNCurve,
    calculate_del,
    calculate_fatigue_damage,
    count_rainflow,
)
from offshoresafe.postprocessing.statistics import (
    ChannelStatistics,
    StatisticsResult,
    compute_statistics,
)

__all__ = [
    "ChannelStatistics",
    "ExtremeValueFit",
    "FatigueDamageResult",
    "Peak",
    "PeakResult",
    "RainflowCycle",
    "RainflowResult",
    "SNCurve",
    "StatisticsResult",
    "calculate_del",
    "calculate_fatigue_damage",
    "compute_statistics",
    "count_rainflow",
    "extract_peaks",
    "fit_extreme_distribution",
    "return_period_response",
]
