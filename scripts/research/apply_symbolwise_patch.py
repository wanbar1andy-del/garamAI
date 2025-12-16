# scripts/research/apply_symbolwise_patch.py
from __future__ import annotations
from pathlib import Path
import yaml

def make_symbolwise_patch(project_root: Path, symbol_map: dict) -> Path:
    """
    symbol_map = { 
        "005930": {"recommended": 10, ...}, 
        "000660": {"recommended": 5, ...}, 
        ... 
    }
    이 정보를 반영하는 '심볼별 MeanReversionStrategy 패치' 생성
    """

    patch_dir = project_root / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)

    code_lines = [
        "# AUTO-GENERATED SYMBOL-WISE PATCH",
        "from garam_core.strategy.catalog.mean_reversion import MeanReversionStrategy as _Base",
        "",
        "class MeanReversionStrategy(_Base):",
        "    NAME = 'mean_reversion'",
        "    def __init__(self, symbol=None, *args, **kwargs):",
        "        super().__init__(*args, **kwargs)",
        "        # symbolwise max_hold_bars patch",
        "        self.symbol_map = {"
    ]

    # 삽입
    for sym, rec in symbol_map.items():
        val = rec.get('recommended')
        if val is not None:
            code_lines.append(f"            '{sym}': {int(val)},")

    code_lines.append("        }")
    code_lines.append("        if symbol and symbol in self.symbol_map:")
    code_lines.append("            self.max_hold_bars = self.symbol_map[symbol]")
    code_lines.append("            # print(f'[PATCH] Applied max_hold_bars={self.max_hold_bars} for {symbol}')")
    code_lines.append("")

    patch_path = patch_dir / "mean_reversion_symbolwise_patch.py"
    patch_path.write_text("\n".join(code_lines), encoding="utf-8")
    return patch_path


def activate_symbolwise_patch(project_root: Path, patch_path: Path):
    # patches.pth 등록
    pth = project_root / "patches" / "patches.pth"
    pth.write_text(str(patch_path.parent.resolve()), encoding="utf-8")
