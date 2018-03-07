#!/usr/bin/env python
#
# nrubik2 - ncurses based virtual rubik's cube
#
# Copyright (c) 2017 Caleb Butler
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

# lowercase chars for moves
up    = 'u'
down  = 'd'
left  = 'l'
right = 'r'
front = 'f'
back  = 'b'

## ruf rule rulez
middle   = 'm'  # r (but reversed: l!)
equator  = 'e'  # u (but reversed: d!)
standing = 's'  # f

cube_x = 'x'  # r
cube_y = 'y'  # u
cube_z = 'z'  # f

########################

undo   = 'KEY_BACKSPACE'
redo   = chr(10)
delete = 'KEY_DC'

reset  = 'KEY_HOME'
solve  = 'KEY_END'
layout = 'KEY_IC'
pause  = ' '
quit   = chr(27)

import curses
import copy
import random
import time

buf_undo = buf_redo = ""

class Cube:

    # mode 0: nrubik b/w  mode 1: nrubik  mode 2: nrubik2
    mode = 2

    looping = True
    pausing = True
    watch = 0
    time_last = time.time()

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
            ['R', 'R', 'R'],
            ['R', 'R', 'R'],
            ['R', 'R', 'R'],
        ],
        [
            ['M', 'M', 'M'],
            ['M', 'M', 'M'],
            ['M', 'M', 'M'],
        ],
        [
            ['B', 'B', 'B'],
            ['B', 'B', 'B'],
            ['B', 'B', 'B'],
        ],
        [
            ['G', 'G', 'G'],
            ['G', 'G', 'G'],
            ['G', 'G', 'G'],
        ],
    ]

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.stdscr.nodelay(True)
        curses.use_default_colors()
        curses.curs_set(False)

        self.cube = copy.deepcopy(self.solved_cube)

        if curses.has_colors():
            if self.mode <= 1:
                curses.init_pair(1, curses.COLOR_WHITE,   -1)
                curses.init_pair(2, curses.COLOR_YELLOW,  -1)
                curses.init_pair(3, curses.COLOR_MAGENTA, -1)
                curses.init_pair(4, curses.COLOR_RED,     -1)
                curses.init_pair(5, curses.COLOR_GREEN,   -1)
                curses.init_pair(6, curses.COLOR_BLUE,    -1)
            else:
                curses.init_pair(1, curses.COLOR_WHITE,   curses.COLOR_WHITE)
                curses.init_pair(2, curses.COLOR_YELLOW,  curses.COLOR_YELLOW)
                curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
                curses.init_pair(4, curses.COLOR_RED,     curses.COLOR_RED)
                curses.init_pair(5, curses.COLOR_GREEN,   curses.COLOR_GREEN)
                curses.init_pair(6, curses.COLOR_BLUE,    curses.COLOR_BLUE)
        else:
            self.mode = 0

    def helper(self):
        max_y, max_x = self.stdscr.getmaxyx()
        start_y = 2
        start_x = 2
        end_x   = 2 + 18

        head = "nrubik2 - An N-Curses Based, Virtual Rubik's Cube"
        self.stdscr.addstr(0, int(max_x / 2 - len(head) / 2 - 1), head)

        self.stdscr.addstr(start_y + 0,  start_x, "Keybindings:")

        self.stdscr.addstr(start_y + 2,  start_x, up + ","    + up.upper()    + " - Up")
        self.stdscr.addstr(start_y + 3,  start_x, down + ","  + down.upper()  + " - Down")
        self.stdscr.addstr(start_y + 4,  start_x, left + ","  + left.upper()  + " - Left")
        self.stdscr.addstr(start_y + 5,  start_x, right + "," + right.upper() + " - Right")
        self.stdscr.addstr(start_y + 6,  start_x, front + "," + front.upper() + " - Front")
        self.stdscr.addstr(start_y + 7,  start_x, back + ","  + back.upper()  + " - Back")

        self.stdscr.addstr(start_y + 9,  start_x, middle + ","   + middle.upper()   + " - Middle")
        self.stdscr.addstr(start_y + 10, start_x, equator + ","  + equator.upper()  + " - Equator")
        self.stdscr.addstr(start_y + 11, start_x, standing + "," + standing.upper() + " - Standing")

        self.stdscr.addstr(start_y + 13, start_x, cube_x + "," + cube_x.upper() + " - Cube X")
        self.stdscr.addstr(start_y + 14, start_x, cube_y + "," + cube_y.upper() + " - Cube Y")
        self.stdscr.addstr(start_y + 15, start_x, cube_z + "," + cube_z.upper() + " - Cube Z")

        self.stdscr.addstr(start_y + 7,  max_x - end_x, "Home - Reset")
        self.stdscr.addstr(start_y + 8,  max_x - end_x, "End  - Solve")

        self.stdscr.addstr(start_y + 10, max_x - end_x, "Backspace - Undo")
        self.stdscr.addstr(start_y + 11, max_x - end_x, "Enter     - Redo")
        self.stdscr.addstr(start_y + 12, max_x - end_x, "Delete    - Delete")

        self.stdscr.addstr(start_y + 14, max_x - end_x, "Insert - Layout")
        self.stdscr.addstr(start_y + 15, max_x - end_x, "Space  - Timer")
        self.stdscr.addstr(start_y + 16, max_x - end_x, "Escape - Quit")

    def solved(self):
        for i in range(6):
            if not self.cube[i][0][0] == self.cube[i][0][1] == self.cube[i][0][2]\
                == self.cube[i][1][0] == self.cube[i][1][1] == self.cube[i][1][2]\
                == self.cube[i][2][0] == self.cube[i][2][1] == self.cube[i][2][2]:
                    return False

        self.pausing = True
        return True

    def print_appeal(self):
        max_y, max_x = self.stdscr.getmaxyx()

        if len(buf_undo) == 0:
            appeal = "'Home' for Start!"
        else:
            appeal = "Solved. Congrats!"

        self.stdscr.addstr(int(max_y / 2 - 10), int(max_x / 2 - len(appeal) / 2 - 1), appeal)

    def display_cubie(self, y, x, cubie):
        colors = {'W': 1, 'Y': 2, 'M': 3, 'R': 4, 'G': 5, 'B': 6}

        if self.mode == 2:
            cub = cubie * 2
        else:
            cub = cubie

        if not curses.has_colors() or self.mode == 0:
            self.stdscr.addstr(int(y), int(x), cub)
        else:
            self.stdscr.addstr(int(y), int(x), cub, curses.color_pair(colors[cubie]))

    def display_cube(self):
        max_y, max_x = self.stdscr.getmaxyx()
        self.stdscr.scrollok(1)

        # nrubik + b/w
        if self.mode <= 1:
            # top
            for i, line in enumerate(self.cube[0]):
                for j in range(3):
                    self.display_cubie(max_y / 2 - 5 + i, max_x / 2 - 1 + j, line[j])
            # bottom
            for i, line in enumerate(self.cube[1]):
                for j in range(3):
                    self.display_cubie(max_y / 2 + 3 + i, max_x / 2 - 1 + j, line[j])
            # left
            for i, line in enumerate(self.cube[2]):
                for j in range(3):
                    self.display_cubie(max_y / 2 - 1 + i, max_x / 2 - 5 + j, line[j])
            # right
            for i, line in enumerate(self.cube[3]):
                for j in range(3):
                    self.display_cubie(max_y / 2 - 1 + i, max_x / 2 + 3 + j, line[j])
            # front
            for i, line in enumerate(self.cube[4]):
                for j in range(3):
                    self.display_cubie(max_y / 2 - 1 + i, max_x / 2 - 1 + j, line[j])
            # back
            for i, line in enumerate(self.cube[5]):
                for j in range(3):
                    self.display_cubie(max_y / 2 - 6 + i, max_x / 2 + 4 + j, line[j])
        # nrubik2
        else:
            # bars
            self.stdscr.addstr(int(max_y / 2 - 9), int(max_x / 2 - 1),  " __________________")
            self.stdscr.addstr(int(max_y / 2 - 8), int(max_x / 2 + 17), "||")
            self.stdscr.addstr(int(max_y / 2 - 7), int(max_x / 2 - 10), "______  ||  ______")
            self.stdscr.addstr(int(max_y / 2 - 6), int(max_x / 2 - 7),  "___......___")
            self.stdscr.addstr(int(max_y / 2 - 5), int(max_x / 2 - 12), "|   /___......___\\   |")
            self.stdscr.addstr(int(max_y / 2 - 4), int(max_x / 2 - 12), "|  /    ......    \\  |")
            self.stdscr.addstr(int(max_y / 2 - 3), int(max_x / 2 - 12), "| ||   +  ||  +   || |")
            self.stdscr.addstr(int(max_y / 2 - 1), int(max_x / 2 - 14), "--......--......--......--")
            self.stdscr.addstr(int(max_y / 2 + 1), int(max_x / 2 - 12), "| ||   +  ||  +   || |")
            self.stdscr.addstr(int(max_y / 2 + 2), int(max_x / 2 - 12), "|  \\ ___......___ /  |")
            self.stdscr.addstr(int(max_y / 2 + 3), int(max_x / 2 - 12), "|   \\___......___/   |")
            self.stdscr.addstr(int(max_y / 2 + 4), int(max_x / 2 - 10), "______  ||  ______")
            self.stdscr.addstr(int(max_y / 2 + 5), int(max_x / 2 - 2),  "||")

            # top
            for i, line in enumerate(self.cube[0]):
                for j in range(3):
                    self.display_cubie(max_y / 2 - 6 + i, max_x / 2 - 4 + (j*2),      line[j])
            # bottom
            for i, line in enumerate(self.cube[1]):
                for j in range(3):
                    self.display_cubie(max_y / 2 + 2 + i, max_x / 2 - 4 + (j*2),      line[j])
            # left
            for i, line in enumerate(self.cube[2]):
                for j in range(3):
                    self.display_cubie(max_y / 2 - 2 + i, max_x / 2 - 12 + (j*2),     line[j])
            # right
            for i, line in enumerate(self.cube[3]):
                for j in range(3):
                    self.display_cubie(max_y / 2 - 2 + i, max_x / 2 + 4 + (j*2),      line[j])
            # front
            for i, line in enumerate(self.cube[4]):
                for j in range(3):
                    self.display_cubie(max_y / 2 - 2 + i, max_x / 2 - 4 + (j*2),      line[j])
            # back
            for i, line in enumerate(self.cube[5]):
                for j in range(3):
                    self.display_cubie(max_y / 2 - 7 + i, max_x / 2 + 15 + (4-(2*j)), line[j])

            # mirror
            self.display_cubie(max_y / 2 - 6, max_x / 2 + 8,  self.cube[5][0][0])
            self.display_cubie(max_y / 2 - 8, max_x / 2 - 2,  self.cube[5][0][1])
            self.display_cubie(max_y / 2 - 6, max_x / 2 - 12, self.cube[5][0][2])

            self.display_cubie(max_y / 2 - 1, max_x / 2 + 12, self.cube[5][1][0])
            self.display_cubie(max_y / 2 - 1, max_x / 2 - 16, self.cube[5][1][2])

            self.display_cubie(max_y / 2 + 4, max_x / 2 + 8,  self.cube[5][2][0])
            self.display_cubie(max_y / 2 + 6, max_x / 2 - 2,  self.cube[5][2][1])
            self.display_cubie(max_y / 2 + 4, max_x / 2 - 12, self.cube[5][2][2])

        # trace redo
        max = int((max_x - 12 - 6) / 2 * 2)
        buf = buf_redo[::-1]
        if len(buf) > max:
            buf = buf[:max]
            buf += " ...  "
        self.stdscr.addstr(int(max_y / 2 + 6 + 2), 0, "Redo ({:.0f}):{:s}".format(len(buf_redo) / 2, buf))

        # trace undo
        max = int((max_x + max_x / 2 - 14 - 4 + 2) / 2 * 2)
        buf = buf_undo[-max:]
        if len(buf_undo) > max:
            buf = "... " + buf
        self.stdscr.addstr(int(max_y / 2 + 6 + 3), 0, "Trace ({:.0f}): {:s}".format(len(buf_undo) / 2, buf))

        # timer
        time_curr = time.time()
        if self.pausing is False:
            self.watch += time_curr - self.time_last
        self.time_last = time_curr

        self.stdscr.addstr(int(2), int(max_x - 2 - 8),
                '{:02}:{:02}:{:02}'.format(int(self.watch/60/60%24), int(self.watch/60%60), int(self.watch%60)),
                    curses.color_pair(0) | curses.A_STANDOUT | curses.A_DIM if self.pausing == True else curses.A_NORMAL)

    def turn_top(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn top only
        for i in range(3):
            for j in range(3):
                self.cube[0][i][j] = backup_cube[0][2-j][i]
        # turn rest
        for i, j in [(2, 4), (3, 5), (4, 3), (5, 2)]:
            for k in range(3):
                self.cube[i][0][k] = backup_cube[j][0][k]

    def turn_top_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn top only
        for i in range(3):
            for j in range(3):
                self.cube[0][j][i] = backup_cube[0][i][2-j]
        # turn rest
        for i, j in [(2, 5), (3, 4), (4, 2), (5, 3)]:
            for k in range(3):
                self.cube[i][0][k] = backup_cube[j][0][k]

    def turn_bottom(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn bottom only
        for i in range(3):
            for j in range(3):
                self.cube[1][i][j] = backup_cube[1][2-j][i]
        # turn rest
        for i, j in [(2, 5), (3, 4), (4, 2), (5, 3)]:
            for k in range(3):
                self.cube[i][2][k] = backup_cube[j][2][k]

    def turn_bottom_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn bottom only
        for i in range(3):
            for j in range(3):
                self.cube[1][j][i] = backup_cube[1][i][2-j]
        # turn rest
        for i, j in [(2, 4), (3, 5), (4, 3), (5, 2)]:
            for k in range(3):
                self.cube[i][2][k] = backup_cube[j][2][k]

    def turn_left(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn left only
        for i in range(3):
            for j in range(3):
                self.cube[2][i][j] = backup_cube[2][2-j][i]
        # change top-part
        for i in range(3):
            self.cube[0][i][0] = backup_cube[5][2-i][2]
        # change bottom-part
        for i in range(3):
            self.cube[1][i][0] = backup_cube[4][i][0]
        # change front-part
        for i in range(3):
            self.cube[4][i][0] = backup_cube[0][i][0]
        # change back-part
        for i in range(3):
            self.cube[5][i][2] = backup_cube[1][2-i][0]

    def turn_left_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn left only
        for i in range(3):
            for j in range(3):
                self.cube[2][j][i] = backup_cube[2][i][2-j]
        # change top-part
        for i in range(3):
            self.cube[0][i][0] = backup_cube[4][i][0]
        # change bottom-part
        for i in range(3):
            self.cube[1][i][0] = backup_cube[5][2-i][2]
        # change front-part
        for i in range(3):
            self.cube[4][i][0] = backup_cube[1][i][0]
        # change back-part
        for i in range(3):
            self.cube[5][i][2] = backup_cube[0][2-i][0]

    def turn_right(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn right only
        for i in range(3):
            for j in range(3):
                self.cube[3][i][j] = backup_cube[3][2-j][i]
        # change top-part
        for i in range(3):
            self.cube[0][i][2] = backup_cube[4][i][2]
        # change bottom-part
        for i in range(3):
            self.cube[1][i][2] = backup_cube[5][2-i][0]
        # change front-part
        for i in range(3):
            self.cube[4][i][2] = backup_cube[1][i][2]
        # change back-part
        for i in range(3):
            self.cube[5][i][0] = backup_cube[0][2-i][2]

    def turn_right_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn right only
        for i in range(3):
            for j in range(3):
                self.cube[3][j][i] = backup_cube[3][i][2-j]
        # change top-part
        for i in range(3):
            self.cube[0][i][2] = backup_cube[5][2-i][0]
        # change bottom-part
        for i in range(3):
            self.cube[1][i][2] = backup_cube[4][i][2]
        # change front-part
        for i in range(3):
            self.cube[4][i][2] = backup_cube[0][i][2]
        # change back-part
        for i in range(3):
            self.cube[5][i][0] = backup_cube[1][2-i][2]

    def turn_front(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn front only
        for i in range(3):
            for j in range(3):
                self.cube[4][i][j] = backup_cube[4][2-j][i]
        # change top-part
        for i in range(3):
            self.cube[0][2][i] = backup_cube[2][2-i][2]
        # change bottom-part
        for i in range(3):
            self.cube[1][0][i] = backup_cube[3][2-i][0]
        # change left-part
        for i in range(3):
            self.cube[2][i][2] = backup_cube[1][0][i]
        # change right-part
        for i in range(3):
            self.cube[3][i][0] = backup_cube[0][2][i]

    def turn_front_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn front only
        for i in range(3):
            for j in range(3):
                self.cube[4][j][i] = backup_cube[4][i][2-j]
        # change top-part
        for i in range(3):
            self.cube[0][2][i] = backup_cube[3][i][0]
        # change bottom-part
        for i in range(3):
            self.cube[1][0][i] = backup_cube[2][i][2]
        # change left-part
        for i in range(3):
            self.cube[2][i][2] = backup_cube[0][2][2-i]
        # change right-part
        for i in range(3):
            self.cube[3][i][0] = backup_cube[1][0][2-i]

    def turn_back(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn back only
        for i in range(3):
            for j in range(3):
                self.cube[5][i][j] = backup_cube[5][2-j][i]
        # change top-part
        for i in range(3):
            self.cube[0][0][i] = backup_cube[3][i][2]
        # change bottom-part
        for i in range(3):
            self.cube[1][2][i] = backup_cube[2][i][0]
        # change left-part
        for i in range(3):
            self.cube[2][i][0] = backup_cube[0][0][2-i]
        # change right-part
        for i in range(3):
            self.cube[3][i][2] = backup_cube[1][2][2-i]

    def turn_back_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn back only
        for i in range(3):
            for j in range(3):
                self.cube[5][j][i] = backup_cube[5][i][2-j]
        # change top-part
        for i in range(3):
            self.cube[0][0][i] = backup_cube[2][2-i][0]
        # change bottom-part
        for i in range(3):
            self.cube[1][2][i] = backup_cube[3][2-i][2]
        # change left-part
        for i in range(3):
            self.cube[2][i][0] = backup_cube[1][2][i]
        # change right-part
        for i in range(3):
            self.cube[3][i][2] = backup_cube[0][0][i]

    # r
    def turn_middle(self):
        backup_cube = copy.deepcopy(self.cube)
        for i in range(3):
            self.cube[0][i][1] = backup_cube[4][i][1]
            self.cube[4][i][1] = backup_cube[1][i][1]
            self.cube[1][i][1] = backup_cube[5][2-i][1]
            self.cube[5][i][1] = backup_cube[0][2-i][1]

    # R
    def turn_middle_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        for i in range(3):
            self.cube[0][i][1] = backup_cube[5][2-i][1]
            self.cube[4][i][1] = backup_cube[0][i][1]
            self.cube[1][i][1] = backup_cube[4][i][1]
            self.cube[5][i][1] = backup_cube[1][2-i][1]

    # u
    def turn_equator(self):
        backup_cube = copy.deepcopy(self.cube)
        for i, j in [(2, 4), (4, 3), (3, 5), (5, 2)]:
            for k in range(3):
                self.cube[i][1][k] = backup_cube[j][1][k]

    # U
    def turn_equator_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        for i, j in [(2, 5), (4, 2), (3, 4), (5, 3)]:
            for k in range(3):
                self.cube[i][1][k] = backup_cube[j][1][k]

    # f
    def turn_standing(self):
        backup_cube = copy.deepcopy(self.cube)
        for k in range(3):
            self.cube[0][1][k] = backup_cube[2][2-k][1]
            self.cube[2][k][1] = backup_cube[1][1][k]
            self.cube[1][1][k] = backup_cube[3][2-k][1]
            self.cube[3][k][1] = backup_cube[0][1][k]

    # F
    def turn_standing_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        for k in range(3):
            self.cube[0][1][k] = backup_cube[3][k][1]
            self.cube[2][k][1] = backup_cube[0][1][2-k]
            self.cube[1][1][k] = backup_cube[2][k][1]
            self.cube[3][k][1] = backup_cube[1][1][2-k]

    # cube x-axis r/L
    def move_x(self):
        self.turn_right()
        self.turn_middle()
        self.turn_left_rev()

    # R/l
    def move_x_rev(self):
        self.turn_right_rev()
        self.turn_middle_rev()
        self.turn_left()

    # cube y-axis u/D
    def move_y(self):
        self.turn_top()
        self.turn_equator()
        self.turn_bottom_rev()

    # U/d
    def move_y_rev(self):
        self.turn_top_rev()
        self.turn_equator_rev()
        self.turn_bottom()

    # cube z-axis f/B
    def move_z(self):
        self.turn_front()
        self.turn_standing()
        self.turn_back_rev()

    # F/b
    def move_z_rev(self):
        self.turn_front_rev()
        self.turn_standing_rev()
        self.turn_back()

    def scramble(self):
        global buf_undo, buf_redo
        functions = [self.turn_top, self.turn_bottom, self.turn_left,
                     self.turn_right, self.turn_front, self.turn_back]
        for i in range(30):
            functions[random.randint(0, 5)]()

        buf_undo = buf_redo =  ""
        self.watch = 0
        self.time_last = time.time()
        self.pausing = False

    def get_input(self):
        global buf_undo, buf_redo
        key = None
        dismiss = False
        try:
            key = self.stdscr.getkey()
        except curses.error:
            pass

        # trace buffer
        if key == delete:
            key = buf_undo[-2:-1]
            key = key.lower() if key == key.upper() else key.upper()
            buf_undo = buf_undo[:-2]
            dismiss = True

        elif key == undo:
            key = buf_undo[-2:-1]
            key = key.lower() if key == key.upper() else key.upper()
            buf_redo += buf_undo[-2:]
            buf_undo = buf_undo[:-2]
            dismiss = True

        elif key == redo:
            key = buf_redo[-2:-1]
            buf_redo = buf_redo[:-2]

        # controls
        if key == reset:
            self.scramble()

        elif key == solve:
            self.cube = copy.deepcopy(self.solved_cube)

        elif key == layout:
            self.mode = (self.mode + 1) % 3

            if self.mode <= 1:
                curses.init_pair(1, curses.COLOR_WHITE,   -1)
                curses.init_pair(2, curses.COLOR_YELLOW,  -1)
                curses.init_pair(3, curses.COLOR_MAGENTA, -1)
                curses.init_pair(4, curses.COLOR_RED,     -1)
                curses.init_pair(5, curses.COLOR_GREEN,   -1)
                curses.init_pair(6, curses.COLOR_BLUE,    -1)
            else:
                curses.init_pair(1, curses.COLOR_WHITE,   curses.COLOR_WHITE)
                curses.init_pair(2, curses.COLOR_YELLOW,  curses.COLOR_YELLOW)
                curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
                curses.init_pair(4, curses.COLOR_RED,     curses.COLOR_RED)
                curses.init_pair(5, curses.COLOR_GREEN,   curses.COLOR_GREEN)
                curses.init_pair(6, curses.COLOR_BLUE,    curses.COLOR_BLUE)

        elif key == pause:
            self.pausing = not self.pausing

        elif key == quit:
            self.looping = False

        # moves
        elif key == up:
            if not dismiss:
                buf_undo += key + " "
            self.turn_top()
        elif key == up.upper():
            if not dismiss:
                buf_undo += key + " "
            self.turn_top_rev()

        elif key == down:
            if not dismiss:
                buf_undo += key + " "
            self.turn_bottom()
        elif key == down.upper():
            if not dismiss:
                buf_undo += key + " "
            self.turn_bottom_rev()

        elif key == left:
            if not dismiss:
                buf_undo += key + " "
            self.turn_left()
        elif key == left.upper():
            if not dismiss:
                buf_undo += key + " "
            self.turn_left_rev()

        elif key == right:
            if not dismiss:
                buf_undo += key + " "
            self.turn_right()
        elif key == right.upper():
            if not dismiss:
                buf_undo += key + " "
            self.turn_right_rev()

        elif key == front:
            if not dismiss:
                buf_undo += key + " "
            self.turn_front()
        elif key == front.upper():
            if not dismiss:
                buf_undo += key + " "
            self.turn_front_rev()

        elif key == back:
            if not dismiss:
                buf_undo += key + " "
            self.turn_back()
        elif key == back.upper():
            if not dismiss:
                buf_undo += key + " "
            self.turn_back_rev()

        # inconsistently reversed!
        elif key == middle:
            if not dismiss:
                buf_undo += key + " "
            self.turn_middle_rev()
        elif key == middle.upper():
            if not dismiss:
                buf_undo += key + " "
            self.turn_middle()

        # inconsistently reversed!
        elif key == equator:
            if not dismiss:
                buf_undo += key + " "
            self.turn_equator_rev()
        elif key == equator.upper():
            if not dismiss:
                buf_undo += key + " "
            self.turn_equator()

        elif key == standing:
            if not dismiss:
                buf_undo += key + " "
            self.turn_standing()
        elif key == standing.upper():
            if not dismiss:
                buf_undo += key + " "
            self.turn_standing_rev()

        # turns
        elif key == cube_x:
            if not dismiss:
                buf_undo += key + " "
            self.move_x()
        elif key == cube_x.upper():
            if not dismiss:
                buf_undo += key + " "
            self.move_x_rev()

        elif key == cube_y:
            if not dismiss:
                buf_undo += key + " "
            self.move_y()
        elif key == cube_y.upper():
            if not dismiss:
                buf_undo += key + " "
            self.move_y_rev()

        elif key == cube_z:
            if not dismiss:
                buf_undo += key + " "
            self.move_z()
        elif key == cube_z.upper():
            if not dismiss:
                buf_undo += key + " "
            self.move_z_rev()

        time.sleep(0.02)

    def loop(self):
        while self.looping:
            self.stdscr.erase()
            self.helper()
            if self.solved() is True:
                self.print_appeal()
            self.display_cube()
            self.stdscr.refresh()
            self.get_input()

def main(stdscr):
    cube = Cube(stdscr)
    cube.loop()

if __name__ == '__main__':
    curses.wrapper(main)

