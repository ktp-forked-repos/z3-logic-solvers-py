from z3 import *
import numpy as np


def grid_cells(grid):
    (height, width) = grid.shape
    for r in range(height):
        for c in range(width):
            yield (r, c)


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


def model_to_matrix(puzzle, model, z3_cells):
    ret = np.zeros(puzzle.shape)
    for k in z3_cells.keys():
        ret[k] = model[z3_cells[k]].as_long()
    return ret


def find_new_sol_mat(solver, model, z3_vars):
    diff_c = []
    for k in z3_vars.keys():
        diff_c.append(z3_vars[k] != is_true(model[z3_vars[k]]))
    solver.add(And(Or(*diff_c)))


def traverse_path(start_cell, model, z3_vars):
    path = [[], []]
    curr_cell = start_cell
    dir_from = None
    while True:
        (r, c) = curr_cell
        path[0].append(curr_cell[0])
        path[1].append(curr_cell[1])
        # Traverse to left
        if ((r, c - 1), (r, c)) in z3_vars and is_true(model[z3_vars[((r, c - 1), (r, c))]]) and dir_from != 'L':
            curr_cell = (r, c - 1)
            dir_from = 'R'
        elif ((r, c), (r, c + 1)) in z3_vars and is_true(model[z3_vars[((r, c), (r, c + 1))]]) and dir_from != 'R':
            curr_cell = (r, c + 1)
            dir_from = 'L'
        elif ((r - 1, c), (r, c)) in z3_vars and is_true(model[z3_vars[((r - 1, c), (r, c))]]) and dir_from != 'U':
            curr_cell = (r - 1, c)
            dir_from = 'D'
        elif ((r, c), (r + 1, c)) in z3_vars and is_true(model[z3_vars[((r, c), (r + 1, c))]]) and dir_from != 'D':
            curr_cell = (r + 1, c)
            dir_from = 'U'
        if curr_cell == start_cell:
            return tuple(path[0]), tuple(path[1])


def find_region(start_cell, model, z3_vars):
    # ret = [[start_cell[0]], [start_cell[1]]]
    poly_cells = [start_cell]
    prev_added = [start_cell]
    while len(prev_added):
        to_add = set()
        for edge_cell in prev_added:
            (r, c) = edge_cell
            cell_l = (r, c - 1)
            cell_r = (r, c + 1)
            cell_u = (r - 1, c)
            cell_d = (r + 1, c)
            cells = [cell_l, cell_r, cell_u, cell_d]
            for x in cells:
                # Check - valid cell, same value, and not currently in the region
                if x in z3_vars and model[z3_vars[x]] == model[z3_vars[start_cell]] and x not in poly_cells:
                    to_add.add(x)
                    # ret[0].append(x[0])
                    # ret[1].append(x[1])
        poly_cells.extend(to_add)
        prev_added = list(to_add)
    # return tuple(ret[0]), tuple(ret[1])
    return tuple(zip(*tuple(set(poly_cells))))
