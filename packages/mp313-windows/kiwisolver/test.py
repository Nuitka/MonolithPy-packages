"""
Basic sanity tests for kiwisolver package.
Tests C-backed constraint solver functionality without extra dependencies.
"""

import kiwisolver as kiwi


def test_version():
    """Test version is accessible."""
    assert hasattr(kiwi, '__version__')
    assert kiwi.__version__ is not None


def test_variable_creation():
    """Test variable creation (C-backed)."""
    x = kiwi.Variable('x')
    assert x.name() == 'x'
    
    y = kiwi.Variable('y')
    assert y.name() == 'y'


def test_simple_constraint():
    """Test simple constraint solving (C-backed)."""
    solver = kiwi.Solver()
    
    x = kiwi.Variable('x')
    
    # Add constraint: x == 10
    solver.addConstraint(x == 10)
    solver.updateVariables()
    
    assert x.value() == 10


def test_multiple_constraints():
    """Test multiple constraints (C-backed)."""
    solver = kiwi.Solver()
    
    x = kiwi.Variable('x')
    y = kiwi.Variable('y')
    
    # x + y == 20
    # x == 2 * y
    solver.addConstraint(x + y == 20)
    solver.addConstraint(x == 2 * y)
    solver.updateVariables()
    
    # x should be ~13.33, y should be ~6.67
    assert abs(x.value() - 40/3) < 1e-10
    assert abs(y.value() - 20/3) < 1e-10


def test_inequality_constraints():
    """Test inequality constraints (C-backed)."""
    solver = kiwi.Solver()
    
    x = kiwi.Variable('x')
    
    # x >= 5
    # x <= 10
    solver.addConstraint(x >= 5)
    solver.addConstraint(x <= 10)
    solver.updateVariables()
    
    assert 5 <= x.value() <= 10


def test_strength():
    """Test constraint strengths (C-backed)."""
    solver = kiwi.Solver()
    
    x = kiwi.Variable('x')
    
    # Strong constraint: x >= 0
    solver.addConstraint((x >= 0) | kiwi.strength.strong)
    
    # Weak constraint: x == 100
    solver.addConstraint((x == 100) | kiwi.strength.weak)
    
    solver.updateVariables()
    
    # x should be 100 (weak constraint satisfied when possible)
    assert x.value() == 100


def test_edit_variable():
    """Test edit variables (C-backed)."""
    solver = kiwi.Solver()
    
    x = kiwi.Variable('x')
    y = kiwi.Variable('y')
    
    # y = 2 * x
    solver.addConstraint(y == 2 * x)
    
    # Make x editable
    solver.addEditVariable(x, kiwi.strength.strong)
    
    # Suggest value for x
    solver.suggestValue(x, 5)
    solver.updateVariables()
    
    assert x.value() == 5
    assert y.value() == 10
    
    # Change suggested value
    solver.suggestValue(x, 10)
    solver.updateVariables()
    
    assert x.value() == 10
    assert y.value() == 20


def test_remove_constraint():
    """Test removing constraints (C-backed)."""
    solver = kiwi.Solver()
    
    x = kiwi.Variable('x')
    
    c1 = x == 10
    c2 = x == 20
    
    solver.addConstraint(c1)
    solver.updateVariables()
    assert x.value() == 10
    
    solver.removeConstraint(c1)
    solver.addConstraint(c2)
    solver.updateVariables()
    assert x.value() == 20


def test_expression():
    """Test expressions (C-backed)."""
    x = kiwi.Variable('x')
    y = kiwi.Variable('y')
    
    # Create expression
    expr = 2 * x + 3 * y + 5
    
    solver = kiwi.Solver()
    solver.addConstraint(x == 1)
    solver.addConstraint(y == 2)
    solver.addConstraint(kiwi.Variable('z') == expr)
    solver.updateVariables()
    
    # z should be 2*1 + 3*2 + 5 = 13
    z = kiwi.Variable('z')
    solver2 = kiwi.Solver()
    solver2.addConstraint(x == 1)
    solver2.addConstraint(y == 2)
    solver2.addConstraint(z == 2 * x + 3 * y + 5)
    solver2.updateVariables()
    
    assert z.value() == 13


def test_layout_example():
    """Test layout-like constraint problem (C-backed)."""
    solver = kiwi.Solver()
    
    # Simulate a simple layout: two boxes side by side
    left = kiwi.Variable('left')
    width1 = kiwi.Variable('width1')
    width2 = kiwi.Variable('width2')
    right = kiwi.Variable('right')
    
    # Constraints
    solver.addConstraint(left == 0)
    solver.addConstraint(right == 100)
    solver.addConstraint(width1 + width2 == right - left)
    solver.addConstraint(width1 == width2)  # Equal widths
    
    solver.updateVariables()
    
    assert left.value() == 0
    assert right.value() == 100
    assert width1.value() == 50
    assert width2.value() == 50


if __name__ == "__main__":
    test_version()
    test_variable_creation()
    test_simple_constraint()
    test_multiple_constraints()
    test_inequality_constraints()
    test_strength()
    test_edit_variable()
    test_remove_constraint()
    test_expression()
    test_layout_example()
    print("All kiwisolver tests passed!")

