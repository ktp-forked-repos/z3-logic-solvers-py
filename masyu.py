from z3 import *
from z3_helpers import *
import numpy as np
import itertools


def path_constraints(solver, cells, z3_vars):
    """Add path constraints for each cell - either 2 edges or none."""
    for (r, c) in cells:
        edge_c = []
        edge_l = ((r, c - 1), (r, c))
        edge_r = ((r, c), (r, c + 1))
        edge_u = ((r - 1, c), (r, c))
        edge_d = ((r, c), (r + 1, c))
        edges = [edge_l, edge_r, edge_u, edge_d]
        # Select out valid edges
        valid = set()
        for x in edges:
            if x in z3_vars:
                valid.add(x)
        # Path not going through this cell is always a possibility
        edge_c.append(And(*[Not(z3_vars[x]) for x in valid]))
        # Add all pairs of entry / exit edges
        for pair in itertools.combinations(valid, 2):
            rule = []
            rule.extend([z3_vars[x] for x in pair])
            rule.extend([Not(z3_vars[x]) for x in valid - set(pair)])
            edge_c.append(And(*rule))
        solver.append(Or(*edge_c))


def white_pearl_constraints(solver, pearls, z3_vars):
    """Add white pearl path constraints - straight through, turn on at least one side."""
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
            # If we can make a turn, then add this to our constraints
            if len(turn_c) != 0:
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
            # If we can make a turn, then add this to our constraints
            if len(turn_c) != 0:
                straight_c.append(Or(*turn_c))
                pearl_c.append(And(*straight_c))
            pearl_c.append(And(*straight_c))
        # If we have a possible path through the cell, add it
        if len(pearl_c) != 0:
            solver.add(Or(*pearl_c))
        # Otherwise, add unsatisfiable constraint for impossible pearl
        else:
            solver.add(And(False))


def black_pearl_constraints(solver, pearls, z3_vars):
    """Add black pearl path constraints - turn on pearl, straight on both sides."""
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
        # Explicitly enumerate all 4 possible paths
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
        # No need to check if a path exists; black pearl always satisfiable in standard masyu
        solver.add(Or(*pearl_c))


def coalesce_loops_constraints(puzzle, solver, model, z3_vars):
    """Given an incorrect model with multiple loops, add constraints to the puzzle to merge adjacent loops."""

    # Find all loops
    loops = np.zeros(puzzle.shape)
    loop_count = 0
    for k in z3_vars.keys():
        # If the cell is on the path, then it is part of a loop - flag it
        if is_true(model[z3_vars[k]]):
            loops[k[0]] = -1
            loops[k[1]] = -1
    while -1 in loops:
        # Argmin pulls out first cell with no loop found
        loop_count += 1
        start_cell = np.unravel_index(np.argmin(loops), puzzle.shape)
        loops[traverse_path(puzzle, start_cell, model, z3_vars)] = loop_count

    # Single loop puzzle, no need to add constraints
    if loop_count == 1:
        return

    loop_rules = [[]] * loop_count
    # Iterate over all loops
    for n in range(1, loop_count + 1):
        # Extract cells in the current loop
        for cell in zip(*np.where(loops == n)):
            (r, c) = cell
            edge_l = ((r, c - 1), (r, c))
            edge_r = ((r, c), (r, c + 1))
            edge_u = ((r - 1, c), (r, c))
            edge_d = ((r, c), (r + 1, c))
            edges = [edge_l, edge_r, edge_u, edge_d]
            for x in edges:
                # If the edge points to outside the loop, it is a possible edge to expand the loop
                if x in z3_vars and loops[x[0]] != loops[x[1]]:
                    loop_rules[n - 1].append(z3_vars[x])
    # Every loop must be expanded, by at least one edge
    solver.add(And(*[Or(*rule) for rule in loop_rules]))


def test_single_loop(puzzle, model, z3_vars):
    """Check whether the given model has a single loop."""
    # Find all cells that are on the path
    on_path = np.zeros(puzzle.shape, dtype="bool")
    for k in z3_vars.keys():
        if is_true(model[z3_vars[k]]):
            on_path[k[0]] = 1
            on_path[k[1]] = 1
    # Arbitrary start cell on path
    start = np.unravel_index(np.argmax(on_path), puzzle.shape)
    # Set all reachable cells on the path to 0
    on_path[traverse_path(puzzle, start, model, z3_vars)] = 0
    # Return if we reached all cells
    return not np.any(on_path)


def print_masyu(puzzle, model, z3_vars):
    res = ""
    (height, width) = puzzle.shape
    for r in range(height):
        row = ""
        for c in range(width):
            t = puzzle[r][c]
            if t != 'B' and t != 'W':
                # Check all edges
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
        res += row + "\n"
    return res


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
    print(print_masyu(puzz, m, p_vars))
    if not test_single_loop(puzz, m, p_vars):
        print("Coalescing loops...")
        coalesce_loops_constraints(puzz, s, m, p_vars)
    else:
        break