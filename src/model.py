import pulp
from typing import Dict, Optional, Any
from .data import ELEMENT_PRICES, DEFAULT_RATIOS, MAX_REFUEL_PERCENTAGE, ELEMENTS


class RefrigerantOptimizer:

    def __init__(self, operation: str, initial_composition: Optional[Dict[str, float]] = None, 
                 target_weight: Optional[float] = None):

        self.operation = operation
        self.initial_composition = initial_composition or {}
        self.target_weight = target_weight
        
        if operation not in ['refuel', 'new_blend']:
            raise ValueError("Operation must be either 'refuel' or 'new_blend'")
    
    def calculate_max_additions(self) -> Dict[str, float]:
        """
        Returns a dictionary mapping each element to its maximum addition amount (kg)
        """
        if not self.initial_composition:
            return {element: 0.0 for element in ELEMENTS}
        
        max_additions = {}
        for element in ELEMENTS:
            current_amount = self.initial_composition.get(element, 0)
            max_additions[element] = current_amount * MAX_REFUEL_PERCENTAGE
        
        return max_additions
    
    def optimize(self) -> Dict[str, Any]:
        """
        Will return a dictionary with the following keys:
            - status: ('Optimal', 'Infeasible', etc.)
            - total_cost: Total cost of solution
            - additions: Dict of element additions (for refuel)
            - extractions: Dict of element extractions (for new_blend)
            - final_composition: Final composition of the refrigerant
        """
        if self.operation == 'refuel':
            return self.optimize_refuel()
        elif self.operation == 'new_blend':
            return self.optimize_new_blend()
        else:
            raise ValueError(f"Unsupported operation: {self.operation}")
