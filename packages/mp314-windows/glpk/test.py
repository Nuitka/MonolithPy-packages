"""
Basic sanity tests for glpk package (PyGLPK).
Tests C-backed (GLPK library) functionality without extra dependencies.
Note: This tests the PyGLPK Python bindings for GLPK.
"""

import glpk


def test_version():
    """Test GLPK version is accessible."""
    version = glpk.env.version
    assert version is not None
    assert len(version) == 2  # (major, minor) tuple


def test_create_problem():
    """Test problem creation (C-backed)."""
    lp = glpk.LPX()
    assert lp is not None
    del lp


def test_set_problem_name():
    """Test setting problem name (C-backed)."""
    lp = glpk.LPX()

    lp.name = "test_problem"
    assert lp.name == "test_problem"

    del lp


def test_add_rows_cols():
    """Test adding rows and columns (C-backed)."""
    lp = glpk.LPX()

    # Add rows (constraints)
    lp.rows.add(3)
    assert len(lp.rows) == 3

    # Add columns (variables)
    lp.cols.add(2)
    assert len(lp.cols) == 2

    del lp


def test_set_bounds():
    """Test setting variable bounds (C-backed)."""
    lp = glpk.LPX()
    lp.cols.add(1)

    # Set bounds: 0 <= x <= 10
    lp.cols[0].bounds = 0.0, 10.0

    lb, ub = lp.cols[0].bounds

    assert lb == 0.0
    assert ub == 10.0

    del lp


def test_simple_lp():
    """Test simple LP problem (C-backed)."""
    # Maximize: z = x1 + x2
    # Subject to:
    #   x1 + 2*x2 <= 4
    #   x1, x2 >= 0

    lp = glpk.LPX()
    lp.name = "simple_lp"
    lp.obj.maximize = True

    # Add rows (constraints)
    lp.rows.add(1)
    lp.rows[0].bounds = None, 4.0  # <= 4

    # Add columns (variables)
    lp.cols.add(2)

    # x1 >= 0
    lp.cols[0].bounds = 0.0, None
    lp.obj[0] = 1.0

    # x2 >= 0
    lp.cols[1].bounds = 0.0, None
    lp.obj[1] = 1.0

    # Set constraint matrix: x1 + 2*x2
    lp.matrix = [(0, 0, 1.0), (0, 1, 2.0)]

    # Solve
    lp.simplex()

    # Get solution
    z = lp.obj.value
    x1 = lp.cols[0].primal
    x2 = lp.cols[1].primal

    assert z > 0
    assert x1 >= 0
    assert x2 >= 0

    del lp


def test_mip():
    """Test mixed integer programming (C-backed)."""
    lp = glpk.LPX()
    lp.obj.maximize = True

    # Add integer variable
    lp.cols.add(1)
    lp.cols[0].kind = int  # Integer variable
    lp.cols[0].bounds = 0.0, 10.0
    lp.obj[0] = 1.0

    # Solve as MIP
    lp.simplex()
    lp.integer()

    x = lp.cols[0].value
    assert x == int(x)  # Should be integer

    del lp


def test_objective_direction():
    """Test objective direction setting (C-backed)."""
    lp = glpk.LPX()

    lp.obj.maximize = False
    assert lp.obj.maximize == False

    lp.obj.maximize = True
    assert lp.obj.maximize == True

    del lp


if __name__ == "__main__":
    test_version()
    test_create_problem()
    test_set_problem_name()
    test_add_rows_cols()
    test_set_bounds()
    test_simple_lp()
    test_mip()
    test_objective_direction()
    print("All glpk tests passed!")

