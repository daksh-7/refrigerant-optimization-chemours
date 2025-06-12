from src.model import RefrigerantOptimizer
from src.data import ELEMENT_PRICES, DEFAULT_RATIOS

class TestScenario1Refuel:    
#All tests but the third one pass because the RefrigerantOptimizer class, including some methods, are now defined in model.py and usable. 
    def test_s1_basic(self):
        initial_composition = {'A': 40, 'B': 30, 'C': 20, 'D': 10}
        
        optimizer = RefrigerantOptimizer(
            operation='refuel',
            initial_composition=initial_composition
        )
        
        assert optimizer is not None
        assert optimizer.operation == 'refuel'
        assert optimizer.initial_composition == initial_composition
    
    def test_s1_max_additions(self):
        initial_composition = {'A': 40, 'B': 30, 'C': 20, 'D': 10}
        
        optimizer = RefrigerantOptimizer(
            operation='refuel',
            initial_composition=initial_composition
        )
        max_additions = optimizer.calculate_max_additions()
        
        expected = {'A': 6.0, 'B': 4.5, 'C': 3.0, 'D': 1.5}
        assert max_additions == expected

#Since optimize_refuel and optimize_new_blend are not yet defined, and optimize() calls these methods,this test will fail.    

    def test_s1_optimization(self):
        initial_composition = {'A': 40, 'B': 30, 'C': 20, 'D': 10}
        
        optimizer = RefrigerantOptimizer(
            operation='refuel',
            initial_composition=initial_composition
        )
        result = optimizer.optimize()
        
        assert result is not None

        assert 'status' in result
        assert 'total_cost' in result
        assert 'additions' in result

        assert result['status'] == 'Optimal'
        assert result['total_cost'] >= 0
        assert result['total_cost'] <= 200