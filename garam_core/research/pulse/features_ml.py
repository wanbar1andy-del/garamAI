# garam_core/research/pulse/features_ml.py
import pandas as pd

def make_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs feature matrix for ML model.
    """
    # Ensure required cols exist
    for col in ["return1", "vol20", "vol5", "vol_pressure"]:
        if col not in df.columns:
            # Fallback if Enhance not called? Should not happen in pipeline.
            raise ValueError(f"Missing column {col} in dataframe")
            
    features = pd.DataFrame({
        "return1": df["return1"],
        "vol20": df["vol20"],
        "vol5": df["vol5"],
        "vol_pressure": df["vol_pressure"],
        "fear_score": df.get("fear_score", 0), # Optional
    }, index=df.index)
    
    features = features.fillna(0)
    return features
