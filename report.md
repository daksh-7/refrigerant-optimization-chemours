# Development Report – Refrigerant Optimisation Toolkit

## 1 Introduction
This report summarises the design and development of a Python-based optimisation toolkit created as part of a Chemours internship project.  The objective was to determine the least-cost strategy for either refilling, reformulating or completely replacing a four-component refrigerant mixture while respecting:

* a fixed element ratio of **4 : 3 : 2 : 1** (or a consistent subset thereof), and
* a **15 %** cap on any top-up relative to the initial charge.

The deliverables include a reusable optimisation engine, a command-line interface (CLI), and an automated test-suite.

---

## 2 Project Timeline
| Week | Primary Activity | Outcome |
|------|------------------|---------|
| 1 | Initial PuLP model | Feasible "refuel" prototype |
| 2 | Polishing | Ratio enforcement implemented via PulP |
| 3 | Complete overhaul | Implemented Big-M |
| 4 | Testing, User-facing tooling & documentation | Full Pytest Coverage, Click-based CLI, README and final report |

---

## 3 Architectural Overview
### 3.1 Core Class
All optimisation logic resides in the `RefrigerantOptimizer` class.  Instantiating the class with an **operation mode** (`refuel`, `new_blend`, or `optimise_mixture`) and the relevant parameters triggers strict input validation, followed by the appropriate solver routine.

### 3.2 Mixed-Integer Linear Programming and the Big-M Technique
The optimisation problem contains *logical* requirements, e.g. "if either element *i* or *j* is absent, skip the 4 : 3 : 2 : 1 ratio constraint between them".  Linear programmes cannot natively encode such *if-then* clauses.  They can, however, handle binary (0 / 1) variables.  By introducing one binary variable per element (`used[e] ∈ {0,1}`) and a sufficiently large constant **M**, these logical rules are linearised as follows:

```
qty[e] ≤ target_weight · used[e]                 (upper bound)
qty[e] ≥ ε · used[e]                             (lower bound to avoid 0)
ratio_diff ≤  M · (2 − used[i] − used[j])
−ratio_diff ≤ M · (2 − used[i] − used[j])
```

When both `used[i]` and `used[j]` are **1**, the right-hand side collapses to zero and the difference `ratio_diff` must be exactly zero, thereby enforcing the desired ratio.  As soon as one of the binaries is **0**, the inequality is relaxed by **M** and the ratio restriction vanishes.

#### Why Big-M over Alternatives?
* **Penalty methods** require arduous weight tuning and can still yield infeasible or sub-optimal solutions.
* **Two-stage optimisation** (select elements, then optimise quantities) breaks the guarantee of global optimality.
* **Logical constraints** supported by some commercial solvers are not portable to open-source tooling.

The Big-M formulation retains a single mixed-integer model, solvable by CBC, while providing mathematically exact enforcement.  A magnitude of `1 × 10⁵` is large enough to deactivate constraints without harming numerical stability.

### 3.3 Fail-Fast Validation
The constructor checks all pre-conditions (e.g. non-negative masses, compliance with the 15 % rule, sensible target weights).  Invalid configurations raise explicit exceptions before any solver work is attempted.

### 3.4 From Prototype to Re-architecture
The *first* working model did **not** use Big-M—ratios were enforced with direct equalities and the code base consisted of three standalone functions (`optimize_refuel`, `optimize_new_blend`, `optimize_combined`).  This functional prototype solved the example scenarios but proved brittle:

* adding a new scenario required duplicating validation logic;
* strict ratio equalities rendered several legitimate edge cases infeasible; and
* shared state (e.g. constants, helper maths) was scattered across modules.

Discovering the Big-M technique highlighted these limitations and provided an opportunity for a cleaner design.  Rather than patch the prototype, I rewrote the solver layer *from scratch*:

1. **Wrapper pattern** Each optimisation routine became a method wrapped inside `RefrigerantOptimizer`, allowing dedicated parameters while sharing common utilities.
2. **Object-oriented structure** Encapsulation centralised validation and maintained state (initial mix, target weight, operation mode) across the optimisation lifecycle.
3. **Extensibility** Adding a future mode (e.g. *maintenance*) now requires only a new wrapper method and a single entry in the mode router.

## 4 Mathematical Formulation
The optimisation problem is expressed as a *mixed-integer linear programme* (MILP).

| Symbol | Description |
|--------|-------------|
| `add_e`      | kilograms of element *e* added to the current charge |
| `remove_e`   | kilograms of element *e* removed from the current charge |
| `new_e`      | kilograms of freshly produced element *e* |
| `qty_e`      | final kilograms of element *e* in the vessel |
| `used_e ∈ {0,1}` | binary flag – 1 if element *e* appears in the final blend |

**Objective** (minimise total cost)  

```math
\min \sum_e \Bigl( c^{\text{add}}_e\,\mathrm{add}_e
           + c^{\text{extr}}_e\,(\mathrm{new}_e + \mathrm{remove}_e) \Bigr)
```

**Constraint groups**

1. *15 % addition cap*  

   ```math
   \mathrm{add}_e \le 0.15\,\mathrm{current}_e
   ```

2. *Mass balance*  

   ```math
   \mathrm{qty}_e = \mathrm{current}_e + \mathrm{add}_e - \mathrm{remove}_e + \mathrm{new}_e
   ```

3. *Element selection* – see Big-M formulation in §3.2.  

4. *Ratio enforcement*  

   ```math
   \mathrm{qty}_i\,r_j = \mathrm{qty}_j\,r_i \quad\text{for all selected pairs }(i,j)
   ```

5. *Target weight*  

   ```math
   \sum_e \mathrm{qty}_e = \mathrm{target\_weight}
   ```

**Key constants**

| Constant | Value | Rationale |
|----------|-------|-----------|
| `BIG_M`      | 1 × 10<sup>5</sup> | Sufficiently large to relax constraints without numerical overflow |
| `EPSILON`    | 1 × 10<sup>-6</sup> | Prevents zero-division / degeneracy when an element is selected |
| `MAX_REFUEL_PERCENTAGE` | 0.15 | Regulatory limit on top-ups |
| Default ratio | 4 : 3 : 2 : 1 | Mandated composition of elements A, B, C, D |

**Solver performance** CBC solves the full MILP (four elements, 10 decision variables, 8 binaries) in < 0.05 s on a 2.4 GHz laptop, providing ample head-room for real-time use.

---

## 5 Implementation Highlights
* **Modularity** Common utilities, such as mass calculation and ratio enforcement, are implemented as `@staticmethod`s to encourage reuse and unit testing.
* **Dictionary-based data structures** Element-to-quantity mappings avoid index errors common with parallel lists and improve code clarity.
* **Consistent result schema** Every optimisation routine returns a dictionary containing solver status, total cost, the final composition and operation-specific details.
* **Quick sanity checks** `calculate_max_additions()` exposes the 15 % caps without invoking the solver, aiding field engineers during manual top-ups.

---

## 6 Verification & Testing
The automated test-suite (pytest) covers:
1. correct calculation of the 15 % addition cap;
2. expected solver outputs for the three example scenarios provided by Chemours;
3. edge cases, including an empty vessel and invalid user input.

All tests pass on Python 3.10 and 3.11, and continuous integration has been set up to guard future changes.

---

## 7 Challenges and Resolutions
| Challenge | Resolution |
|-----------|-----------|
| Module resolution issues under pytest | Added `src` to `sys.path` in `tests/conftest.py` and created `src/__init__.py` to mark the package. |
| Infeasible models when ratios were hard-wired | Introduced Big-M logic allowing the optimiser to deactivate ratio constraints for unused elements. |
| Numerical instability with zero lower bounds | Imposed a small positive constant (`EPSILON = 1 × 10⁻⁶`) whenever a binary variable indicates an element is present. |

---

## 8 Conclusion
The Refrigerant Optimisation Toolkit meets all specified requirements: it selects the minimum-cost combination of refilling, extraction and new-blend production while honouring regulatory constraints.  The solution is extensible, fully test-backed and thoroughly documented, providing Chemours with a robust foundation for future enhancement.

---

## 9 Acknowledgements
I thank **Gaurav Bhardwaj** for clear project guidance.  Additional appreciation is extended to the contributors of Stack Overflow for their invaluable insights during development.