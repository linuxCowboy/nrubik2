#!/usr/bin/env python
#
# profiling_solver for nrubik2
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
import timeit

tests_per_run = 10
runs = 3
scramble_moves = 17

if sys.argv[1:]:
    if sys.argv[1] == '--help':
        print("\n    %s [tests_per_run{%d} [runs{%d} [scramble_moves{%d}]]]\n" % \
                (sys.argv[0], tests_per_run, runs, scramble_moves))
        sys.exit(0)

if sys.argv[1:]:
    tests_per_run = int(sys.argv[1])

if sys.argv[2:]:
    runs = int(sys.argv[2])

if sys.argv[3:]:
    scramble_moves = int(sys.argv[3])

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

functions = [turn_top, turn_top_rev, turn_bottom, turn_bottom_rev,\
             turn_left, turn_left_rev, turn_right, turn_right_rev,\
             turn_front, turn_front_rev, turn_back, turn_back_rev]

def search_edge(cubie1, cubie2):
    found = []

    edges = (
    ((0, 0, 1), (5, 0, 1)),
    ((0, 1, 0), (2, 0, 1)),
    ((0, 1, 2), (3, 0, 1)),
    ((0, 2, 1), (4, 0, 1)),
    ((1, 0, 1), (4, 2, 1)),
    ((1, 1, 0), (2, 2, 1)),
    ((1, 1, 2), (3, 2, 1)),
    ((1, 2, 1), (5, 2, 1)),
    ((2, 0, 1), (0, 1, 0)),
    ((2, 1, 0), (5, 1, 2)),
    ((2, 1, 2), (4, 1, 0)),
    ((2, 2, 1), (1, 1, 0)),
    ((3, 0, 1), (0, 1, 2)),
    ((3, 1, 0), (4, 1, 2)),
    ((3, 1, 2), (5, 1, 0)),
    ((3, 2, 1), (1, 1, 2)),
    ((4, 0, 1), (0, 2, 1)),
    ((4, 1, 0), (2, 1, 2)),
    ((4, 1, 2), (3, 1, 0)),
    ((4, 2, 1), (1, 0, 1)),
    ((5, 0, 1), (0, 0, 1)),
    ((5, 1, 0), (3, 1, 2)),
    ((5, 1, 2), (2, 1, 0)),
    ((5, 2, 1), (1, 2, 1)))

    for c in range(24):
        i, j, k = edges[c][0]
        l, m, n = edges[c][1]

        if cube[i][j][k] == cubie1 and cube[l][m][n] == cubie2:
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
        funcs = [4, 5]
        if cubie[1] == 0:
            funcs += [0, 1]
        elif cubie[1] == 1:
            if cubie[2] == 0:
                funcs += [10, 11]
            else:
                funcs += [8, 9]
        else:
            funcs += [2, 3]

    elif cubie[0] == 3:
        funcs = [6, 7]
        if cubie[1] == 0:
            funcs += [0, 1]
        elif cubie[1] == 1:
            if cubie[2] == 0:
                funcs += [8, 9]
            else:
                funcs += [10, 11]
        else:
            funcs += [2, 3]

    elif cubie[0] == 4:
        funcs = [8, 9]
        if cubie[1] == 0:
            funcs += [0, 1]
        elif cubie[1] == 1:
            if cubie[2] == 0:
                funcs += [4, 5]
            else:
                funcs += [6, 7]
        else:
            funcs += [2, 3]

    elif cubie[0] == 5:
        funcs = [10, 11]
        if cubie[1] == 0:
            funcs += [0, 1]
        elif cubie[1] == 1:
            if cubie[2] == 0:
                funcs += [6, 7]
            else:
                funcs += [4, 5]
        else:
            funcs += [2, 3]

    random.shuffle(funcs)

    functions[funcs[0]]()

def solve():
    global cube

    for i in range(scramble_moves):
        functions[random.randint(0, 11)]()

    while not (cube[0][2][1] == cube[0][1][2] == cube[0][0][1] == cube[0][1][0]\
                             == solved_cube[0][1][1] and
               cube[4][0][1] == solved_cube[4][0][1] and
               cube[3][0][1] == solved_cube[3][0][1] and
               cube[5][0][1] == solved_cube[5][0][1] and
               cube[2][0][1] == solved_cube[2][0][1]):

        i = 0
        while not (cube[0][2][1] == solved_cube[0][2][1] and cube[4][0][1] == solved_cube[4][0][1]):
            if i == 0:
                backup_cube = copy.deepcopy(cube)

            elif i == search_deep:
                cube = copy.deepcopy(backup_cube)
                i = 0

            cubie = search_edge(solved_cube[0][2][1], solved_cube[4][0][1])

            move_edge(cubie)
            i += 1

        i = 0
        while not (cube[0][1][2] == solved_cube[0][1][2] and cube[3][0][1] == solved_cube[3][0][1]):
            if i == 0:
                backup_cube = copy.deepcopy(cube)

            elif i == search_deep:
                cube = copy.deepcopy(backup_cube)
                i = 0

            cubie = search_edge(solved_cube[0][1][2], solved_cube[3][0][1])

            move_edge(cubie)
            i += 1

        i = 0
        while not (cube[0][0][1] == solved_cube[0][0][1] and cube[5][0][1] == solved_cube[5][0][1]):
            if i == 0:
                backup_cube = copy.deepcopy(cube)

            elif i == search_deep:
                cube = copy.deepcopy(backup_cube)
                i = 0

            cubie = search_edge(solved_cube[0][0][1], solved_cube[5][0][1])

            move_edge(cubie)
            i += 1

        i = 0
        while not (cube[0][1][0] == solved_cube[0][1][0] and cube[2][0][1] == solved_cube[2][0][1]):
            if i == 0:
                backup_cube = copy.deepcopy(cube)

            elif i == search_deep:
                cube = copy.deepcopy(backup_cube)
                i = 0

            cubie = search_edge(solved_cube[0][1][0], solved_cube[2][0][1])

            move_edge(cubie)
            i += 1

if __name__ == '__main__':
    print("Run %d x %d tests with %d scramble moves... (search deep 4 - 10)" % (runs, tests_per_run, scramble_moves))

    for i in range(4, 11):
        search_deep = i

        l = timeit.repeat('solve()', number=tests_per_run, repeat=runs, setup="from __main__ import solve")

        print("%2d:  " % i + "  ".join("%.2f" % t for t in l))

