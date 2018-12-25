from z3 import *
from z3_helpers import *
import numpy as np


def prior_constraints(solver, puzzle, z3_vars):
    for cell in grid_cells(puzz):
        if puzzle[cell] != '.':
            solver.add(And(z3_vars[cell] == int(puzzle[cell])))
        else:
            solver.add(And(z3_vars[cell] > 0))


def test_polynomino_counts(puzzle, model, z3_vars):
    # Find all polynominos
    polynominos = np.zeros(puzzle.shape)
    while 0 in polynominos:
        start_cell = np.unravel_index(np.argmin(polynominos), puzzle.shape)
        region = find_region(start_cell, model, z3_vars)
        polynominos[region] = len(list(zip(*region)))
        # print(polynominos)
    puzz_soln = model_to_matrix(puzzle, model, z3_vars)
    return not np.any(puzz_soln - polynominos)


def adjust_polynomino_constraints(solver, puzzle, model, z3_vars):
    ## Broken, fix later.
    # Find all polynominos
    poly_count = 0
    polynominos = np.zeros(puzzle.shape) - 1
    while -1 in polynominos:
        poly_count += 1
        start_cell = np.unravel_index(np.argmin(polynominos), puzzle.shape)
        polynominos[find_region(start_cell, model, z3_vars)] = poly_count
    poly_rules = []
    # Iterate all polynominos
    for p in range(1, poly_count + 1):
        curr_rule = []
        region = list(zip(*np.where(polynominos == p)))
        # Satisfied region - add irrelevant rule to avoid breaking
        if len(region) == model[z3_vars[region[0]]].as_long():
            curr_rule.append(And(True))
            print('%d correct size - %d' % (p, model[z3_vars[region[0]]].as_long()))
            poly_rules.append(curr_rule)
            continue
        grow_region = len(region) < model[z3_vars[region[0]]].as_long()
        shrink_region = len(region) > model[z3_vars[region[0]]].as_long()
        for cell in region:
            if grow_region:
                (r, c) = cell
                cell_l = (r, c - 1)
                cell_r = (r, c + 1)
                cell_u = (r - 1, c)
                cell_d = (r + 1, c)
                neighbors = [cell_l, cell_r, cell_u, cell_d]
                for x in neighbors:
                    if x in z3_vars and polynominos[x] != polynominos[cell]:
                        # If the cell is not taken over by another region
                        # then add this edge as a possible growth location
                        # curr_rule.append(If(z3_vars[cell] == model[z3_vars[cell]],
                        #                     z3_vars[x] == model[z3_vars[cell]],
                        #                     # Replace this condition?0
                        #                     True))
                        curr_rule.append(z3_vars[x] == model[z3_vars[cell]])
            elif shrink_region:
                curr_rule.append(z3_vars[cell] != model[z3_vars[cell]])
        poly_rules.append(curr_rule)
    solver.add(And(*[Or(*rule) for rule in poly_rules]))


def fillomino_to_str(puzzle, model, z3_vars):
    grid = np.zeros(puzzle.shape)
    for cell in grid_cells(puzzle):
        grid[cell] = model[z3_vars[cell]].as_long()
    return str(grid)


puzz_s = """. . . 3 . . . . 5
            . . 8 3 10 . . 5 .
             . 3 . . . 4 4 . .
            1 3 . 3 . . 2 . .
            . 2 . . 3 . . 2 .
            . . 2 . . 3 . 1 3
            . . 4 4 . . . 3 .
            . 4 . . 4 3 3 . .
            6 . . . . 1 . . ."""

puzz = np.array([x.strip().split(" ") for x in puzz_s.replace("\r\n", "\n").split("\n")])

p_vars = {}

for cell in grid_cells(puzz):
    p_vars[cell] = Int(str(cell))

s = Solver()
prior_constraints(s, puzz, p_vars)
while s.check() == sat:
    m = s.model()
    print(fillomino_to_str(puzz, m, p_vars))
    if not test_polynomino_counts(puzz, m, p_vars):
        print("Adjusting polynominos...")
        adjust_polynomino_constraints(s, puzz, m, p_vars)
    else:
        break

print(s.check())