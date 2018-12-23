from z3 import *


grid = [[Int("x_%s_%s" % (i+1, j+1))
         for j in range(9)]
        for i in range(9)]
cell_c = [And(1 <= grid[i][j], grid[i][j] <= 9) for i in range(9) for j in range(9)]

row_c = [Distinct(grid[i]) for i in range(9)]
col_c = [Distinct([grid[i][j] for i in range(9)]) for j in range(9)]
sq_c = [Distinct([ grid[3*i0 + i][3*j0 + j] for i in range(3) for j in range(3)]) for i0 in range(3) for j0 in range(3)]

sudoku_c = cell_c + row_c + col_c + sq_c

# sudoku instance, we use '0' for empty cells
instance = ((0,0,0,0,9,4,0,3,0),
            (0,0,0,5,1,0,0,0,7),
            (0,8,9,0,0,0,0,4,0),
            (0,0,0,0,0,0,2,0,8),
            (0,6,0,2,0,1,0,5,0),
            (1,0,2,0,0,0,0,0,0),
            (0,7,0,0,0,0,5,2,0),
            (9,0,0,0,6,5,0,0,0),
            (0,4,0,9,7,0,0,0,0))

instance_c = [If(instance[i][j] == 0, True, grid[i][j] == instance[i][j]) for i in range(9) for j in range(9)]

s = Solver()
s.add(sudoku_c + instance_c)
if s.check() == sat:
    m = s.model()
    r = [[m.evaluate(grid[i][j]) for j in range(9)] for i in range(9)]
    print_matrix(r)
else:
    print("Failed to solve")