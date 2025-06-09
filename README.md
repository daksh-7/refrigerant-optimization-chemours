# Refrigerant Optimization Model

![Project Status](https://img.shields.io/badge/status-development-orange)
![Language](https://img.shields.io/badge/python-3.10+-blue.svg)
![Library](https://img.shields.io/badge/library-PuLP-orange)
![Testing](https://img.shields.io/badge/testing-Pytest-brightgreen)

## 1. Project Overview

This project aims to develop a linear optimization model to enhance the cost-effectiveness and sustainability of refrigerant management. The model will determine the most economical strategy for handling refrigerant stocks by deciding between two primary actions:

1.  **Refueling:** Topping up an existing refrigerant mixture with a limited quantity of new elements.
2.  **Formulation:** Creating a new refrigerant blend from a specified subset of available elements.

The solution will be a decision-support tool that minimizes operational costs while adhering to strict chemical composition, ratio, and quantity constraints. This work is foundational for optimizing resource allocation in refrigerant recycling and distillation processes.

## 2. Approach & Proposed Solution

The problem is a resource allocation challenge, perfectly suited for **Linear Programming (LP)**. My approach is to translate the business rules and constraints into a formal mathematical model and solve it using the `PuLP` library in Python.

### A. Mathematical Formulation (The Plan)

The model will be built around the following core components:

*   **Decision Variables:**
    *   `add_e`: Continuous variable representing the kilograms (kg) of element `e` to **add**.
    *   `extract_e`: Continuous variable representing the kilograms (kg) of element `e` to **extract/remove**.
    *   Variables to handle the binary choice between refueling and creating a new blend will be formulated to ensure the logic is mutually exclusive.

*   **Objective Function:**
    The primary goal is to minimize total cost. The objective function will be:
    `Minimize(Total Cost) = Σ (add_e * addition_price_e) + Σ (extract_e * extraction_price_e)`
    for all elements `e` in {A, B, C, D}.

*   **Key Constraints:**
    The model's logic will be governed by a set of precise constraints derived directly from the assignment:
    1.  **Mass Balance:** The final weight of the refrigerant must match the system's requirement.
    2.  **Refueling Limit:** When refueling, the amount of each element added (`add_e`) cannot exceed 15% of its original quantity in the mixture.
    3.  **Ratio Integrity:** For both refueling and new blend formulation, the elemental ratios (e.g., 4:3:2:1) must be strictly maintained within the chosen subset of elements.
    4.  **Subset Composition:** A new blend must use a subset of the original elements {A, B, C, D}, containing at least one element.
    5.  **Non-Negativity:** All decision variables for quantities must be greater than or equal to zero.

### B. Development Methodology

This project will be developed using a **Test-Driven Development (TDD)** approach. I will begin by writing failing tests that codify the requirements of each scenario. I will then write the minimum amount of code required to make the tests pass, before refactoring for clarity and efficiency. This ensures the model is robust, verifiable, and correct by design.

## 3. Installation Instructions

This project is a standard Python package. To set up the environment and run the model, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/daksh-7/refrigerant-optimization-chemours.git
    cd refrigerant-optimization-chemours
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -e .
    ```
    
    For development (includes testing tools):
    ```bash
    pip install -e .[dev]
    ```

## 4. Usage

The model is accessible via a command-line interface (CLI) for ease of use and testing.

### Running Tests
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_model.py -v
```

### Running Optimization (Planned)
```bash
# To run a specific scenario from the assignment
python -m src.cli solve --scenario examples/scenario1.yaml

# Example output:
# --- Scenario 1: Refueling Optimization ---
# Status: Optimal
# Total Cost: $160.50
#
# --- Decision Variables ---
# Add Element A: 6.0 kg
# Add Element B: 4.5 kg
# Add Element C: 3.0 kg
# Add Element D: 1.5 kg
```

## 5. Project Structure

```
refrigerant-optimization-chemours/
├── src/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── data.py             # Static data and constants
│   ├── model.py            # Core PuLP optimization model
│   └── scenarios.py        # Scenario loading and processing
├── tests/
│   ├── test_model.py       # Core model tests
│   └── test_edge.py        # Edge case tests
├── examples/
│   ├── scenario1.yaml      # Test scenarios
│   ├── scenario2.yaml
│   └── scenario3.yaml
└── pyproject.toml          # Project configuration