#!/usr/bin/env python
#
# profiling_solver for nrubik2:
#
#     profile search_deep_2 and reset_point
#
# Copyright (c) 2018 LinuxCowboy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

import sys
import copy
import random
import time

runs              = 3
search_deep_start = 4
search_deep_end   = 14
reset_point       = 400
threshold         = 0

scramble_moves    = 17
search_deep_1     = 6

if sys.argv[1:]:
    if sys.argv[1] == '--help':
        print("\n    %s [runs{%d} [search_deep_start{%d} [search_deep_end{%d} [reset_point{%d} [threshold{%d}]]]]]\n" % \
                (sys.argv[0], runs, search_deep_start, search_deep_end, reset_point, threshold))
        sys.exit(0)
    else:
        runs          = int(sys.argv[1])

if sys.argv[2:]:
    search_deep_start = int(sys.argv[2])

if sys.argv[3:]:
    search_deep_end   = int(sys.argv[3])

if sys.argv[4:]:
    reset_point       = int(sys.argv[4])

if sys.argv[5:]:
    threshold         = int(sys.argv[5])

solved_cube = [
    [
        ['W', 'W', 'W'],
        ['W', 'W', 'W'],
        ['W', 'W', 'W'],
    ],
    [
        ['Y', 'Y', 'Y'],
        ['Y', 'Y', 'Y'],
        ['Y', 'Y', 'Y'],
    ],
    [
        ['M', 'M', 'M'],
        ['M', 'M', 'M'],
        ['M', 'M', 'M'],
    ],
    [
        ['R', 'R', 'R'],
        ['R', 'R', 'R'],
        ['R', 'R', 'R'],
    ],
    [
        ['G', 'G', 'G'],
        ['G', 'G', 'G'],
        ['G', 'G', 'G'],
    ],
    [
        ['B', 'B', 'B'],
        ['B', 'B', 'B'],
        ['B', 'B', 'B'],
    ],
]

cube = copy.deepcopy(solved_cube)

def turn_top():
    backup_cube = copy.deepcopy(cube)
    # turn top only
    for i in range(3):
        for j in range(3):
            cube[0][i][j] = backup_cube[0][2-j][i]
    # turn rest
    for i, j in [(2, 4), (3, 5), (4, 3), (5, 2)]:
        for k in range(3):
            cube[i][0][k] = backup_cube[j][0][k]

def turn_top_rev():
    backup_cube = copy.deepcopy(cube)
    # turn top only
    for i in range(3):
        for j in range(3):
            cube[0][j][i] = backup_cube[0][i][2-j]
    # turn rest
    for i, j in [(2, 5), (3, 4), (4, 2), (5, 3)]:
        for k in range(3):
            cube[i][0][k] = backup_cube[j][0][k]

def turn_bottom():
    backup_cube = copy.deepcopy(cube)
    # turn bottom only
    for i in range(3):
        for j in range(3):
            cube[1][i][j] = backup_cube[1][2-j][i]
    # turn rest
    for i, j in [(2, 5), (3, 4), (4, 2), (5, 3)]:
        for k in range(3):
            cube[i][2][k] = backup_cube[j][2][k]

def turn_bottom_rev():
    backup_cube = copy.deepcopy(cube)
    # turn bottom only
    for i in range(3):
        for j in range(3):
            cube[1][j][i] = backup_cube[1][i][2-j]
    # turn rest
    for i, j in [(2, 4), (3, 5), (4, 3), (5, 2)]:
        for k in range(3):
            cube[i][2][k] = backup_cube[j][2][k]

def turn_left():
    backup_cube = copy.deepcopy(cube)
    # turn left only
    for i in range(3):
        for j in range(3):
            cube[2][i][j] = backup_cube[2][2-j][i]
    # change top-part
    for i in range(3):
        cube[0][i][0] = backup_cube[5][2-i][2]
    # change bottom-part
    for i in range(3):
        cube[1][i][0] = backup_cube[4][i][0]
    # change front-part
    for i in range(3):
        cube[4][i][0] = backup_cube[0][i][0]
    # change back-part
    for i in range(3):
        cube[5][i][2] = backup_cube[1][2-i][0]

def turn_left_rev():
    backup_cube = copy.deepcopy(cube)
    # turn left only
    for i in range(3):
        for j in range(3):
            cube[2][j][i] = backup_cube[2][i][2-j]
    # change top-part
    for i in range(3):
        cube[0][i][0] = backup_cube[4][i][0]
    # change bottom-part
    for i in range(3):
        cube[1][i][0] = backup_cube[5][2-i][2]
    # change front-part
    for i in range(3):
        cube[4][i][0] = backup_cube[1][i][0]
    # change back-part
    for i in range(3):
        cube[5][i][2] = backup_cube[0][2-i][0]

def turn_right():
    backup_cube = copy.deepcopy(cube)
    # turn right only
    for i in range(3):
        for j in range(3):
            cube[3][i][j] = backup_cube[3][2-j][i]
    # change top-part
    for i in range(3):
        cube[0][i][2] = backup_cube[4][i][2]
    # change bottom-part
    for i in range(3):
        cube[1][i][2] = backup_cube[5][2-i][0]
    # change front-part
    for i in range(3):
        cube[4][i][2] = backup_cube[1][i][2]
    # change back-part
    for i in range(3):
        cube[5][i][0] = backup_cube[0][2-i][2]

def turn_right_rev():
    backup_cube = copy.deepcopy(cube)
    # turn right only
    for i in range(3):
        for j in range(3):
            cube[3][j][i] = backup_cube[3][i][2-j]
    # change top-part
    for i in range(3):
        cube[0][i][2] = backup_cube[5][2-i][0]
    # change bottom-part
    for i in range(3):
        cube[1][i][2] = backup_cube[4][i][2]
    # change front-part
    for i in range(3):
        cube[4][i][2] = backup_cube[0][i][2]
    # change back-part
    for i in range(3):
        cube[5][i][0] = backup_cube[1][2-i][2]

def turn_front():
    backup_cube = copy.deepcopy(cube)
    # turn front only
    for i in range(3):
        for j in range(3):
            cube[4][i][j] = backup_cube[4][2-j][i]
    # change top-part
    for i in range(3):
        cube[0][2][i] = backup_cube[2][2-i][2]
    # change bottom-part
    for i in range(3):
        cube[1][0][i] = backup_cube[3][2-i][0]
    # change left-part
    for i in range(3):
        cube[2][i][2] = backup_cube[1][0][i]
    # change right-part
    for i in range(3):
        cube[3][i][0] = backup_cube[0][2][i]

def turn_front_rev():
    backup_cube = copy.deepcopy(cube)
    # turn front only
    for i in range(3):
        for j in range(3):
            cube[4][j][i] = backup_cube[4][i][2-j]
    # change top-part
    for i in range(3):
        cube[0][2][i] = backup_cube[3][i][0]
    # change bottom-part
    for i in range(3):
        cube[1][0][i] = backup_cube[2][i][2]
    # change left-part
    for i in range(3):
        cube[2][i][2] = backup_cube[0][2][2-i]
    # change right-part
    for i in range(3):
        cube[3][i][0] = backup_cube[1][0][2-i]

def turn_back():
    backup_cube = copy.deepcopy(cube)
    # turn back only
    for i in range(3):
        for j in range(3):
            cube[5][i][j] = backup_cube[5][2-j][i]
    # change top-part
    for i in range(3):
        cube[0][0][i] = backup_cube[3][i][2]
    # change bottom-part
    for i in range(3):
        cube[1][2][i] = backup_cube[2][i][0]
    # change left-part
    for i in range(3):
        cube[2][i][0] = backup_cube[0][0][2-i]
    # change right-part
    for i in range(3):
        cube[3][i][2] = backup_cube[1][2][2-i]

def turn_back_rev():
    backup_cube = copy.deepcopy(cube)
    # turn back only
    for i in range(3):
        for j in range(3):
            cube[5][j][i] = backup_cube[5][i][2-j]
    # change top-part
    for i in range(3):
        cube[0][0][i] = backup_cube[2][2-i][0]
    # change bottom-part
    for i in range(3):
        cube[1][2][i] = backup_cube[3][2-i][2]
    # change left-part
    for i in range(3):
        cube[2][i][0] = backup_cube[1][2][i]
    # change right-part
    for i in range(3):
        cube[3][i][2] = backup_cube[0][0][i]

def turn_middle():
    backup_cube = copy.deepcopy(cube)
    for i in range(3):
        cube[0][i][1] = backup_cube[4][i][1]
        cube[4][i][1] = backup_cube[1][i][1]
        cube[1][i][1] = backup_cube[5][2-i][1]
        cube[5][i][1] = backup_cube[0][2-i][1]

def turn_equator():
    backup_cube = copy.deepcopy(cube)
    for i, j in [(2, 4), (4, 3), (3, 5), (5, 2)]:
        for k in range(3):
            cube[i][1][k] = backup_cube[j][1][k]

def turn_standing():
    backup_cube = copy.deepcopy(cube)
    for k in range(3):
        cube[0][1][k] = backup_cube[2][2-k][1]
        cube[2][k][1] = backup_cube[1][1][k]
        cube[1][1][k] = backup_cube[3][2-k][1]
        cube[3][k][1] = backup_cube[0][1][k]

def move_x():
    turn_right()
    turn_middle()
    turn_left_rev()

def move_y():
    turn_top()
    turn_equator()
    turn_bottom_rev()

def move_z():
    turn_front()
    turn_standing()
    turn_back_rev()

functions = (turn_top, turn_top_rev, turn_bottom, turn_bottom_rev,
             turn_left, turn_left_rev, turn_right, turn_right_rev,
             turn_front, turn_front_rev, turn_back, turn_back_rev)

def search_edge(cubie1, cubie2):
    found = []

    edges = (((0, 0, 1), (5, 0, 1)),
             ((0, 1, 0), (2, 0, 1)),
             ((0, 1, 2), (3, 0, 1)),
             ((0, 2, 1), (4, 0, 1)),

             ((1, 0, 1), (4, 2, 1)),
             ((1, 1, 0), (2, 2, 1)),
             ((1, 1, 2), (3, 2, 1)),
             ((1, 2, 1), (5, 2, 1)),

             ((2, 1, 0), (5, 1, 2)),
             ((3, 1, 0), (4, 1, 2)),
             ((4, 1, 0), (2, 1, 2)),
             ((5, 1, 0), (3, 1, 2)))

    for e in range(12):
        i, j, k = edges[e][0]
        l, m, n = edges[e][1]

        if (cube[i][j][k] == cubie1 and cube[l][m][n] == cubie2 or
            cube[i][j][k] == cubie2 and cube[l][m][n] == cubie1):
                found.extend((i, j, k))
                break

    return found

def move_edge(cubie):
    if cubie[0] == 0:
        funcs = [0, 1]

        if cubie[1] == 0:
            funcs += [10, 11]

        elif cubie[1] == 1:
            if cubie[2] == 0:
                funcs += [4, 5]
            else:
                funcs += [6, 7]
        else:
            funcs += [8, 9]

    elif cubie[0] == 1:
        funcs = [2, 3]

        if cubie[1] == 0:
            funcs += [8, 9]

        elif cubie[1] == 1:
            if cubie[2] == 0:
                funcs += [4, 5]
            else:
                funcs += [6, 7]
        else:
            funcs += [10, 11]

    elif cubie[0] == 2:
        funcs = [4, 5, 10 ,11]

    elif cubie[0] == 3:
        funcs = [6, 7, 8, 9]

    elif cubie[0] == 4:
        funcs = [8, 9, 4, 5]

    elif cubie[0] == 5:
        funcs = [10, 11, 6, 7]

    random.shuffle(funcs)

    functions[funcs[0]]()

def solve_1():
    global cube, solve_moves_1, solve_time_1_restart

    restart_time = time.time()

    edges = (((0, 2, 1), (4, 0, 1)),
             ((0, 1, 2), (3, 0, 1)),
             ((0, 0, 1), (5, 0, 1)),
             ((0, 1, 0), (2, 0, 1)))

    i = 0
    while cube[0][1][1] != solved_cube[0][1][1]:
        if i < 3:
            move_x()
        else:
            move_z()
        i += 1

    while cube[4][1][1] != solved_cube[4][1][1]:
            move_y()

    while not (cube[0][2][1] == cube[0][1][2] == cube[0][0][1] == cube[0][1][0]\
                             == solved_cube[0][1][1] and

               cube[2][0][1] == solved_cube[2][0][1] and
               cube[3][0][1] == solved_cube[3][0][1] and
               cube[4][0][1] == solved_cube[4][0][1] and
               cube[5][0][1] == solved_cube[5][0][1]):

        for e in range(4):
            i, j, k = edges[e][0]
            l, m, n = edges[e][1]

            c = 0
            while not (cube[i][j][k] == solved_cube[i][j][k] and
                       cube[l][m][n] == solved_cube[l][m][n]):
                            if c == 0:
                                backup_cube = copy.deepcopy(cube)

                            elif c == search_deep_1:
                                cube = copy.deepcopy(backup_cube)
                                c = 0

                            cubie = search_edge(solved_cube[i][j][k], solved_cube[l][m][n])

                            move_edge(cubie)
                            c += 1
                            solve_moves_1 += 1

    solve_time_1_restart += time.time() - restart_time

def search_corner(cubie1, cubie2):
    found = []

    corners = (((0, 2, 2), (3, 0, 0), (4, 0, 2)),
               ((0, 0, 2), (5, 0, 0), (3, 0, 2)),
               ((0, 0, 0), (2, 0, 0), (5, 0, 2)),
               ((0, 2, 0), (4, 0, 0), (2, 0, 2)),

               ((1, 0, 2), (4, 2, 2), (3, 2, 0)),
               ((1, 2, 2), (3, 2, 2), (5, 2, 0)),
               ((1, 2, 0), (5, 2, 2), (2, 2, 0)),
               ((1, 0, 0), (2, 2, 2), (4, 2, 0)))

    for c in range(8):
        i, j, k = corners[c][0]
        l, m, n = corners[c][1]
        o, p, q = corners[c][2]

        if (cube[i][j][k] == solved_cube[0][1][1] and cube[l][m][n] == cubie1 and cube[o][p][q] == cubie2 or
            cube[l][m][n] == solved_cube[0][1][1] and cube[o][p][q] == cubie1 and cube[i][j][k] == cubie2 or
            cube[o][p][q] == solved_cube[0][1][1] and cube[i][j][k] == cubie1 and cube[l][m][n] == cubie2):
                found.extend((i, j, k))
                break

    return found

def move_corner(cubie):
    if cubie[0] == 0:
        funcs = [0, 1]

        if cubie[1] == 0:
            funcs += [10, 11]
        else:
            funcs += [8, 9]
    else:
        funcs = [2, 3]

        if cubie[1] == 0:
            funcs += [8, 9]
        else:
            funcs += [10, 11]

    if cubie[2] == 0:
        funcs += [4, 5]
    else:
        funcs += [6, 7]

    random.shuffle(funcs)

    functions[funcs[0]]()

def solve_2(search_deep):
    global cube, solve_moves_2
    restart = True

    while restart:
        restart = False

        for c1, c2 in ((solved_cube[3][0][0], solved_cube[4][0][2]), (solved_cube[5][0][0], solved_cube[3][0][2]),\
                       (solved_cube[2][0][0], solved_cube[5][0][2]), (solved_cube[4][0][0], solved_cube[2][0][2])):
            i = moves = 0

            while not ((cube[4][2][2] == solved_cube[0][2][2] and cube[3][2][0] == c1 or
                        cube[3][2][0] == solved_cube[0][2][2] and cube[1][0][2] == c1 or
                        cube[1][0][2] == solved_cube[0][2][2] and cube[4][2][2] == c1) and

                       cube[0][1][2] == cube[0][0][1] == cube[0][1][0] == cube[0][2][1] == solved_cube[0][1][1] and

                       cube[3][0][1] == cube[3][1][1] and
                       cube[5][0][1] == cube[5][1][1] and
                       cube[2][0][1] == cube[2][1][1] and
                       cube[4][0][1] == cube[4][1][1] and

                       (c1 == solved_cube[3][0][0] or

                        c1 == solved_cube[5][0][0] and
                            cube[0][2][0] == solved_cube[0][2][0] and cube[4][0][0] == solved_cube[3][0][0] or

                        c1 == solved_cube[2][0][0] and
                            cube[0][2][0] == solved_cube[0][2][0] and cube[4][0][0] == solved_cube[5][0][0] and
                            cube[0][0][0] == solved_cube[0][0][0] and cube[2][0][0] == solved_cube[3][0][0] or

                        c1 == solved_cube[4][0][0] and
                            cube[0][2][0] == solved_cube[0][2][0] and cube[4][0][0] == solved_cube[2][0][0] and
                            cube[0][0][0] == solved_cube[0][0][0] and cube[2][0][0] == solved_cube[5][0][0] and
                            cube[0][0][2] == solved_cube[0][0][2] and cube[5][0][0] == solved_cube[3][0][0])):

                if i == 0:
                    backup_cube = copy.deepcopy(cube)

                elif i == search_deep:
                    cube = copy.deepcopy(backup_cube)
                    i = 0

                cubie = search_corner(c1, c2)

                move_corner(cubie)

                i += 1
                moves += 1
                solve_moves_2 += 1

                if not moves % reset_point:
                    solve_1()

                    restart = True
                    break

            if restart:
                break

            if cube[4][2][2] == solved_cube[0][2][2]:
                turn_bottom_rev()
                turn_right_rev()
                turn_bottom()
                turn_right()

                solve_moves_2 += 4

            elif cube[1][0][2] == solved_cube[0][2][2]:
                turn_right_rev()
                turn_bottom()
                turn_right()
                turn_bottom()
                turn_bottom()

                solve_moves_2 += 5

            if cube[3][2][0] == solved_cube[0][2][2] and cube[1][0][2] == c1:
                turn_right_rev()
                turn_bottom_rev()
                turn_right()

                solve_moves_2 += 3

            move_y()
            solve_moves_2 += 1

def solve():
    global cube, solve_moves_1, solve_moves_2, solve_time_1_restart

    print("Run %d test(s) with search deep %d - %d and reset point %d, threshold %d second(s)" % \
            (runs, search_deep_start, search_deep_end, reset_point, threshold))
    print("          search deep      edges    {restart}    corners  (moves / seconds)\n")

    for i in range(runs):
        for j in range(scramble_moves):
            functions[random.randint(0, 11)]()

        scrambled_cube = copy.deepcopy(cube)

        for sd in range(search_deep_start, search_deep_end + 1):
            solve_moves_1 = solve_moves_2 = 0

            cube = copy.deepcopy(scrambled_cube)

            solve_time_1 = time.time()
            solve_time_1_restart = 0
            solve_1()

            solve_time_2 = time.time()
            solve_time_1 = solve_time_2 - solve_time_1

            solve_2(sd)
            solve_time_2 = time.time() - solve_time_2

            if solve_time_2 > threshold:
                print("%3d.Run:       %2d      %5d / %.2f {%.2f}   %6d / %.2f" % \
                    (i + 1, sd, solve_moves_1, solve_time_1, solve_time_1_restart, solve_moves_2, solve_time_2))

        if search_deep_start != search_deep_end:
            print("")

if __name__ == '__main__':
    solve()

