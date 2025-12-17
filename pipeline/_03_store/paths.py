from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from garam_core.health.gate import gate_environment

@dataclass(frozen=True)
class StorePaths:
    project_root_computed: Path
    data_root: Path
    validated_minute_dir: Path

def get_store_paths(project_root: Path | None = None) -> StorePaths:
    project_root = project_root or Path.cwd()
    paths = gate_environment(project_root)  # Gate0: paths.yaml
    data_root = paths.data_root

    validated_minute_dir = data_root / "validated" / "minute"
    # STORE는 "읽기"가 주역이지만, 디렉토리 미존재로 실패하는 운영사고를 막기 위해 mkdir은 허용
    validated_minute_dir.mkdir(parents=True, exist_ok=True)

    return StorePaths(
        project_root_computed=project_root,
        data_root=data_root,
        validated_minute_dir=validated_minute_dir,
    )
