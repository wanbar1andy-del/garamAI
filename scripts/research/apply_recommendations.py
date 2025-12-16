# scripts/research/apply_recommendations.py
from __future__ import annotations
from pathlib import Path
import shutil
import yaml

def make_meanrev_patch(project_root: Path, recommended_hold: int) -> Path:
    """
    MeanReversionStrategy의 기본 max_hold_bars를 덮어쓰는
    '패치 클래스'를 생성한다. (원본 보존)
    """
    patch_dir = project_root / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)

    patch_path = patch_dir / "mean_reversion_patch.py"
    code = f'''
# AUTO-GENERATED PATCH
# Applies recommended max_hold_bars safely without touching original source.

from garam_core.strategy.catalog.mean_reversion import MeanReversionStrategy as _Base

class MeanReversionStrategy(_Base):
    NAME = "mean_reversion"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_hold_bars = {int(recommended_hold)}
'''
    patch_path.write_text(code.strip() + "\\n", encoding="utf-8")
    return patch_path


def activate_patch(project_root: Path, patch_path: Path):
    """
    registry가 patch를 우선 로드하도록 .pth 방식으로 sys.path 선두에 추가
    """
    pth = project_root / "patches" / "patches.pth"
    pth.write_text(str(patch_path.parent.resolve()), encoding="utf-8")
