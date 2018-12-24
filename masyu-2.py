from z3 import *
from z3_helpers import *
import numpy as np
import itertools


def path_constraints(solver, cells, z3_vars):
    for (r, c) in cells:
        edge_c = []
        edge_l = ((r, c - 1), (r, c))
        edge_r = ((r, c), (r, c + 1))
        edge_u = ((r - 1, c), (r, c))
        edge_d = ((r, c), (r + 1, c))
        edges = [edge_l, edge_r, edge_u, edge_d]
        valid = set()
        for x in edges:
            if x in z3_vars:
                valid.add(x)
        edge_c.append(And(*[Not(z3_vars[x]) for x in valid]))
        for pair in itertools.combinations(valid, 2):
            rule = []
            rule.extend([z3_vars[x] for x in pair])
            rule.extend([Not(z3_vars[x]) for x in valid - set(pair)])
            edge_c.append(And(*rule))
        solver.append(Or(*edge_c))


def white_pearl_constraints(solver, pearls, z3_vars):
    for (r, c) in pearls:
        pearl_c = []
        edge_l = ((r, c - 1), (r, c))
        edge_r = ((r, c), (r, c + 1))
        edge_u = ((r - 1, c), (r, c))
        edge_d = ((r, c), (r + 1, c))
        # Horizontal edge through cell
        if edge_l in z3_vars and edge_r in z3_vars:
            # Constraint enforcing horizontal edge
            straight_c = [And(z3_vars[edge_l], z3_vars[edge_r])]
            # All possible turns
            turns = [((r - 1, c - 1), (r, c - 1)),
                     ((r, c - 1), (r + 1, c - 1)),
                     ((r - 1, c + 1), (r, c + 1)),
                     ((r, c + 1), (r + 1, c + 1))]
            turn_c = []
            for t in turns:
                if t in z3_vars:
                    turn_c.append(z3_vars[t])
            # No possible turns - add unsatisfiable constraint.
            if len(turn_c) == 0:
                print("uhoh 1")
                solver.add(And(False))
            # If we have turns, then Or all of them
            else:
                straight_c.append(Or(*turn_c))
            pearl_c.append(And(*straight_c))
        # Vertical edge through cell
        if edge_u in z3_vars and edge_d in z3_vars:
            # Constraint enforcing vertical edge
            straight_c = [And(z3_vars[edge_u], z3_vars[edge_d])]
            # All possible turns
            turns = [((r - 1, c - 1), (r - 1, c)),
                     ((r - 1, c), (r - 1, c + 1)),
                     ((r + 1, c - 1), (r + 1, c)),
                     ((r + 1, c), (r + 1, c + 1))]
            turn_c = []
            for t in turns:
                if t in z3_vars:
                    turn_c.append(z3_vars[t])
            if len(turn_c) == 0:
                solver.add(And(False))
            else:
                straight_c.append(Or(*turn_c))
            pearl_c.append(And(*straight_c))
        if len(pearl_c) == 0:
            solver.add(And(False))
        else:
            solver.add(Or(*pearl_c))


def black_pearl_constraints(solver, pearls, z3_vars):
    for (r, c) in pearls:
        pearl_c = []
        edge_l = ((r, c - 1), (r, c))
        edge_ll = ((r, c - 2), (r, c - 1))
        edge_r = ((r, c), (r, c + 1))
        edge_rr = ((r, c + 1), (r, c + 2))
        edge_u = ((r - 1, c), (r, c))
        edge_uu = ((r - 2, c), (r - 1, c))
        edge_d = ((r, c), (r + 1, c))
        edge_dd = ((r + 1, c), (r + 2, c))
        if edge_l in z3_vars and edge_ll in z3_vars and edge_u in z3_vars and edge_uu in z3_vars:
            pearl_c.append(And(z3_vars[edge_l], z3_vars[edge_ll],
                               z3_vars[edge_u], z3_vars[edge_uu]))
        if edge_l in z3_vars and edge_ll in z3_vars and edge_d in z3_vars and edge_dd in z3_vars:
            pearl_c.append(And(z3_vars[edge_l], z3_vars[edge_ll],
                               z3_vars[edge_d], z3_vars[edge_dd]))
        if edge_r in z3_vars and edge_rr in z3_vars and edge_u in z3_vars and edge_uu in z3_vars:
            pearl_c.append(And(z3_vars[edge_r], z3_vars[edge_rr],
                               z3_vars[edge_u], z3_vars[edge_uu]))
        if edge_r in z3_vars and edge_rr in z3_vars and edge_d in z3_vars and edge_dd in z3_vars:
            pearl_c.append(And(z3_vars[edge_r], z3_vars[edge_rr],
                               z3_vars[edge_d], z3_vars[edge_dd]))
        solver.add(Or(*pearl_c))


def coalesce_islands_constraints(puzzle, solver, model, z3_vars):
    # Given an incorrect model that has multiple loops, add a set of
    # constraints that ensure that an island is merged with at least
    # one adjacent island.

    # Find all loops
    loops = np.zeros(puzzle.shape)
    loop_count = 1
    for k in z3_vars.keys():
        if is_true(model[z3_vars[k]]):
            loops[k[0]] = -1
            loops[k[1]] = -1
    while -1 in loops:
        start_cell = np.unravel_index(np.argmin(loops), puzzle.shape)
        loops[traverse_path(puzzle, start_cell, model, z3_vars)] = loop_count
        loop_count += 1

    # For all loops, construct possible edges to another loop
    loop_rules = [[]] * loop_count
    for n in range(1, loop_count + 1):
        for cell in zip(*np.where(loops == n)):
            (r, c) = cell
            edge_l = ((r, c - 1), (r, c))
            edge_r = ((r, c), (r, c + 1))
            edge_u = ((r - 1, c), (r, c))
            edge_d = ((r, c), (r + 1, c))
            edges = [edge_l, edge_r, edge_u, edge_d]
            for x in edges:
                if x in z3_vars and loops[x[0]] != loops[x[1]]:
                    loop_rules[n].append(z3_vars[x])
    # print(loop_rules)
    solver.add(And(*[Or(*rule) for rule in loop_rules]))


def print_masyu(puzzle, model, z3_vars):
    (height, width) = puzzle.shape
    for r in range(height):
        row = ""
        for c in range(width):
            t = puzzle[r][c]
            if t != 'B' and t != 'W':
                l_e = c != 0 and is_true(model[z3_vars[((r, c - 1), (r, c))]])
                r_e = c != width - 1 and is_true(model[z3_vars[((r, c), (r, c + 1))]])
                u_e = r != 0 and is_true(model[z3_vars[((r - 1, c), (r, c))]])
                d_e = r != height - 1 and is_true(model[z3_vars[((r, c), (r + 1, c))]])
                if u_e and d_e:
                    row = row + "│"
                elif r_e and d_e:
                    row = row + "┌"
                elif r_e and u_e:
                    row = row + "└"
                elif l_e and d_e:
                    row = row + "┐"
                elif l_e and u_e:
                    row = row + "┘"
                elif l_e and r_e:
                    row = row + "─"
                else:
                    row = row + t
            else:
                row = row + t
        print(row)


puzz_s = """..W.W.....
    ....W...B.
    ..B.B.W...
    ...W..W...
    B....W...W
    ..W....W..
    ..B...W...
    W...B....W
    ......WW..
    ..B......B"""

puzz = np.array([list(s.strip()) for s in puzz_s.replace("\r\n", "\n").split("\n")])

p_vars = {}

for edge in grid_edges(puzz):
    p_vars[edge] = Bool(str(edge))

s = Solver()

coors = [(r, c) for r in range(puzz.shape[0]) for c in range(puzz.shape[1])]
path_constraints(s, coors, p_vars)

white = np.where(puzz == 'W')
white_pearl_constraints(s, zip(*white), p_vars)

black = np.where(puzz == 'B')
black_pearl_constraints(s, zip(*black), p_vars)

while s.check() == sat:
    m = s.model()
    print_masyu(puzz, m, p_vars)
    if not test_single_loop(puzz, m, p_vars):
        print("Coalescing islands...")
        coalesce_islands_constraints(puzz, s, m, p_vars)
    else:
        break