from z3 import *


def grid_edges(grid):
    (height, width) = grid.shape
    for r in range(height):
        for c in range(width):
            if c != width - 1:
                # Yield edge right
                yield ((r, c), (r, c + 1))
            if r != height - 1:
                # Yield edge down
                yield ((r, c), (r + 1, c))


def find_new_sol_mat(solver, model, z3_vars):
    diff_c = []
    for k in z3_vars.keys():
        diff_c.append(z3_vars[k] != is_true(model[z3_vars[k]]))
    solver.add(And(Or(*diff_c)))
