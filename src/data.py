#Definitions
ELEMENT_PRICES = {'A': {'extraction': 5, 'addition': 10}, 
                  'B': {'extraction': 6, 'addition': 12}, 
                  'C': {'extraction': 4, 'addition': 8}, 
                  'D': {'extraction': 7, 'addition': 15}}

DEFAULT_RATIOS = {'A': 4, 'B': 3, 'C': 2, 'D': 1}

MAX_REFUEL_PERCENTAGE = 0.15

ELEMENTS = ['A', 'B', 'C', 'D']

DEFAULT_SCENARIOS = {'scenario1': {'initial_weight': 100,'initial_composition': {'A': 40, 'B': 30, 'C': 20, 'D': 10}},
                     'scenario2': {'target_weight': 80, 'operation': 'new_blend'},
                     'scenario3': {'initial_weight': 150, 'target_weight': 120, 'initial_composition': {'A': 60, 'B': 45, 'C': 30, 'D': 15}}}