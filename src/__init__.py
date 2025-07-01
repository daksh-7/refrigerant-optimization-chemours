"""
Top-level package for the Refrigerant Optimisation Toolkit. 
This makes the main optimiser class directly importable via from src import RefrigerantOptimizer
"""

from .model import RefrigerantOptimizer

__all__: list[str] = ["RefrigerantOptimizer"]
