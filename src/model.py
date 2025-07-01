import pulp
from src.data import ELEMENT_PRICES, DEFAULT_RATIOS, MAX_REFUEL_PERCENTAGE, ELEMENTS
from typing import Optional, Dict

BIG_M = 1e5  # sufficiently large constant for Big-M formulations
EPSILON = 1e-6  # tiny positive number for linking binary/select variables

class RefrigerantOptimizer:
    _OPERATIONS = {"refuel", "new_blend", "optimise_mixture", "auto"}

    def __init__(
        self,
        operation: str,
        *,
        initial_composition: Optional[Dict[str, float]] = None,
        target_weight: Optional[float] = None,
    ) -> None:
        op = operation.lower()
        if op not in self._OPERATIONS:
            raise ValueError(f"Unknown operation '{operation}'.")

        self.operation: str = "optimise_mixture" if op == "auto" else op
        self.initial_composition: Dict[str, float] = initial_composition or {}
        self.target_weight: Optional[float] = target_weight

        # basic validations
        # For the combined optimisation we NEED to know (explicitly) what is in the
        # vessel right now.  Passing None means "I don't know".  Passing an
        # explicit empty dict {} allowed and means the vessel is empty.
        if self.operation == "optimise_mixture" and initial_composition is None:
            raise ValueError(
                "initial_composition is required for optimise_mixture – use {} if empty."
            )

        if self.operation == "new_blend" and (self.target_weight is None):
            raise ValueError("target_weight must be supplied for a new blend.")

        if self.operation == "refuel" and self.target_weight is not None:
            current_mass = self._current_mass(self.initial_composition)
            max_possible = current_mass * (1 + MAX_REFUEL_PERCENTAGE)
            if self.target_weight > max_possible + 1e-6:
                raise ValueError(
                    "target_weight violates the 15 % refuel cap – try optimise_mixture instead."
                )

    @staticmethod
    def _current_mass(mix: Dict[str, float]) -> float:
        return sum(mix.get(e, 0.0) for e in ELEMENTS)

    @staticmethod
    def _enforce_ratios(model: pulp.LpProblem, qty, used):
        """Enforce DEFAULT_RATIOS inside the selected subset (used==1)."""
        for i, ei in enumerate(ELEMENTS[:-1]):
            for ej in ELEMENTS[i + 1 :]:
                ri, rj = DEFAULT_RATIOS[ei], DEFAULT_RATIOS[ej]
                diff = qty[ei] * rj - qty[ej] * ri
                model += diff <= BIG_M * (2 - used[ei] - used[ej])
                model += -diff <= BIG_M * (2 - used[ei] - used[ej])

    def refuel(self, initial_mix: Dict[str, float], target_weight: Optional[float] = None):
        """Optimise a refuel operation under the required constraints."""
        current = {e: initial_mix.get(e, 0.0) for e in ELEMENTS}
        current_mass = self._current_mass(current)

        if current_mass == 0:
            empty = {e: 0.0 for e in ELEMENTS}
            return {
                "status": "Nothing to refuel",
                "total_cost": 0.0,
                "additions": empty,
                "final_composition": empty,
            }

        add = {e: pulp.LpVariable(f"add_{e}", lowBound=0) for e in ELEMENTS}
        model = pulp.LpProblem("refuel", pulp.LpMinimize)

        # objective – minimise addition cost
        model += pulp.lpSum(ELEMENT_PRICES[e]["addition"] * add[e] for e in ELEMENTS)

        # 15 % cap per element
        for e in ELEMENTS:
            model += add[e] <= current[e] * MAX_REFUEL_PERCENTAGE

        # keep the overall 4:3:2:1 ratio in the *final* mixture
        scale = pulp.LpVariable("scale", lowBound=0)

        for e in ELEMENTS:
            model += current[e] + add[e] == DEFAULT_RATIOS[e] * scale

        # optional exact-weight requirement
        if target_weight is not None:
            if target_weight < current_mass - 1e-6:
                raise ValueError("target_weight below current weight – extraction required.")
            model += pulp.lpSum(add.values()) == target_weight - current_mass

        model.solve(pulp.PULP_CBC_CMD(msg=False))
        status = pulp.LpStatus[model.status]
        if status != "Optimal":
            return {"status": status}

        additions = {e: float(add[e].value() or 0.0) for e in ELEMENTS}
        final = {e: current[e] + additions[e] for e in ELEMENTS}
        cost = float(pulp.value(model.objective) or 0.0)

        return {
            "status": status,
            "total_cost": cost,
            "additions": additions,
            "final_composition": final,
        }

    def new_blend(self, target_weight: float):
        """Design a fresh refrigerant blend of target_weight kilograms."""
        if target_weight <= 0:
            raise ValueError("target_weight must be positive.")

        qty = {e: pulp.LpVariable(f"qty_{e}", lowBound=0) for e in ELEMENTS}
        used = {e: pulp.LpVariable(f"used_{e}", cat="Binary") for e in ELEMENTS}
        model = pulp.LpProblem("new_blend", pulp.LpMinimize)

        # objective – minimise extraction cost of the new blend
        model += pulp.lpSum(ELEMENT_PRICES[e]["extraction"] * qty[e] for e in ELEMENTS)

        # total mass requirement
        model += pulp.lpSum(qty.values()) == target_weight

        # at least one element must be present in the new blend
        model += pulp.lpSum(used.values()) >= 1

        for e in ELEMENTS:
            model += qty[e] <= target_weight * used[e]

        self._enforce_ratios(model, qty, used)

        model.solve(pulp.PULP_CBC_CMD(msg=False))
        status = pulp.LpStatus[model.status]

        composition = {e: float(qty[e].value() or 0.0) for e in ELEMENTS}
        cost = float(pulp.value(model.objective) or 0.0)

        return {
            "status": status,
            "total_cost": cost,
            "extractions": composition,
            "final_composition": composition,
        }

    def optimise_mixture(
        self,
        initial_mix: Dict[str, float],
        target_weight: float,
    ):
        """Find the cheapest way to reach *target_weight* kilograms.

        The solver can:
        • remove any amount of the current charge (remove_e),
        • add up to 15 % of each original component (add_e), and/or
        • produce a brand-new quantity of each component (new_e).

        The final composition must satisfy the 4∶3∶2∶1 ratios inside the
        chosen subset of elements, and at least one element must remain.
        """

        if target_weight <= 0:
            raise ValueError("target_weight must be positive.")

        current = {e: initial_mix.get(e, 0.0) for e in ELEMENTS}
        current_mass = self._current_mass(current)

        # decision variables
        add = {e: pulp.LpVariable(f"add_{e}", lowBound=0) for e in ELEMENTS}
        remove = {
            e: pulp.LpVariable(f"remove_{e}", lowBound=0, upBound=current[e])
            for e in ELEMENTS
        }
        new = {e: pulp.LpVariable(f"new_{e}", lowBound=0) for e in ELEMENTS}

        used = {e: pulp.LpVariable(f"used_{e}", cat="Binary") for e in ELEMENTS}

        model = pulp.LpProblem("combined_refrigerant_optimisation", pulp.LpMinimize)

        # objective
        # cost of operations: adding fresh material, extracting new material and
        # discarding (removing) existing material incur their respective unit
        # costs.  Removal is treated the same as an extraction cost-wise.
        model += pulp.lpSum(
            ELEMENT_PRICES[e]["addition"] * add[e]
            + ELEMENT_PRICES[e]["extraction"] * (new[e] + remove[e])
            for e in ELEMENTS
        )

        # constraints
        # 15 % cap on additions to the *current* stock
        for e in ELEMENTS:
            model += add[e] <= current[e] * MAX_REFUEL_PERCENTAGE

        # final quantity of each element after all operations
        qty = {
            e: current[e] + add[e] - remove[e] + new[e] for e in ELEMENTS
        }

        # link binary *used* indicator to presence in the final mixture
        for e in ELEMENTS:
            model += qty[e] <= target_weight * used[e]
            model += qty[e] >= EPSILON * used[e]

        # at least one element must remain in the final blend
        model += pulp.lpSum(used.values()) >= 1

        # total mass requirement
        model += pulp.lpSum(qty.values()) == target_weight

        # enforce 4∶3∶2∶1 ratios inside the selected subset
        self._enforce_ratios(model, qty, used)

        # solve
        model.solve(pulp.PULP_CBC_CMD(msg=False))
        status = pulp.LpStatus[model.status]

        if status != "Optimal":
            return {"status": status}

        additions = {e: float(add[e].value() or 0.0) for e in ELEMENTS}
        removals = {e: float(remove[e].value() or 0.0) for e in ELEMENTS}
        extractions = {e: float(new[e].value() or 0.0) for e in ELEMENTS}
        final = {e: float(qty[e].value() or 0.0) for e in ELEMENTS}
        cost = float(pulp.value(model.objective) or 0.0)

        return {
            "status": status,
            "total_cost": cost,
            "additions": additions,
            "removals": removals,
            "extractions": extractions,
            "final_composition": final,
        }

    # Public helpers
    def calculate_max_additions(self) -> Dict[str, float]:
        """Return the 15 %-cap additions for the current charge.

        For elements not present we simply return 0.0.
        """

        if not self.initial_composition:
            return {e: 0.0 for e in ELEMENTS}
        return {e: self.initial_composition.get(e, 0.0) * MAX_REFUEL_PERCENTAGE for e in ELEMENTS}

    # Optimisation
    def optimize(self) -> Dict[str, float]:
        """Solve the chosen optimisation problem and return the result dict."""

        if self.operation == "refuel":
            return self.refuel(self.initial_composition, self.target_weight)

        if self.operation == "new_blend":
            return self.new_blend(self.target_weight)

        # optimise_mixture
        if self.target_weight is None:
            raise ValueError("target_weight required for optimise_mixture.")
        return self.optimise_mixture(self.initial_composition, self.target_weight)