# garam_core/strategy/registry.py
import pkgutil
import warnings
import inspect
import importlib
from typing import List, Type
from pathlib import Path

from garam_core.strategy.base import BaseStrategy

def discover_strategies(package_name: str = "garam_core.strategy.catalog") -> List[Type[BaseStrategy]]:
    """
    Dynamically discovers all BaseStrategy implementations in the given package.
    """
    strategies = []
    
    # Resolve package path
    spec = importlib.util.find_spec(package_name)
    if not spec:
        warnings.warn(f"Strategy catalog package '{package_name}' not found.")
        return []
    
    path = spec.submodule_search_locations[0]
    
    for loader, module_name, is_pkg in pkgutil.iter_modules([path]):
        full_name = f"{package_name}.{module_name}"
        try:
            module = importlib.import_module(full_name)
            
            # Inspect module for BaseStrategy subclasses
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) 
                    and issubclass(obj, BaseStrategy) 
                    and obj is not BaseStrategy):
                    strategies.append(obj)
                    
        except ImportError as e:
            warnings.warn(f"Failed to import strategy module {full_name}: {e}")
            
    return strategies
