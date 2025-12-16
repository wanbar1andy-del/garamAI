# core/contracts/__init__.py
from .universe import UniverseRow
from .market import MarketSchema
from .features import FeatureFrameSpec
from .signals import SignalRecord
from .hero import HeroMetadata
from .allocation import AllocationRow

__all__ = [
    "UniverseRow",
    "MarketSchema",
    "FeatureFrameSpec",
    "SignalRecord",
    "HeroMetadata",
    "AllocationRow"
]
