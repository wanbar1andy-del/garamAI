from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml
import pandas as pd

# Fix import path to be relative or absolute based on execution context
# Assuming this runs as a module: from garam_core.schema...
# But for now, let's keep it relative for portability within the package
from ..schema.market_schema import validate_market_df, MarketSchemaSpec, SchemaError


class GateError(RuntimeError):
    """Raised when any startup gate fails."""


def _gate_fail(msg: str) -> None:
    raise GateError(msg)


@dataclass(frozen=True)
class PathsConfig:
    # core는 절대경로 금지. paths.yaml은 '상대경로'만 정의.
    project_root: Path
    data_root: Path
    logs_root: Path

    @staticmethod
    def from_yaml(project_root: Path, yaml_path: Path) -> "PathsConfig":
        if not yaml_path.exists():
            _gate_fail(f"Gate0: paths.yaml not found: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        def rel(p: str) -> Path:
            if not p:
                _gate_fail("Gate0: empty path entry in paths.yaml")
            pp = Path(p)
            # SSOT v2: Block absolute/drive/UNC paths
            if pp.is_absolute() or pp.drive or str(pp).startswith(("\\\\", "//")):
                _gate_fail(f"Gate0: absolute/drive/UNC path is forbidden in core: {p}")
            # COMPUTED = project_root / relative (no resolve)
            return project_root / pp

        data_root = rel(raw.get("data_root", ""))
        logs_root = rel(raw.get("logs_root", ""))

        # SSOT Policy v2: Relative paths only (enforced above)
        # Drive letters (C:, G:) may appear in resolved() due to GDrive sync
        # but are NOT blocked - that's an environment implementation detail

        # 디렉토리 존재성은 core에서 '강제 생성'하지 않습니다(무상태 원칙).
        # 존재하지 않으면 실패시키는 것이 맞습니다.
        if not data_root.exists():
            _gate_fail(f"Gate0: data_root does not exist: {data_root}")
        if not logs_root.exists():
            # logs는 없으면 생성을 허용할 수도 있지만, 여기서는 strict로 유지
            _gate_fail(f"Gate0: logs_root does not exist: {logs_root}")

        # SSOT v2: COMPUTED paths only (no resolve in return)
        return PathsConfig(project_root=project_root, data_root=data_root, logs_root=logs_root)


@dataclass(frozen=True)
class GateSpec:
    timezone: str = "UTC"             # core 기준
    allow_na: bool = False
    allow_duplicate_index: bool = False


def gate_environment(project_root: Path) -> PathsConfig:
    """Gate0: Environment/Paths"""
    yaml_path = project_root / "config" / "paths.yaml"
    return PathsConfig.from_yaml(project_root=project_root, yaml_path=yaml_path)


def gate_schema(df: pd.DataFrame, spec: GateSpec) -> pd.DataFrame:
    """Gate1: Data Schema"""
    try:
        return validate_market_df(
            df,
            MarketSchemaSpec(
                timezone=spec.timezone,
                allow_na=spec.allow_na,
                allow_duplicate_index=spec.allow_duplicate_index,
            ),
        )
    except SchemaError as e:
        _gate_fail(f"Gate1: schema failed: {e}")


def gate_determinism(fn, *args, **kwargs):
    """
    Gate2: Determinism (same input -> same output).
    NOTE: core 로직 함수(fn)는 순수해야 하므로, 2회 호출 결과가 동일해야 함.
    """
    out1 = fn(*args, **kwargs)
    out2 = fn(*args, **kwargs)
    # Simple equality check constraints: DataFrame equality might need specific handling, 
    # but for basic contract phase, this checks exact object equality or value equality relying on __eq__
    # For DataFrames, direct == is ambiguous, should use .equals()
    if isinstance(out1, pd.DataFrame) or isinstance(out1, pd.Series):
         if not out1.equals(out2):
             _gate_fail("Gate2: determinism failed: output differs between identical runs (Top/Bottom mismatch).")
    elif out1 != out2:
        _gate_fail("Gate2: determinism failed: output differs between identical runs.")
    return out1


def gate_strategy_sanity(result: dict, max_multiplier: float = 2.5) -> None:
    """Gate3: Strategy sanity"""
    if result is None:
        _gate_fail("Gate3: result is None.")

    # 최소 규약 예시 (Turbo/Signal 결과에 공통 적용 가능)
    if "multiplier" in result:
        m = result["multiplier"]
        if not isinstance(m, (int, float)):
            _gate_fail("Gate3: multiplier is not numeric.")
        if m <= 0 or m > max_multiplier:
            _gate_fail(f"Gate3: multiplier out of bounds: {m} (max {max_multiplier})")

    # NaN 방지
    for k, v in result.items():
        if isinstance(v, float) and (v != v):  # NaN check
            _gate_fail(f"Gate3: NaN detected in result field: {k}")
