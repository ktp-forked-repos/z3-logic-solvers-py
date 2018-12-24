from z3 import *
import numpy as np

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


def traverse_path(puzzle, start_cell, model, z3_vars):
    (height, width) = puzzle.shape
    path = [[], []]
    curr_cell = start_cell
    dir_from = None
    while True:
        (r, c) = curr_cell
        path[0].append(curr_cell[0])
        path[1].append(curr_cell[1])
        # Traverse to left
        if c != 0 and is_true(model[z3_vars[((r, c - 1), (r, c))]]) and dir_from != 'L':
            curr_cell = (r, c - 1)
            dir_from = 'R'
        elif c != width - 1 and is_true(model[z3_vars[((r, c), (r, c + 1))]]) and dir_from != 'R':
            curr_cell = (r, c + 1)
            dir_from = 'L'
        elif r != 0 and is_true(model[z3_vars[((r - 1, c), (r, c))]]) and dir_from != 'U':
            curr_cell = (r - 1, c)
            dir_from = 'D'
        elif r != height - 1 and is_true(model[z3_vars[((r, c), (r + 1, c))]]) and dir_from != 'D':
            curr_cell = (r + 1, c)
            dir_from = 'U'
        if curr_cell == start_cell:
            return tuple(path[0]), tuple(path[1])


def test_single_loop(puzzle, model, z3_vars):
    # Find all cells that are on the path
    on_path = np.zeros(puzzle.shape, dtype="bool")
    for k in z3_vars.keys():
        if is_true(model[z3_vars[k]]):
            on_path[k[0]] = 1
            on_path[k[1]] = 1
    start = np.unravel_index(np.argmax(on_path), puzzle.shape)
    # Set all reachable cells on the path to 0
    on_path[traverse_path(puzzle, start, model, z3_vars)] = 0
    # Return if we reached all cells
    return not np.any(on_path)
