# scripts/research/apply_surface_patch.py
from __future__ import annotations
from pathlib import Path
import yaml

def make_surface_patch(project_root: Path, symbol_param_map: dict) -> Path:
    """
    symbol_param_map:
      {
        "005930": {"recommended": {"ev_mult":1.2, "vol_mult":1.3}, ...},
        ...
      }
    """
    patch_dir = project_root / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# AUTO-GENERATED SURFACE PATCH",
        "from garam_core.strategy.catalog.regime_switch import RegimeSwitchStrategy as _Base",
        "",
        "class RegimeSwitchStrategy(_Base):",
        "    NAME = 'regime_switch'",
        "    def __init__(self, symbol=None, *args, **kwargs):",
        "        super().__init__(*args, **kwargs)",
        "        self.symbol_map = {"
    ]
    for sym, rec in symbol_param_map.items():
        r = rec.get("recommended") or {}
        ev = r.get("ev_mult")
        vol = r.get("vol_mult")
        if ev is None or vol is None:
            continue
        lines.append(f"            '{sym}': {{'ev_mult': {ev}, 'vol_mult': {vol}}},")
    
    lines.append("        }")
    lines.append("        if symbol and symbol in self.symbol_map:")
    lines.append("            params = self.symbol_map[symbol]")
    lines.append("            # print(f'[PATCH] Applied {{params}} for {symbol}')")
    lines.append("            self.ev_mult = params['ev_mult']")
    lines.append("            self.vol_mult = params['vol_mult']")
    lines.append("")

    patch_path = patch_dir / "regime_switch_surface_patch.py"
    patch_path.write_text("\n".join(lines), encoding="utf-8")
    return patch_path


def activate_surface_patch(project_root: Path, patch_path: Path):
    pth = project_root / "patches" / "patches.pth"
    pth.write_text(str(patch_path.parent.resolve()), encoding="utf-8")
