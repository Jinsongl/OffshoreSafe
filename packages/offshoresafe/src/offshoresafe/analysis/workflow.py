"""Traceable engineering analysis orchestration for OffshoreSafe projects."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

from offshoresafe.postprocessing import (
    SNCurve,
    calculate_del,
    calculate_fatigue_damage,
    compute_statistics,
    count_rainflow,
    extract_peaks,
    fit_extreme_distribution,
    return_period_response,
)
from offshoresafe.project import AnalysisConfiguration, OffshoreProject
from offshoresafe.solver import HEROWINDAdapter, OpenFASTAdapter, SolverAdapter
from offshoresafe.structural import (
    analyze_blade_fatigue_reliability,
    analyze_tower_reliability,
)

_RESULT_FIELDS = {
    "schema_version",
    "project_id",
    "analysis_id",
    "analysis_type",
    "method",
    "solver_id",
    "adapter",
    "software_version",
    "analyzed_at",
    "parameters",
    "traceability",
    "payload",
}


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class EngineeringAnalysisResult:
    """Immutable, JSON-serializable engineering result with provenance."""

    project_id: str
    analysis_id: str
    analysis_type: str
    method: str
    solver_id: str
    adapter: str
    software_version: str
    analyzed_at: str
    parameters: Mapping[str, Any]
    traceability: Mapping[str, Any]
    payload: Mapping[str, Any]
    schema_version: str = field(default="1.0")

    def __post_init__(self) -> None:
        for name in (
            "project_id",
            "analysis_id",
            "analysis_type",
            "method",
            "solver_id",
            "adapter",
            "software_version",
            "analyzed_at",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.schema_version != "1.0":
            raise ValueError(
                f"unsupported engineering result schema: {self.schema_version}"
            )
        try:
            parsed_time = datetime.fromisoformat(
                self.analyzed_at.replace("Z", "+00:00")
            )
        except ValueError as error:
            raise ValueError("analyzed_at must be an ISO 8601 timestamp") from error
        if parsed_time.tzinfo is None or parsed_time.utcoffset() is None:
            raise ValueError("analyzed_at must include a timezone")
        for name in ("parameters", "traceability", "payload"):
            if not isinstance(getattr(self, name), Mapping):
                raise TypeError(f"{name} must be a mapping")
        object.__setattr__(self, "parameters", _freeze(self.parameters))
        object.__setattr__(self, "traceability", _freeze(self.traceability))
        object.__setattr__(self, "payload", _freeze(self.payload))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation in schema order."""

        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "analysis_id": self.analysis_id,
            "analysis_type": self.analysis_type,
            "method": self.method,
            "solver_id": self.solver_id,
            "adapter": self.adapter,
            "software_version": self.software_version,
            "analyzed_at": self.analyzed_at,
            "parameters": _thaw(self.parameters),
            "traceability": _thaw(self.traceability),
            "payload": _thaw(self.payload),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EngineeringAnalysisResult:
        """Validate and restore an exported result mapping."""

        unknown = set(data) - _RESULT_FIELDS
        missing = _RESULT_FIELDS - set(data)
        if unknown:
            raise ValueError(
                f"unknown engineering result fields: {', '.join(sorted(unknown))}"
            )
        if missing:
            raise ValueError(
                f"missing engineering result fields: {', '.join(sorted(missing))}"
            )
        return cls(**dict(data))

    @classmethod
    def load(cls, path: str | Path) -> EngineeringAnalysisResult:
        """Load one exported engineering result from JSON."""

        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"engineering result does not exist: {source}")
        data = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(data, Mapping):
            raise ValueError("engineering result JSON root must be an object")
        return cls.from_dict(data)


class EngineeringAnalysisWorkflow:
    """Run configured engineering analyses over normalized solver results."""

    def __init__(
        self,
        project: OffshoreProject,
        *,
        adapters: Mapping[str, SolverAdapter] | None = None,
    ) -> None:
        if not isinstance(project, OffshoreProject):
            raise TypeError("project must be an OffshoreProject")
        configured = (
            {"openfast": OpenFASTAdapter(), "herowind": HEROWINDAdapter()}
            if adapters is None
            else dict(adapters)
        )
        normalized: dict[str, SolverAdapter] = {}
        for name, adapter in configured.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("adapter registry names must be non-empty strings")
            if not isinstance(adapter, SolverAdapter):
                raise TypeError("adapter registry values must implement SolverAdapter")
            normalized[name.casefold()] = adapter
        self.project = project
        self.adapters = MappingProxyType(normalized)

    def _analysis(self, analysis_id: str) -> AnalysisConfiguration:
        matches = [
            analysis
            for analysis in self.project.analyses
            if analysis.analysis_id == analysis_id
        ]
        if not matches:
            raise KeyError(f"unknown project analysis: {analysis_id}")
        return matches[0]

    def _adapter(self) -> SolverAdapter:
        name = self.project.solver.adapter.casefold()
        try:
            return self.adapters[name]
        except KeyError as error:
            available = ", ".join(sorted(self.adapters)) or "none"
            raise ValueError(
                f"unsupported solver adapter {self.project.solver.adapter!r}; "
                f"available adapters: {available}"
            ) from error

    @staticmethod
    def _settings(analysis: AnalysisConfiguration, allowed: set[str]) -> dict[str, Any]:
        settings = dict(analysis.settings)
        unknown = settings.keys() - allowed
        if unknown:
            raise ValueError(
                f"unsupported {analysis.analysis_type} settings: "
                f"{', '.join(sorted(unknown))}"
            )
        return settings

    @staticmethod
    def _statistics_payload(result: Any) -> dict[str, Any]:
        return {
            "channels": {
                name: asdict(statistics) for name, statistics in result.channels.items()
            }
        }

    def _run_postprocessing(
        self, analysis: AnalysisConfiguration, solver_result: Any
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        analysis_type = analysis.analysis_type.casefold().replace("-", "_")
        if analysis_type == "statistics":
            settings = self._settings(analysis, {"channels", "ddof"})
            result = compute_statistics(solver_result, **settings)
            return self._statistics_payload(result), settings

        if analysis_type in {"extreme", "extreme_response"}:
            settings = self._settings(
                analysis,
                {
                    "channel",
                    "direction",
                    "threshold",
                    "min_distance",
                    "distribution",
                    "return_period",
                    "events_per_period",
                },
            )
            if "channel" not in settings or "return_period" not in settings:
                raise ValueError("extreme analysis requires channel and return_period")
            peak_keys = {"direction", "threshold", "min_distance"}
            peak_options = {key: settings[key] for key in peak_keys if key in settings}
            peaks = extract_peaks(
                solver_result, str(settings["channel"]), **peak_options
            )
            fitted = fit_extreme_distribution(
                peaks, distribution=settings.get("distribution", "gumbel")
            )
            response = return_period_response(
                fitted,
                float(settings["return_period"]),
                events_per_period=float(settings.get("events_per_period", 1.0)),
            )
            return (
                {
                    "channel": peaks.channel,
                    "unit": peaks.unit,
                    "peaks": [asdict(peak) for peak in peaks.peaks],
                    "distribution": fitted.distribution,
                    "distribution_parameters": dict(fitted.parameters),
                    "sample_count": fitted.sample_count,
                    "return_period_response": response,
                },
                settings,
            )

        if analysis_type == "fatigue":
            settings = self._settings(
                analysis,
                {
                    "channel",
                    "slope",
                    "log10_intercept",
                    "endurance_limit",
                    "equivalent_cycles",
                },
            )
            required = {"channel", "slope", "log10_intercept", "equivalent_cycles"}
            missing = required - settings.keys()
            if missing:
                raise ValueError(
                    f"fatigue analysis missing settings: {', '.join(sorted(missing))}"
                )
            channel = str(settings["channel"])
            try:
                values = solver_result.channels[channel]
            except KeyError as error:
                raise KeyError(f"unknown solver channel: {channel}") from error
            cycles = count_rainflow(values)
            curve = SNCurve(
                slope=float(settings["slope"]),
                log10_intercept=float(settings["log10_intercept"]),
                endurance_limit=(
                    float(settings["endurance_limit"])
                    if settings.get("endurance_limit") is not None
                    else None
                ),
            )
            damage = calculate_fatigue_damage(cycles, curve)
            equivalent_load = calculate_del(
                cycles,
                slope=curve.slope,
                equivalent_cycles=float(settings["equivalent_cycles"]),
            )
            return (
                {
                    "channel": channel,
                    "unit": solver_result.units.get(channel),
                    "cycles": [asdict(cycle) for cycle in cycles.cycles],
                    "damage": damage.damage,
                    "damage_contributions": list(damage.contributions),
                    "damage_equivalent_load": equivalent_load,
                },
                settings,
            )

        if analysis_type == "tower_reliability":
            return analyze_tower_reliability(
                solver_result,
                analysis.settings,
                method=analysis.method,
                backend=analysis.backend,
            )

        if analysis_type == "blade_fatigue_reliability":
            return analyze_blade_fatigue_reliability(
                solver_result,
                analysis.settings,
                method=analysis.method,
                backend=analysis.backend,
            )

        raise ValueError(
            f"unsupported engineering analysis_type: {analysis.analysis_type!r}"
        )

    def run(
        self,
        analysis_id: str,
        *,
        output_file: str | Path | None = None,
        analyzed_at: datetime | None = None,
    ) -> EngineeringAnalysisResult:
        """Execute one configured analysis over a solver output file."""

        analysis = self._analysis(analysis_id)
        adapter = self._adapter()
        source = output_file or self.project.solver.output_file
        if source is None:
            raise ValueError(
                "solver output_file is required in the project or workflow run call"
            )
        input_metadata = adapter.read_input(self.project.solver.input_file)
        solver_result = adapter.read_output(source)
        payload, parameters = self._run_postprocessing(analysis, solver_result)
        timestamp = analyzed_at or datetime.now(UTC)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("analyzed_at must be timezone-aware")
        from offshoresafe import __version__

        return EngineeringAnalysisResult(
            project_id=self.project.project.project_id,
            analysis_id=analysis.analysis_id,
            analysis_type=analysis.analysis_type,
            method=analysis.method,
            solver_id=self.project.solver.solver_id,
            adapter=adapter.name,
            software_version=__version__,
            analyzed_at=timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            parameters=parameters,
            traceability={
                "project_source_file": (
                    str(self.project.source_file) if self.project.source_file else None
                ),
                "solver_input": dict(input_metadata),
                "solver_output": dict(solver_result.metadata),
            },
            payload=payload,
        )

    @staticmethod
    def export_result(result: EngineeringAnalysisResult, path: str | Path) -> Path:
        """Write one engineering result using deterministic JSON formatting."""

        if not isinstance(result, EngineeringAnalysisResult):
            raise TypeError("result must be an EngineeringAnalysisResult")
        target = Path(path).expanduser().resolve()
        if target.suffix.lower() != ".json":
            raise ValueError("engineering result exports must use a .json path")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(
                result.to_dict(),
                stream,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            stream.write("\n")
        return target


__all__ = ["EngineeringAnalysisResult", "EngineeringAnalysisWorkflow"]
