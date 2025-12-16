from dataclasses import dataclass, field
from typing import List, Dict
import pandas as pd

@dataclass
class FeatureFrameSpec:
    """
    Feature Specification for validation.
    """
    required_columns: List[str]
    dtypes: Dict[str, str] = field(default_factory=dict)
    
    def validate(self, df: pd.DataFrame) -> bool:
        missing = [c for c in self.required_columns if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        return True
