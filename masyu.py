from z3 import *

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

puzzle = [list(s.strip()) for s in puzz_s.replace("\r\n", "\n").split("\n")]

width = len(puzzle[0])
height = len(puzzle)

s = Solver()

L = [[Bool('L_r%d_c%d' % (r, c)) for c in range(width)] for r in range(height)]
R = [[Bool('R_r%d_c%d' % (r, c)) for c in range(width)] for r in range(height)]
U = [[Bool('U_r%d_c%d' % (r, c)) for c in range(width)] for r in range(height)]
D = [[Bool('D_r%d_c%d' % (r, c)) for c in range(width)] for r in range(height)]

# U for a cell must be equal to D of the cell above , etc:
for r in range(height):
    for c in range(width):
        if r != 0:
            s.add(U[r][c] == D[r - 1][c])
        if r != height - 1:
            s.add(D[r][c] == U[r + 1][c])
        if c != 0:
            s.add(L[r][c] == R[r][c - 1])
        if c != width - 1:
            s.add(R[r][c] == L[r][c + 1])

# Encode constraints for cell contents
for r in range(height):
    for c in range(width):
        v = puzzle[r][c]
        rules = []
        # White circle - straight path, turn before / after
        if v == 'W':
            # Horizontal
            if c != 0 and c != width - 1:
                rules.append(And(L[r][c],
                                 R[r][c],
                                 Not(U[r][c]),
                                 Not(D[r][c]),
                                 Or(U[r][c - 1], D[r][c - 1], U[r][c + 1], D[r][c + 1])))
            # Vertical
            if r != 0 and r != height - 1:
                rules.append(And(Not(L[r][c]),
                                 Not(R[r][c]),
                                 U[r][c],
                                 D[r][c],
                                 Or(L[r - 1][c], R[r - 1][c], L[r + 1][c], R[r + 1][c])))
            # If neither, then add unsatisfiable condition
            if len(rules) == 0:
                print("uhoh")
                rules.append(L[r][c] != L[r][c])
        # Black circle - turn, straight before / after
        elif v == 'B':
            # Handle each of 4 orientations separately
            if c != 0 and r != 0:
                rules.append(And(L[r][c],
                                 Not(R[r][c]),
                                 U[r][c],
                                 Not(D[r][c]),
                                 L[r][c - 1],
                                 U[r - 1][c]))
            if c != width - 1 and r != 0:
                rules.append(And(Not(L[r][c]),
                                 R[r][c],
                                 U[r][c],
                                 Not(D[r][c]),
                                 R[r][c + 1],
                                 U[r - 1][c]))
            if c != 0 and r != height - 1:
                rules.append(And(L[r][c],
                                 Not(R[r][c]),
                                 Not(U[r][c]),
                                 D[r][c],
                                 L[r][c - 1],
                                 D[r + 1][c]))
            if c != width - 1 and r != height - 1:
                rules.append(And(Not(L[r][c]),
                                 R[r][c],
                                 Not(U[r][c]),
                                 D[r][c],
                                 R[r][c + 1],
                                 D[r + 1][c]))
            # Black cell ALWAYS sat, no need to include dummy case
        # Empty, all possible paths
        else:
            rules.append(And(L[r][c], R[r][c], Not(U[r][c]), Not(D[r][c])))
            rules.append(And(L[r][c], Not(R[r][c]), U[r][c], Not(D[r][c])))
            rules.append(And(L[r][c], Not(R[r][c]), Not(U[r][c]), D[r][c]))
            rules.append(And(Not(L[r][c]), R[r][c], U[r][c], Not(D[r][c])))
            rules.append(And(Not(L[r][c]), R[r][c], Not(U[r][c]), D[r][c]))
            rules.append(And(Not(L[r][c]), Not(R[r][c]), U[r][c], D[r][c]))
            rules.append(And(Not(L[r][c]), Not(R[r][c]), Not(U[r][c]), Not(D[r][c])))
        s.add(Or(*rules))

for r in range(height):
    s.add(L[r][0] == False)
    s.add(R[r][width - 1] == False)
for c in range(width):
    s.add(U[0][c] == False)
    s.add(D[height - 1][c] == False)

print(s.check())
m = s.model()

# Print path
for r in range(height):
    row = ""
    for c in range(width):
        t = puzzle[r][c]
        if t != "W" and t != "B":
            tl = (True if str(m[L[r][c]]) == "True" else False)
            tr = (True if str(m[R[r][c]]) == "True" else False)
            tu = (True if str(m[U[r][c]]) == "True" else False)
            td = (True if str(m[D[r][c]]) == "True" else False)
            if tu and td:
                row = row + "│"
            elif tr and td:
                row = row + "┌"
            elif tr and tu:
                row = row + "└"
            elif tl and td:
                row = row + "┐"
            elif tl and tu:
                row = row + "┘"
            elif tl and tr:
                row = row + "─"
            else:
                row = row + t
        else:
            row = row + t
    print(row)
