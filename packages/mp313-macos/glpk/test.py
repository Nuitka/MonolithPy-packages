"""
Basic sanity tests for glpk package.
Tests C-backed (GLPK library) functionality without extra dependencies.
Note: This tests the swiglpk Python bindings for GLPK.
"""

import swiglpk as glpk


def test_version():
    """Test GLPK version is accessible."""
    major = glpk.glp_version()
    assert major is not None


def test_create_problem():
    """Test problem creation (C-backed)."""
    prob = glpk.glp_create_prob()
    assert prob is not None
    
    glpk.glp_delete_prob(prob)


def test_set_problem_name():
    """Test setting problem name (C-backed)."""
    prob = glpk.glp_create_prob()
    
    glpk.glp_set_prob_name(prob, "test_problem")
    name = glpk.glp_get_prob_name(prob)
    assert name == "test_problem"
    
    glpk.glp_delete_prob(prob)


def test_add_rows_cols():
    """Test adding rows and columns (C-backed)."""
    prob = glpk.glp_create_prob()
    
    # Add rows (constraints)
    glpk.glp_add_rows(prob, 3)
    assert glpk.glp_get_num_rows(prob) == 3
    
    # Add columns (variables)
    glpk.glp_add_cols(prob, 2)
    assert glpk.glp_get_num_cols(prob) == 2
    
    glpk.glp_delete_prob(prob)


def test_set_bounds():
    """Test setting variable bounds (C-backed)."""
    prob = glpk.glp_create_prob()
    glpk.glp_add_cols(prob, 1)
    
    # Set bounds: 0 <= x <= 10
    glpk.glp_set_col_bnds(prob, 1, glpk.GLP_DB, 0.0, 10.0)
    
    lb = glpk.glp_get_col_lb(prob, 1)
    ub = glpk.glp_get_col_ub(prob, 1)
    
    assert lb == 0.0
    assert ub == 10.0
    
    glpk.glp_delete_prob(prob)


def test_simple_lp():
    """Test simple LP problem (C-backed)."""
    # Maximize: z = x1 + x2
    # Subject to:
    #   x1 + 2*x2 <= 4
    #   x1, x2 >= 0
    
    prob = glpk.glp_create_prob()
    glpk.glp_set_prob_name(prob, "simple_lp")
    glpk.glp_set_obj_dir(prob, glpk.GLP_MAX)
    
    # Add rows (constraints)
    glpk.glp_add_rows(prob, 1)
    glpk.glp_set_row_bnds(prob, 1, glpk.GLP_UP, 0.0, 4.0)
    
    # Add columns (variables)
    glpk.glp_add_cols(prob, 2)
    
    # x1 >= 0
    glpk.glp_set_col_bnds(prob, 1, glpk.GLP_LO, 0.0, 0.0)
    glpk.glp_set_obj_coef(prob, 1, 1.0)
    
    # x2 >= 0
    glpk.glp_set_col_bnds(prob, 2, glpk.GLP_LO, 0.0, 0.0)
    glpk.glp_set_obj_coef(prob, 2, 1.0)
    
    # Set constraint matrix
    ia = glpk.intArray(3)
    ja = glpk.intArray(3)
    ar = glpk.doubleArray(3)
    
    ia[1], ja[1], ar[1] = 1, 1, 1.0  # a[1,1] = 1
    ia[2], ja[2], ar[2] = 1, 2, 2.0  # a[1,2] = 2
    
    glpk.glp_load_matrix(prob, 2, ia, ja, ar)
    
    # Solve
    glpk.glp_simplex(prob, None)
    
    # Get solution
    z = glpk.glp_get_obj_val(prob)
    x1 = glpk.glp_get_col_prim(prob, 1)
    x2 = glpk.glp_get_col_prim(prob, 2)
    
    assert z > 0
    assert x1 >= 0
    assert x2 >= 0
    
    glpk.glp_delete_prob(prob)


def test_mip():
    """Test mixed integer programming (C-backed)."""
    prob = glpk.glp_create_prob()
    glpk.glp_set_obj_dir(prob, glpk.GLP_MAX)
    
    # Add integer variable
    glpk.glp_add_cols(prob, 1)
    glpk.glp_set_col_kind(prob, 1, glpk.GLP_IV)  # Integer variable
    glpk.glp_set_col_bnds(prob, 1, glpk.GLP_DB, 0.0, 10.0)
    glpk.glp_set_obj_coef(prob, 1, 1.0)
    
    # Solve as MIP
    glpk.glp_simplex(prob, None)
    glpk.glp_intopt(prob, None)
    
    x = glpk.glp_mip_col_val(prob, 1)
    assert x == int(x)  # Should be integer
    
    glpk.glp_delete_prob(prob)


def test_objective_direction():
    """Test objective direction setting (C-backed)."""
    prob = glpk.glp_create_prob()
    
    glpk.glp_set_obj_dir(prob, glpk.GLP_MIN)
    assert glpk.glp_get_obj_dir(prob) == glpk.GLP_MIN
    
    glpk.glp_set_obj_dir(prob, glpk.GLP_MAX)
    assert glpk.glp_get_obj_dir(prob) == glpk.GLP_MAX
    
    glpk.glp_delete_prob(prob)


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

