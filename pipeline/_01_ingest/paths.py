from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from garam_core.health.gate import gate_environment


@dataclass(frozen=True)
class IngestPaths:
    project_root_computed: Path
    data_root_computed: Path
    logs_root_computed: Path
    minute_dir: Path


def get_ingest_paths(project_root: Path | None = None) -> IngestPaths:
    """
    SSOT v2 준수:
    - project_root는 CWD 기반(COMPUTED)
    - gate는 paths.yaml 상대경로만 허용
    - resolve() 결과는 로깅용으로만 취급
    """
    project_root = project_root or Path.cwd()

    paths = gate_environment(project_root)  # Gate0 (paths.yaml)
    data_root = paths.data_root
    logs_root = paths.logs_root

    # 파이프라인(운영 계층)에서는 하위 디렉토리 생성 허용
    minute_dir = data_root / "history" / "minute"
    minute_dir.mkdir(parents=True, exist_ok=True)

    return IngestPaths(
        project_root_computed=project_root,
        data_root_computed=data_root,
        logs_root_computed=logs_root,
        minute_dir=minute_dir,
    )
