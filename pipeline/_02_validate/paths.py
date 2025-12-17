from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from garam_core.health.gate import gate_environment


@dataclass(frozen=True)
class ValidatePaths:
    project_root_computed: Path
    data_root_computed: Path
    logs_root_computed: Path
    minute_dir: Path
    validated_minute_dir: Path
    recollect_targets: Path


def get_validate_paths(project_root: Path | None = None) -> ValidatePaths:
    project_root = project_root or Path.cwd()
    env = gate_environment(project_root)

    data_root = env.data_root
    logs_root = env.logs_root

    minute_dir = data_root / "history" / "minute"
    validated_minute_dir = data_root / "validated" / "minute"
    validated_minute_dir.mkdir(parents=True, exist_ok=True)

    recollect_targets = project_root / "recollect_targets.txt"

    return ValidatePaths(
        project_root_computed=project_root,
        data_root_computed=data_root,
        logs_root_computed=logs_root,
        minute_dir=minute_dir,
        validated_minute_dir=validated_minute_dir,
        recollect_targets=recollect_targets,
    )
