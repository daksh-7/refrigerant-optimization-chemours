import pytest
from src.model import RefrigerantOptimizer
import math
from src.data import DEFAULT_RATIOS, ELEMENT_PRICES


@pytest.mark.parametrize(
    "initial,target,expected_status",
    [
        ({"A": 40, "B": 30, "C": 20, "D": 10}, None, "Optimal"),
        ({}, None, "Nothing to refuel"),
    ],
)
def test_refuel(initial, target, expected_status):
    opt = RefrigerantOptimizer("refuel", initial_composition=initial or None, target_weight=target)
    res = opt.optimize()
    assert res["status"] == expected_status
    if expected_status == "Optimal":
        assert 0 <= res["total_cost"] <= 200


def test_max_additions():
    sample = {"A": 40, "B": 30, "C": 20, "D": 10}
    opt = RefrigerantOptimizer("refuel", initial_composition=sample)
    assert opt.calculate_max_additions() == {"A": 6.0, "B": 4.5, "C": 3.0, "D": 1.5}


def test_basic_attributes():
    base = {"A": 1}
    opt = RefrigerantOptimizer("refuel", initial_composition=base)
    assert opt.operation == "refuel"
    assert opt.initial_composition == base


@pytest.mark.parametrize("weight", [10, 80])
def test_new_blend(weight):
    opt = RefrigerantOptimizer("new_blend", target_weight=weight)
    res = opt.optimize()
    assert res["status"] == "Optimal"
    assert abs(sum(res["final_composition"].values()) - weight) < 1e-6


def test_invalid_operation():
    with pytest.raises(ValueError):
        RefrigerantOptimizer("invalid")


def _ratio_holds(mix: dict[str, float], tol: float = 1e-6) -> bool:
    """Return *True* if every pair of *present* elements respects the 4:3:2:1 ratio."""

    # default tolerance loosened slightly for solver floating-point noise
    tol = max(tol, 1e-4)
    present = [e for e, qty in mix.items() if qty > tol]
    for i, ei in enumerate(present[:-1]):
        for ej in present[i + 1 :]:
            ri, rj = DEFAULT_RATIOS[ei], DEFAULT_RATIOS[ej]
            if abs(mix[ei] * rj - mix[ej] * ri) > tol:
                return False
    return True


def test_refuel_scenario1_exact():
    """Scenario 1: refuel a 100 kg charge exactly to the 115 kg 15 % cap."""

    initial = {"A": 40, "B": 30, "C": 20, "D": 10}
    target = 115  # 15 kg total addition (15 %)

    opt = RefrigerantOptimizer("refuel", initial_composition=initial, target_weight=target)
    res = opt.optimize()

    assert res["status"] == "Optimal"
    assert math.isclose(sum(res["final_composition"].values()), target, abs_tol=1e-4)
    assert _ratio_holds(res["final_composition"])

    expected_add = {"A": 6.0, "B": 4.5, "C": 3.0, "D": 1.5}
    for e in expected_add:
        assert math.isclose(res["additions"][e], expected_add[e], rel_tol=1e-4)

    expected_cost = (
        expected_add["A"] * ELEMENT_PRICES["A"]["addition"]
        + expected_add["B"] * ELEMENT_PRICES["B"]["addition"]
        + expected_add["C"] * ELEMENT_PRICES["C"]["addition"]
        + expected_add["D"] * ELEMENT_PRICES["D"]["addition"]
    )
    assert math.isclose(res["total_cost"], expected_cost, rel_tol=1e-4)


def test_new_blend_scenario2_cheapest_element_only():
    """Scenario 2: build an 80 kg blend using the cheapest element only (C)."""

    weight = 80
    opt = RefrigerantOptimizer("new_blend", target_weight=weight)
    res = opt.optimize()

    assert res["status"] == "Optimal"
    assert math.isclose(sum(res["final_composition"].values()), weight, abs_tol=1e-5)

    # Optimal solution should use only element C because it has the lowest extraction cost.
    assert res["final_composition"]["C"] >= weight * 0.999  # allow tiny numeric drift
    for e in ("A", "B", "D"):
        assert res["final_composition"][e] <= 1e-6

    assert math.isclose(res["total_cost"], weight * ELEMENT_PRICES["C"]["extraction"], rel_tol=1e-4)


def test_optimise_mixture_scenario3():
    """Scenario 3: reduce a 150 kg 4:3:2:1 blend to 120 kg at minimum cost (pure removals)."""

    initial = {"A": 60, "B": 45, "C": 30, "D": 15}
    target = 120

    opt = RefrigerantOptimizer(
        "optimise_mixture", initial_composition=initial, target_weight=target
    )
    res = opt.optimize()

    assert res["status"] == "Optimal"

    final = res["final_composition"]
    assert math.isclose(sum(final.values()), target, abs_tol=1e-5)
    assert _ratio_holds(final)

    # The theoretical lower bound is removing exactly 12, 9, 6, 3 kg respectively (cost ≈ 159).
    assert res["total_cost"] <= 160  # small buffer to adjust for noise