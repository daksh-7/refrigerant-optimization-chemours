# Refrigerant Optimisation Toolkit

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/) [![PuLP](https://img.shields.io/badge/solver-PuLP-orange)](https://coin-or.github.io/pulp/) [![Tests](https://img.shields.io/badge/tests-pytest-brightgreen)](https://pytest.org/)

---

## Purpose

The repository provides an LP that selects the lowest-cost way to either top-up (refuel) an existing refrigerant charge or formulate a fresh blend from scratch. Four elements: A, B, C, D are available with addition and extraction prices given.  The model respects three core rules:

1. at most **15 %** of the current mass may be added when refuelling;
2. every blend keeps the fixed ratio **4 : 3 : 2 : 1** (or a consistent subset if some elements are absent);
3. at least one element must be present.

The optimisation logic lives in `src/model.py` and is solved with the PuLP library.

---

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -e .
```

The editable install (`-e`) honors the `pyproject.toml` metadata and exposes the command `refrigerant-opt`.

---

## Command-line interface

```bash
# Refuel (Scenario 1): top-up an existing charge
#   --mix    YAML file mapping each element to the current kg in the vessel
#   --target Desired total weight **after** refuel (kg). Optional – defaults to "as little as possible" within the 15 % cap.
refrigerant-opt refuel --mix examples/scenario1.yaml --target 110

# New blend (Scenario 2): formulate a fresh mixture from scratch
#   --weight Desired total weight of the new blend (kg)
refrigerant-opt new-blend --weight 80

# Combined optimisation (Scenario 3): make any combination of removals, additions
# and fresh extractions to hit a target weight at minimum cost.
#   --mix    YAML file with the *current* composition
#   --target Final desired weight (kg)
refrigerant-opt optimise --mix examples/scenario3.yaml --target 120

# Auto mode: convenience wrapper that currently behaves exactly like `optimise` but
# lets the optimiser decide the cheapest strategy automatically.
refrigerant-opt auto --mix examples/scenario1.yaml --target 110
```

Run `refrigerant-opt --help` (or any sub-command with `--help`) to see the full list of options.

> **Note:** the `examples/` directory only contains `scenario1.yaml` and `scenario3.yaml` because Scenario 2 (the fresh *new-blend* case) does **not** require an input composition file – the optimiser builds the mixture from scratch given only the `--weight` argument.

The tool prints a JSON report identical to the dictionaries returned by the Python API.

---

## Running the tests

```bash
pytest -v
```

The suite (`tests/test_model.py`) covers:

* attribute accessors (`operation`, `initial_composition`);
* maximum additions calculation for a 100 kg reference charge;
* solver output for refuelling and empty-tank cases;
* validation of bad inputs;
* formulation of an 80 kg new blend;
* combined extraction/addition optimisation to hit a 120 kg target.

All tests report **PASSED**.

---

## Usage example

```python
from src.model import RefrigerantOptimizer

# 1) Refuel an existing 100 kg charge
base = {"A": 40, "B": 30, "C": 20, "D": 10}
refuel = RefrigerantOptimizer("refuel", initial_composition=base)
print(refuel.optimize())

# 2) Formulate a brand-new 80 kg blend
blend = RefrigerantOptimizer("new_blend", target_weight=80)
print(blend.optimize())

# 3) Combined optimisation – reduce a 150 kg charge to 120 kg at minimum cost
mix = {"A": 60, "B": 45, "C": 30, "D": 15}
opt = RefrigerantOptimizer("optimise_mixture", initial_composition=mix, target_weight=120)
print(opt.optimize())

# 4) Auto mode (currently identical to optimise_mixture)
auto_opt = RefrigerantOptimizer("auto", initial_composition=mix, target_weight=120)
print(auto_opt.optimize())

# Helper: see how much you are allowed to add during refuel (15 % cap)
print(refuel.calculate_max_additions())
```

All calls return a dictionary with keys:

* `status`: CBC solver status (e.g. *Optimal*),
* `total_cost`: float,
* `final_composition`: element-mass mapping,
* operation-specific details (`additions`, `removals`, `extractions`).

---

## Project structure

```
├── src
│   ├── __init__.py
│   ├── cli.py           # Click CLI entry-point
│   ├── data.py          # price table, ratios, constants
│   └── model.py         # PuLP-based optimiser
├── tests                # pytest suite
│   ├── conftest.py
│   └── test_model.py
├── examples             # YAML scenario files
│   ├── scenario1.yaml
│   └── scenario3.yaml
└── pyproject.toml
```

---