#!/usr/bin/env python
#
# nrubik2 - ncurses based virtual rubik's cube
#
# Copyright (c) 2017 Caleb Butler
# Copyright (c) 2019 LinuxCowboy
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

from __future__ import division

import sys
import curses
import copy
import random
import time
import os

sys.tracebacklimit = 1

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

# solver
solve_1 = '1'
solve_2 = '2'
solve_3 = '3'

# savegames
cube_out   = 'o'  # save with timestamp
cube_in    = 'i'  # load last saved
cube_kill  = 'k'  # delete last loaded

# circular restore
cycle_down = '-'
cycle_up   = '+'

# savegames with zenity
cube_out_zen  = 'O'  # name
cube_in_zen   = 'I'  # choose
cube_kill_zen = 'K'  # delete (multiple)

pause  = ' '  # speedcube timer
marker = '_'  # key buffer
gtimer = 't'  # game timer

# history
undo   = 'KEY_BACKSPACE'
redo   = chr(10)
delete = 'KEY_DC'
toredo = 'KEY_PPAGE'
tonull = 'KEY_NPAGE'

reset  = 'KEY_HOME'
cheat  = 'KEY_END'

layout = 'KEY_IC'
quit   = chr(27)

# auto play / macros
auto     = 'a'
auto_rec = 'A'

auto_play = {
    '4': 'left'  + " " + '_RURURurur_',
    '5': 'right' + " " + '_rururURUR_',
    '6': 'cross' + " " + '_fruRUF_',
    '7': 'edge'  + " " + '_ruRuruuR_',
    '8': 'front' + " " + '_DRdrDRdr_',
    '9': 'side'  + " " + '_RDrdRDrd_',
    '0': 'macro' + " " + '__'}

### free letters:  g h j n p q v w

cube_file = "%y%m%d-%H%M%S"  # time.strftime
cube_dir  = "~/nrubik2"

msg_time = 7  # display duration

player = 'aplay'    # cmdline audio player (alsa-utils)
option = '--quiet'  # suppress any output

tick_files = 'tick1.wav', 'tick2.wav', 'tick3.wav'  # chimes
tick_paths = './', 'sound', '~/Music'
tick_times = (0, 0), (5, 0), (10, 1), (15, 2), (40, 0), (90, 1), (120, 2)  # (seconds, index)

# profiling_solve_1.py
scramble_moves = 17
search_deep_1  = 6

# profiling_solve_2.py
search_deep_2  = 6
reset_point    = 400

############################################################################

if sys.argv[1:]:
    if sys.argv[1] == '--help':
        print("nrubik2 - An N-Curses Based, Virtual Rubik's Cube\n")

        print("    %s [+] [second_to_play,chime_index] ...\n" % sys.argv[0])

        print("option:   replace [or add to] timer ticks list\n")

        default = 'default:  '
        for t in tick_times:
            second, index = t

            default += str(second) + "," + str(index) + " "

        print(default + "\n")

        chimes = 'chimes:   '
        for i,j in enumerate(tick_files):
            chimes += str(i) + ": " + j + "  "

        print(chimes + "\n")

        sys.exit(0)

    else:
        start = 1

        if sys.argv[1] == '+':
            start = 2
        else:
            tick_times = ()

        for i in range(start, len(sys.argv)):
            second, index = sys.argv[i].split(',')

            tick_times += (int(second), int(index)),

        tick_times = sorted(tick_times)

cube_dir = os.path.join(os.path.expanduser(cube_dir), "")  # zenity needs trailing slash

if not os.path.isdir(cube_dir):
    os.makedirs(cube_dir)

def find_exe(execname):
    path = os.environ['PATH'].split(os.pathsep)

    for p in path:
        exe = os.path.join(p, execname)

        if os.path.isfile(exe):
            return exe
    else:
        return False

# Checks: if problems with player or files - simply no sound
timer_ticks = ()

if find_exe(player):
    for tp in tick_paths:
        path = os.path.expanduser(tp)

        for tf in tick_files:
            if not os.path.isfile(os.path.join(path, tf)):
                break
        else:
            for sec,idx in tick_times:
                timer_ticks += (sec, os.path.join(path, tick_files[idx])),
            break

moves = [up, down, left, right, front, back,  middle, equator, standing,  cube_x, cube_y, cube_z]

for m in moves[:]:
    moves.append(m.upper())

class Cube:
    modes = {"nrubik_bw": 0, "nrubik": 1, "nrubik2": 2, "timer": 3}
    mode  = modes["nrubik2"]  # startmode

    looping = True  # False == exit
    pausing = True  # pause timer
    refresh = True  # refresh screen every second or after key press
    show_gt = True  # switch game timer on/off

    game_timer    = 0  # accurate to the second
    speed_timer   = 0  # accurate to the 1/100s
    previous_time = 0  # buffer for timer

    place_1 = 0
    place_2 = 0
    place_3 = 0

    solve_moves = 0  # moves in brute force solver
    solve_stat  = 0  # duration viewing brute force results
    solve_cheat = False

    buf_undo = ""  # trace buffer
    buf_redo = ""  # redo buffer
    auto_buf = ""  # macro buffer
    msg_buf  = ""  # status message

    savegame   = ""  # last loaded file
    load_index = 0   # index in file list

    tick = 0  # index in speedcube timer chimes list

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

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.stdscr.nodelay(True)
        self.stdscr.scrollok(True)
        curses.use_default_colors()
        curses.curs_set(False)

        self.max_y = self.max_x = 0

        self.cube = copy.deepcopy(self.solved_cube)

        self.functions = (self.turn_top, self.turn_top_rev, self.turn_bottom, self.turn_bottom_rev,
                          self.turn_left, self.turn_left_rev, self.turn_right, self.turn_right_rev,
                          self.turn_front, self.turn_front_rev, self.turn_back, self.turn_back_rev)

        if curses.has_colors():
            if self.mode == self.modes["nrubik2"]:
                curses.init_pair(1, curses.COLOR_WHITE,   curses.COLOR_WHITE)
                curses.init_pair(2, curses.COLOR_YELLOW,  curses.COLOR_YELLOW)
                curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
                curses.init_pair(4, curses.COLOR_RED,     curses.COLOR_RED)
                curses.init_pair(5, curses.COLOR_GREEN,   curses.COLOR_GREEN)
                curses.init_pair(6, curses.COLOR_BLUE,    curses.COLOR_BLUE)
            else:
                curses.init_pair(1, curses.COLOR_WHITE,   -1)
                curses.init_pair(2, curses.COLOR_YELLOW,  -1)
                curses.init_pair(3, curses.COLOR_MAGENTA, -1)
                curses.init_pair(4, curses.COLOR_RED,     -1)
                curses.init_pair(5, curses.COLOR_GREEN,   -1)
                curses.init_pair(6, curses.COLOR_BLUE,    -1)

            # vivid colors (RGB)
            # 0:black  1:red  2:green  3:yellow  4:blue  5:magenta  6:cyan  7:white
            if curses.can_change_color():
                curses.init_color(7, 800, 800, 800)
                curses.init_color(3, 800, 800,   0)
                curses.init_color(5, 800,   0, 800)
                curses.init_color(1, 800,   0,   0)
                curses.init_color(2,   0, 800,   0)
                curses.init_color(4,   0,   0, 800)
        else:
            self.mode = self.modes["nrubik_bw"]

    def helper(self):
        start_y = 2
        start_x = 2
        end_x   = self.max_x - 2 - 18

        head = "nrubik2 - An N-Curses Based, Virtual Rubik's Cube"
        self.stdscr.addstr(0, int(self.max_x / 2 - len(head) / 2 - 1), head)

        self.stdscr.addstr(start_y + 0, start_x, "Keybindings:")

        if self.mode != self.modes["timer"]:
            self.stdscr.addstr(start_y + 2,  start_x, up + ","    + up.upper()    + " - Up")
            self.stdscr.addstr(start_y + 3,  start_x, down + ","  + down.upper()  + " - Down")
            self.stdscr.addstr(start_y + 4,  start_x, left + ","  + left.upper()  + " - Left")
            self.stdscr.addstr(start_y + 5,  start_x, right + "," + right.upper() + " - Right")
            self.stdscr.addstr(start_y + 6,  start_x, front + "," + front.upper() + " - Front")
            self.stdscr.addstr(start_y + 7,  start_x, back + ","  + back.upper()  + " - Back")
            self.stdscr.addstr(start_y + 8,  start_x, middle + ","   + middle.upper()   + " - Middle")
            self.stdscr.addstr(start_y + 9,  start_x, equator + ","  + equator.upper()  + " - Equator")
            self.stdscr.addstr(start_y + 10, start_x, standing + "," + standing.upper() + " - Standing")
            self.stdscr.addstr(start_y + 11, start_x, cube_x + ","   + cube_x.upper()   + " - Cube X")
            self.stdscr.addstr(start_y + 12, start_x, cube_y + ","   + cube_y.upper()   + " - Cube Y")
            self.stdscr.addstr(start_y + 13, start_x, cube_z + ","   + cube_z.upper()   + " - Cube Z")
            self.stdscr.addstr(start_y + 14, start_x, "1,2,3 - Solve")
            self.stdscr.addstr(start_y + 15, start_x, "End   - Cheat")
            self.stdscr.addstr(start_y + 16, start_x, "Home  - Reset")

            self.stdscr.addstr(start_y + 2,  end_x + 6, cube_out + "/"   + cube_out_zen  + " - Save")
            self.stdscr.addstr(start_y + 3,  end_x + 6, cube_in + "/"    + cube_in_zen   + " - Load")
            self.stdscr.addstr(start_y + 4,  end_x + 6, cube_kill + "/"  + cube_kill_zen + " - Kill")
            self.stdscr.addstr(start_y + 5,  end_x + 6, cycle_down + "/" + cycle_up      + " - Cycle")
            self.stdscr.addstr(start_y + 6,  end_x + 6, auto + "/"       + auto_rec      + " - Auto")
            self.stdscr.addstr(start_y + 7,  end_x, "Backspace - Undo")
            self.stdscr.addstr(start_y + 8,  end_x, "Enter     - Redo")
            self.stdscr.addstr(start_y + 9,  end_x, "Delete    - Delete")
            self.stdscr.addstr(start_y + 10, end_x, "Page Up   - 2 Redo")
            self.stdscr.addstr(start_y + 11, end_x, "Page Down - 2 Null")
            self.stdscr.addstr(start_y + 12, end_x, "Space     - Marker")

            self.stdscr.addstr(start_y + 14, end_x, gtimer + "      - Timer")
            self.stdscr.addstr(start_y + 15, end_x,         "Insert - Layout")
            self.stdscr.addstr(start_y + 16, end_x,         "Escape - Quit")

        else:
            self.stdscr.addstr(start_y + 2, start_x, "Space - Start/Stop")

            self.stdscr.addstr(start_y + 4, start_x, "Enter - Rate")
            self.stdscr.addstr(start_y + 5, start_x, "Home  - Reset")

            self.stdscr.addstr(start_y + 7, start_x, "Insert - Mode")
            self.stdscr.addstr(start_y + 8, start_x, "Escape - Quit")

    # fullspeed timer, but displayed only in 1/10s
    def timer(self):
        self.stdscr.addstr(int(self.max_y / 2), int(self.max_x / 2 - 4),
            '{:1}:{:05.2f}'.format(int(self.speed_timer / 60), self.speed_timer % 60),
                curses.color_pair(0) | curses.A_STANDOUT | curses.A_DIM if self.pausing else curses.A_NORMAL)

    def solved(self):
        for i in range(6):
            if not self.cube[i][0][0] == self.cube[i][0][1] == self.cube[i][0][2]\
                == self.cube[i][1][0] == self.cube[i][1][1] == self.cube[i][1][2]\
                == self.cube[i][2][0] == self.cube[i][2][1] == self.cube[i][2][2]:
                    return False

        if self.mode != self.modes["timer"]:
            self.pausing = True

        return True

    def headline(self):
        if self.mode != self.modes["timer"]:
            if self.solved() or self.solve_cheat:
                if self.solved() and self.buf_undo and not self.solve_cheat:
                    head = "Solved. Congrats!"
                else:
                    head = "'Home' for Start!"
            else:
                if self.mode in (self.modes["nrubik_bw"], self.modes["nrubik"]):
                    head = "nrubik"
                else:
                    head = "nrubik2"
        else:
            head = "Speedcube Timer"

        self.stdscr.addstr(int(self.max_y / 2 - 10), int(self.max_x / 2 - len(head) / 2 - 1), head)

    def display_cubie(self, y, x, cubie):
        colors = {'W': 1, 'Y': 2, 'M': 3, 'R': 4, 'G': 5, 'B': 6}

        if self.mode == self.modes["nrubik2"]:
            cub = cubie * 2
        else:
            cub = cubie

        if not curses.has_colors() or self.mode == self.modes["nrubik_bw"]:
            self.stdscr.addstr(int(y), int(x), cub)
        else:
            self.stdscr.addstr(int(y), int(x), cub, curses.color_pair(colors[cubie]))

    def display_cube(self):
        y, x = self.max_y, self.max_x
        # nrubik + b/w
        if self.mode in (self.modes["nrubik_bw"], self.modes["nrubik"]):
            # top
            for i, line in enumerate(self.cube[0]):
                for j in range(3):
                    self.display_cubie(y / 2 - 6 + i, x / 2 - 2 + j, line[j])
            # bottom
            for i, line in enumerate(self.cube[1]):
                for j in range(3):
                    self.display_cubie(y / 2 + 2 + i, x / 2 - 2 + j, line[j])
            # left
            for i, line in enumerate(self.cube[2]):
                for j in range(3):
                    self.display_cubie(y / 2 - 2 + i, x / 2 - 6 + j, line[j])
            # right
            for i, line in enumerate(self.cube[3]):
                for j in range(3):
                    self.display_cubie(y / 2 - 2 + i, x / 2 + 2 + j, line[j])
            # front
            for i, line in enumerate(self.cube[4]):
                for j in range(3):
                    self.display_cubie(y / 2 - 2 + i, x / 2 - 2 + j, line[j])
            # back
            for i, line in enumerate(self.cube[5]):
                for j in range(3):
                    self.display_cubie(y / 2 - 7 + i, x / 2 + 3 + j, line[j])
        # nrubik2
        elif self.mode == self.modes["nrubik2"]:
            # bars
            self.stdscr.addstr(int(y / 2 - 9), int(x / 2 - 1),  " __________________")
            self.stdscr.addstr(int(y / 2 - 8), int(x / 2 + 17), "||")
            self.stdscr.addstr(int(y / 2 - 7), int(x / 2 - 10), "______  ||  ______")
            self.stdscr.addstr(int(y / 2 - 6), int(x / 2 - 7),  "___......___")
            self.stdscr.addstr(int(y / 2 - 5), int(x / 2 - 12), "|   /___......___\\   |")
            self.stdscr.addstr(int(y / 2 - 4), int(x / 2 - 12), "|  /    ......    \\  |")
            self.stdscr.addstr(int(y / 2 - 3), int(x / 2 - 12), "| ||   +  ||  +   || |")
            self.stdscr.addstr(int(y / 2 - 1), int(x / 2 - 14), "--......--......--......--")
            self.stdscr.addstr(int(y / 2 + 1), int(x / 2 - 12), "| ||   +  ||  +   || |")
            self.stdscr.addstr(int(y / 2 + 2), int(x / 2 - 12), "|  \\ ___......___ /  |")
            self.stdscr.addstr(int(y / 2 + 3), int(x / 2 - 12), "|   \\___......___/   |")
            self.stdscr.addstr(int(y / 2 + 4), int(x / 2 - 10), "______  ||  ______")
            self.stdscr.addstr(int(y / 2 + 5), int(x / 2 - 2),  "||")

            # top
            for i, line in enumerate(self.cube[0]):
                for j in range(3):
                    self.display_cubie(y / 2 - 6 + i, x / 2 - 4 + (j*2),      line[j])
            # bottom
            for i, line in enumerate(self.cube[1]):
                for j in range(3):
                    self.display_cubie(y / 2 + 2 + i, x / 2 - 4 + (j*2),      line[j])
            # left
            for i, line in enumerate(self.cube[2]):
                for j in range(3):
                    self.display_cubie(y / 2 - 2 + i, x / 2 - 12 + (j*2),     line[j])
            # right
            for i, line in enumerate(self.cube[3]):
                for j in range(3):
                    self.display_cubie(y / 2 - 2 + i, x / 2 + 4 + (j*2),      line[j])
            # front
            for i, line in enumerate(self.cube[4]):
                for j in range(3):
                    self.display_cubie(y / 2 - 2 + i, x / 2 - 4 + (j*2),      line[j])
            # back
            for i, line in enumerate(self.cube[5]):
                for j in range(3):
                    self.display_cubie(y / 2 - 7 + i, x / 2 + 15 + (4-(j*2)), line[j])

            # mirror
            self.display_cubie(y / 2 - 6, x / 2 + 8,  self.cube[5][0][0])
            self.display_cubie(y / 2 - 8, x / 2 - 2,  self.cube[5][0][1])
            self.display_cubie(y / 2 - 6, x / 2 - 12, self.cube[5][0][2])

            self.display_cubie(y / 2 - 1, x / 2 + 12, self.cube[5][1][0])
            self.display_cubie(y / 2 - 1, x / 2 - 16, self.cube[5][1][2])

            self.display_cubie(y / 2 + 4, x / 2 + 8,  self.cube[5][2][0])
            self.display_cubie(y / 2 + 6, x / 2 - 2,  self.cube[5][2][1])
            self.display_cubie(y / 2 + 4, x / 2 - 12, self.cube[5][2][2])

        # timer mode
        else:
            start_y = int(y / 2 + 5)
            start_x = int(x / 2 - 19)

            self.timer()

            self.stdscr.addstr(start_y + 1, start_x, "              _________")
            self.stdscr.addstr(start_y + 2, start_x, "    _________|    1    |")
            self.stdscr.addstr(start_y + 3, start_x, "   |    2    |         |_________")
            self.stdscr.addstr(start_y + 4, start_x, "   |         |         |    3    |")
            self.stdscr.addstr(start_y + 5, start_x, "-------------------------------------")

            self.stdscr.addstr(start_y + 0, start_x + 15, '{:1}:{:05.2f}'.format(int(self.place_1 / 60), self.place_1 % 60))
            self.stdscr.addstr(start_y + 1, start_x +  5, '{:1}:{:05.2f}'.format(int(self.place_2 / 60), self.place_2 % 60))
            self.stdscr.addstr(start_y + 2, start_x + 25, '{:1}:{:05.2f}'.format(int(self.place_3 / 60), self.place_3 % 60))

            if self.solve_stat > self.previous_time:
                self.stdscr.addstr(int(y / 2 + 3), int(x / 2 - len(self.msg_buf) / 2 - 1), self.msg_buf)

            if timer_ticks:
                buf = "  ".join("%d" % t[0] for t in timer_ticks)

                self.stdscr.addstr(int(y / 2 - 5), int(x / 2 - 6), "Timer Ticks:")
                self.stdscr.addstr(int(y / 2 - 3), int(x / 2 - len(buf) / 2), buf)

        if self.mode != self.modes["timer"]:
            # game timer - displayed in 1s
            if self.show_gt:
                self.stdscr.addstr(int(2), int(x - 2 - 8), '{:02}:{:02}:{:02}'.format(
                    int(self.game_timer / 60 / 60 % 24), int(self.game_timer / 60 % 60), int(self.game_timer % 60)),
                        curses.color_pair(0) | curses.A_STANDOUT | curses.A_DIM if self.pausing else curses.A_NORMAL)

            # solve statistic
            if self.solve_stat > self.previous_time:
                self.stdscr.addstr(int(y / 2 + 7), int(x / 2 - len(self.msg_buf) / 2 - 1), self.msg_buf)

            # trace redo
            max = int(x - 13 - 6)
            buf = self.buf_redo[::-1]

            if len(buf) > max:
                buf = buf[:max]
                buf += " ...  "

            self.stdscr.addstr(int(y / 2 + 8), 0, "Redo ({}): {}".format(len(self.buf_redo), buf))

            # trace undo
            max = int(x + x / 2 - 14 - 4)
            buf = self.buf_undo[-max:]

            if len(self.buf_undo) > max:
                buf = "... " + buf

            self.stdscr.addstr(int(y / 2 + 9), 0, "Trace ({}): {}".format(len(self.buf_undo), buf))

### start rotations

    def turn_top(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn top only
        for i in range(3):
            for j in range(3):
                self.cube[0][i][j] = backup_cube[0][2-j][i]
        # turn rest
        for i, j in (2, 4), (3, 5), (4, 3), (5, 2):
            for k in range(3):
                self.cube[i][0][k] = backup_cube[j][0][k]

    def turn_top_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn top only
        for i in range(3):
            for j in range(3):
                self.cube[0][j][i] = backup_cube[0][i][2-j]
        # turn rest
        for i, j in (2, 5), (3, 4), (4, 2), (5, 3):
            for k in range(3):
                self.cube[i][0][k] = backup_cube[j][0][k]

    def turn_bottom(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn bottom only
        for i in range(3):
            for j in range(3):
                self.cube[1][i][j] = backup_cube[1][2-j][i]
        # turn rest
        for i, j in (2, 5), (3, 4), (4, 2), (5, 3):
            for k in range(3):
                self.cube[i][2][k] = backup_cube[j][2][k]

    def turn_bottom_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        # turn bottom only
        for i in range(3):
            for j in range(3):
                self.cube[1][j][i] = backup_cube[1][i][2-j]
        # turn rest
        for i, j in (2, 4), (3, 5), (4, 3), (5, 2):
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
        for i, j in (2, 4), (4, 3), (3, 5), (5, 2):
            for k in range(3):
                self.cube[i][1][k] = backup_cube[j][1][k]

    # U
    def turn_equator_rev(self):
        backup_cube = copy.deepcopy(self.cube)
        for i, j in (2, 5), (4, 2), (3, 4), (5, 3):
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

### start solver

    def search_edge(self, cubie1, cubie2):
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

            if (self.cube[i][j][k] == cubie1 and self.cube[l][m][n] == cubie2 or
                self.cube[i][j][k] == cubie2 and self.cube[l][m][n] == cubie1):
                    found.extend((i, j, k))
                    break

        return found

    def move_edge(self, cubie):
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
            funcs = [4, 5, 10, 11]

        elif cubie[0] == 3:
            funcs = [6, 7, 8, 9]

        elif cubie[0] == 4:
            funcs = [8, 9, 4, 5]

        elif cubie[0] == 5:
            funcs = [10, 11, 6, 7]

        random.shuffle(funcs)

        self.functions[funcs[0]]()

    # solve white cross + edges
    def solve_1(self):

        edges = (((0, 2, 1), (4, 0, 1)),
                 ((0, 1, 2), (3, 0, 1)),
                 ((0, 0, 1), (5, 0, 1)),
                 ((0, 1, 0), (2, 0, 1)))

        i = 0
        # white up (but independent: solved_cube[0])
        while self.cube[0][1][1] != self.solved_cube[0][1][1]:
            if i < 3:
                self.move_x()
            else:
                self.move_z()
            i += 1

        # green at front
        while self.cube[4][1][1] != self.solved_cube[4][1][1]:
                self.move_y()

        while not (self.cube[0][2][1] == self.cube[0][1][2] == self.cube[0][0][1] == self.cube[0][1][0]
                                      == self.solved_cube[0][1][1] and

                   self.cube[2][0][1] == self.solved_cube[2][0][1] and
                   self.cube[3][0][1] == self.solved_cube[3][0][1] and
                   self.cube[4][0][1] == self.solved_cube[4][0][1] and
                   self.cube[5][0][1] == self.solved_cube[5][0][1]):

            for e in range(4):
                i, j, k = edges[e][0]
                l, m, n = edges[e][1]

                c = 0
                while not (self.cube[i][j][k] == self.solved_cube[i][j][k] and
                           self.cube[l][m][n] == self.solved_cube[l][m][n]):
                                if c == 0:
                                    backup_cube = copy.deepcopy(self.cube)

                                elif c == search_deep_1:
                                    self.cube = copy.deepcopy(backup_cube)
                                    c = 0

                                cubie = self.search_edge(self.solved_cube[i][j][k], self.solved_cube[l][m][n])

                                self.move_edge(cubie)

                                c += 1
                                self.solve_moves += 1

    def search_corner(self, cubie1, cubie2):
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

            if (self.cube[i][j][k] == self.solved_cube[0][1][1] and
                                   self.cube[l][m][n] == cubie1 and
                                   self.cube[o][p][q] == cubie2 or

                self.cube[l][m][n] == self.solved_cube[0][1][1] and
                                   self.cube[o][p][q] == cubie1 and
                                   self.cube[i][j][k] == cubie2 or

                self.cube[o][p][q] == self.solved_cube[0][1][1] and
                                   self.cube[i][j][k] == cubie1 and
                                   self.cube[l][m][n] == cubie2):
                    found.extend((i, j, k))
                    break

        return found

    def move_corner(self, cubie):
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

        self.functions[funcs[0]]()

    # solve white corners
    def solve_2(self):
        restart = True

        while restart:
            restart = False

            # orientation independent
            for c1, c2 in ((self.solved_cube[3][0][0], self.solved_cube[4][0][2]),
                           (self.solved_cube[5][0][0], self.solved_cube[3][0][2]),
                           (self.solved_cube[2][0][0], self.solved_cube[5][0][2]),
                           (self.solved_cube[4][0][0], self.solved_cube[2][0][2])):
                i = moves = 0

                while not (# intermediate step
                           (self.cube[4][2][2] == self.solved_cube[0][2][2] and self.cube[3][2][0] == c1 or
                            self.cube[3][2][0] == self.solved_cube[0][2][2] and self.cube[1][0][2] == c1 or
                            self.cube[1][0][2] == self.solved_cube[0][2][2] and self.cube[4][2][2] == c1) and

                           # white cross
                           (self.cube[0][1][2] == self.cube[0][0][1] == self.cube[0][1][0] == self.cube[0][2][1]
                                == self.solved_cube[0][1][1]) and

                           # white edges
                           self.cube[3][0][1] == self.cube[3][1][1] and
                           self.cube[5][0][1] == self.cube[5][1][1] and
                           self.cube[2][0][1] == self.cube[2][1][1] and
                           self.cube[4][0][1] == self.cube[4][1][1] and

                           # solved corners
                           (c1 == self.solved_cube[3][0][0] or

                            c1 == self.solved_cube[5][0][0] and
                                self.cube[0][2][0] == self.solved_cube[0][2][0] and
                                self.cube[4][0][0] == self.solved_cube[3][0][0] or

                            c1 == self.solved_cube[2][0][0] and
                                self.cube[0][2][0] == self.solved_cube[0][2][0] and
                                self.cube[4][0][0] == self.solved_cube[5][0][0] and

                                self.cube[0][0][0] == self.solved_cube[0][0][0] and
                                self.cube[2][0][0] == self.solved_cube[3][0][0] or

                            c1 == self.solved_cube[4][0][0] and
                                self.cube[0][2][0] == self.solved_cube[0][2][0] and
                                self.cube[4][0][0] == self.solved_cube[2][0][0] and

                                self.cube[0][0][0] == self.solved_cube[0][0][0] and
                                self.cube[2][0][0] == self.solved_cube[5][0][0] and

                                self.cube[0][0][2] == self.solved_cube[0][0][2] and
                                self.cube[5][0][0] == self.solved_cube[3][0][0])):

                    if i == 0:
                        backup_cube = copy.deepcopy(self.cube)

                    elif i == search_deep_2:
                        self.cube = copy.deepcopy(backup_cube)
                        i = 0

                    cubie = self.search_corner(c1, c2)

                    self.move_corner(cubie)

                    i += 1
                    moves += 1
                    self.solve_moves += 1

                    if not moves % reset_point:
                        self.solve_1()

                        restart = True
                        break

                if restart:
                    break

                if self.cube[4][2][2] == self.solved_cube[0][2][2]:
                    self.turn_bottom_rev()
                    self.turn_right_rev()
                    self.turn_bottom()
                    self.turn_right()

                elif self.cube[1][0][2] == self.solved_cube[0][2][2]:
                    self.turn_right_rev()
                    self.turn_bottom()
                    self.turn_right()
                    self.turn_bottom()
                    self.turn_bottom()

                # fall through
                if self.cube[3][2][0] == self.solved_cube[0][2][2] and self.cube[1][0][2] == c1:
                    self.turn_right_rev()
                    self.turn_bottom_rev()
                    self.turn_right()

                # next corner
                self.move_y()

        # yellow layer up
        self.move_x()
        self.move_x()

    # solve second layer
    def solve_3(self):

        # to right
        def move_edge():
            self.turn_top()
            self.turn_right()
            self.turn_top_rev()
            self.turn_right_rev()
            self.turn_top_rev()
            self.turn_front_rev()
            self.turn_top()
            self.turn_front()

            self.solve_moves += 8

        while not (self.cube[3][1][0] == self.cube[3][1][1] == self.cube[3][1][2] and
                   self.cube[5][1][0] == self.cube[5][1][1] == self.cube[5][1][2] and
                   self.cube[2][1][0] == self.cube[2][1][1] == self.cube[2][1][2] and
                   self.cube[4][1][0] == self.cube[4][1][1] == self.cube[4][1][2]):

            i = 0
            while not (self.cube[4][0][1] == self.cube[4][1][1] and self.cube[0][2][1] != self.solved_cube[1][1][1]):
                self.turn_top()

                i += 1
                self.solve_moves += 1

                if not i % 4:
                    self.turn_equator()
                    self.turn_bottom_rev()

                    self.solve_moves += 2

                if not i % 16:
                    move_edge()

            if self.cube[0][2][1] == self.cube[3][1][1]:
                move_edge()

            # to left
            else:
                self.turn_top_rev()
                self.turn_left_rev()
                self.turn_top()
                self.turn_left()
                self.turn_top()
                self.turn_front()
                self.turn_top_rev()
                self.turn_front_rev()

                self.solve_moves += 8

### start rest of stuff

    def scramble(self, nrdict={}):
        # restore savegame
        if nrdict:
            self.cube     = nrdict["cube"]
            self.buf_undo = nrdict["undo"]
            self.buf_redo = nrdict["redo"]

            self.speed_timer = self.game_timer = nrdict["time"]
        # new game
        else:
            self.cube = copy.deepcopy(self.solved_cube)

            for _ in range(scramble_moves):
                self.functions[random.randint(0, 11)]()

            self.buf_undo = self.buf_redo = ""
            self.speed_timer = self.game_timer = 0

        self.solve_stat = 0
        self.solve_cheat = False

        self.previous_time = time.time()
        self.pausing = False

    def get_input(self, key=""):
        dismiss = False  # dont save key in trace buffer

        try:
            if not key:
                key = self.stdscr.getkey()

            # control
            if key == undo:
                key = self.buf_undo[-1:]
                self.buf_redo += key
                self.buf_undo = self.buf_undo[:-1]

                key = key.upper() if key.islower() else key.lower()
                dismiss = True

            elif key == redo:
                if self.mode == self.modes["timer"]:
                    if self.pausing:
                        if (not self.speed_timer or
                            self.speed_timer == self.place_1 or
                            self.speed_timer == self.place_2 or
                            self.speed_timer == self.place_3):
                                self.msg_buf = ""

                        elif not self.place_1 or self.speed_timer < self.place_1:
                            if self.speed_timer < self.place_1:
                                self.place_3 = self.place_2
                                self.place_2 = self.place_1

                            self.place_1 = self.speed_timer
                            self.msg_buf = "*** 1. Place ***"

                        elif not self.place_2 or self.speed_timer < self.place_2:
                            if self.speed_timer < self.place_2:
                                self.place_3 = self.place_2

                            self.place_2 = self.speed_timer
                            self.msg_buf = "** 2. Place **"

                        elif not self.place_3 or self.speed_timer < self.place_3:
                            self.place_3 = self.speed_timer
                            self.msg_buf = "* 3. Place *"

                        self.solve_stat = time.time() + msg_time

                else:
                    key = self.buf_redo[-1:]
                    self.buf_redo = self.buf_redo[:-1]

            elif key == delete:
                key = self.buf_undo[-1:]
                self.buf_undo = self.buf_undo[:-1]

                key = key.upper() if key.islower() else key.lower()
                dismiss = True

            elif key == toredo:
                self.buf_redo += self.buf_undo[-1:]
                self.buf_undo = self.buf_undo[:-1]

            elif key == tonull:
                self.buf_undo = self.buf_undo[:-1]

            elif key == reset:
                if self.mode == self.modes["timer"]:
                    self.place_1 = self.place_2 = self.place_3 = self.solve_stat = 0
                else:
                    self.scramble()

            elif key == cheat:
                self.cube = copy.deepcopy(self.solved_cube)
                self.solve_cheat = True
                self.solve_stat = time.time() + msg_time
                self.msg_buf = '*cheat'

            elif key in (solve_1, solve_2, solve_3):
                self.solve_moves = 0
                solve_time = time.time()

                self.solve_1()

                if key in (solve_2, solve_3):
                    self.solve_2()

                if key == solve_3:
                    self.solve_3()

                self.solve_stat = time.time()
                solve_time = self.solve_stat - solve_time  # call time.time() only once
                self.solve_stat += msg_time

                self.msg_buf = "{} moves in {:.2f}s".format(self.solve_moves, solve_time)

            elif key == layout:
                self.mode = (self.mode + 1) % 4
                self.solve_stat = 0

                if self.mode == self.modes["timer"]:
                    self.speed_timer = self.tick = 0
                    self.pausing = True

                    if timer_ticks:
                        os.spawnlp(os.P_NOWAIT, player, player, option, timer_ticks[0][1])

                elif self.mode == self.modes["nrubik_bw"]:
                    self.speed_timer = self.game_timer

                    self.pausing = False

                if self.mode == self.modes["nrubik2"]:
                    curses.init_pair(1, curses.COLOR_WHITE,   curses.COLOR_WHITE)
                    curses.init_pair(2, curses.COLOR_YELLOW,  curses.COLOR_YELLOW)
                    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
                    curses.init_pair(4, curses.COLOR_RED,     curses.COLOR_RED)
                    curses.init_pair(5, curses.COLOR_GREEN,   curses.COLOR_GREEN)
                    curses.init_pair(6, curses.COLOR_BLUE,    curses.COLOR_BLUE)
                else:
                    curses.init_pair(1, curses.COLOR_WHITE,   -1)
                    curses.init_pair(2, curses.COLOR_YELLOW,  -1)
                    curses.init_pair(3, curses.COLOR_MAGENTA, -1)
                    curses.init_pair(4, curses.COLOR_RED,     -1)
                    curses.init_pair(5, curses.COLOR_GREEN,   -1)
                    curses.init_pair(6, curses.COLOR_BLUE,    -1)

            elif key == pause:
                # pause speedcube timer only
                if self.mode == self.modes["timer"]:
                    self.pausing = not self.pausing

                    if not self.pausing:
                        self.speed_timer = self.tick = self.solve_stat = 0

                        self.previous_time = time.time()
                # insert a gap/marker in trace buffer
                else:
                    key = marker

            elif key == quit:
                self.looping = False

            elif key == gtimer:
                self.show_gt = not self.show_gt

            elif key in (cube_out, cube_out_zen):
                if self.mode != self.modes["timer"]:
                    nrdict = {"cube": self.cube, "undo": self.buf_undo, "redo": self.buf_redo, "time": self.game_timer}

                    try:
                        fn = os.path.join(cube_dir, time.strftime(cube_file))

                        if self.solved():
                            fn += '+'

                        if key == cube_out_zen:
                            if find_exe('zenity'):
                                fn = (os.popen("zenity --file-selection --filename %s --save --confirm-overwrite" %
                                        cube_dir).read().strip())
                            else:
                                raise

                        assert fn.startswith(cube_dir)  # security check

                        with open(fn, 'w') as fileout:
                            fileout.write(str(nrdict))

                        self.msg_buf = 'save %s' % os.path.basename(fn)

                    except:
                        self.msg_buf = 'Error Out'

                    self.solve_stat = time.time() + msg_time

            elif key in (cube_in, cycle_down, cycle_up, cube_in_zen):
                if self.mode != self.modes["timer"]:
                    try:
                        flist = [f for f in sorted(os.listdir(cube_dir)) if
                                    os.path.isfile(os.path.join(cube_dir, f))]

                        if key == cube_in:
                            fn = os.path.join(cube_dir, flist[-1])

                            self.msg_buf = "load %s" % os.path.basename(fn)

                        elif key in (cycle_down, cycle_up):
                            if key == cycle_down:
                                if not self.load_index or (self.load_index > len(flist)):
                                    self.load_index = len(flist)  # circular load

                                self.load_index -= 1
                            else:
                                self.load_index += 1

                                if self.load_index >= len(flist):
                                    self.load_index = 0

                            fn = os.path.join(cube_dir, flist[self.load_index])

                            self.msg_buf = "load %d. %s" % (self.load_index + 1, os.path.basename(fn))
                        else:
                            if find_exe('zenity'):
                                fn = os.popen("zenity --file-selection --filename %s" % cube_dir).read().strip()

                                self.msg_buf = "load %s" % os.path.basename(fn)
                            else:
                                raise

                        with open(fn) as filein:
                            nrdict = eval(filein.read(), {'__builtins__': None}, {})  # str to dict

                        self.scramble(nrdict)

                        self.savegame = fn  # successful loaded game may be kicked
                    except:
                        self.msg_buf = 'Error In'

                    self.solve_stat = time.time() + msg_time

            elif key in (cube_kill, cube_kill_zen):
                if self.mode != self.modes["timer"]:
                    try:
                        if key == cube_kill:
                            assert self.savegame.startswith(cube_dir)
                            os.remove(self.savegame)

                            self.msg_buf = "kill %s" % os.path.basename(self.savegame)
                            self.savegame = ""
                        else:
                            if find_exe('zenity'):
                                fs = (os.popen("zenity --file-selection --filename %s --multiple" %
                                        cube_dir).read().strip().split('|'))

                                self.msg_buf = "kill %d file" % len(fs) + ('s', '')[len(fs) == 1]

                                for f in fs:
                                    assert f.startswith(cube_dir)
                                    os.remove(f)
                            else:
                                raise
                    except:
                        self.msg_buf = 'Error Del'

                    self.solve_stat = time.time() + msg_time

            # auto play
            elif key in (auto, auto_rec):
                if self.mode != self.modes["timer"]:
                    try:
                        if find_exe('zenity'):
                            if key == auto:
                                cmd = ("zenity --list --width 400 --height 300 --title 'auto generate' "
                                       "--print-column ALL --column Hotkey --column Hint --column Sequence")

                                for i in sorted(auto_play):
                                    cmd += " " + i + " " + auto_play[i]

                                self.msg_buf = os.popen(cmd).read().strip().split('|')

                                self.auto_buf = self.msg_buf[2]
                                self.msg_buf  = self.msg_buf[1]

                            else:
                                self.msg_buf  = auto_play['0'].split()[1]

                                cmd = "zenity --entry --title 'record Macro' --text 'Enter keys for 0' --entry-text "

                                self.msg_buf = os.popen(cmd + self.msg_buf).read().strip()

                                if self.msg_buf:
                                    auto_play['0'] = 'macro '

                                    for i in self.msg_buf:
                                        if i in moves or i == marker:
                                            auto_play['0'] += i
                                        else:
                                            auto_play['0'] += '_'

                                    self.msg_buf = auto_play['0']
                        else:
                            raise
                    except:
                        self.msg_buf = 'Error Auto'

                    self.solve_stat = time.time() + msg_time

            elif key in auto_play:
                self.auto_buf = auto_play[key].split()[1]
                self.msg_buf  = auto_play[key].split()[0]

                self.solve_stat = time.time() + msg_time

            ### reset key loop

            # trace buffer
            if (key in moves or key == marker) and not dismiss:
                self.buf_undo += key

            # moves
            if key == up:
                self.turn_top()
            elif key == up.upper():
                self.turn_top_rev()

            elif key == down:
                self.turn_bottom()
            elif key == down.upper():
                self.turn_bottom_rev()

            elif key == left:
                self.turn_left()
            elif key == left.upper():
                self.turn_left_rev()

            elif key == right:
                self.turn_right()
            elif key == right.upper():
                self.turn_right_rev()

            elif key == front:
                self.turn_front()
            elif key == front.upper():
                self.turn_front_rev()

            elif key == back:
                self.turn_back()
            elif key == back.upper():
                self.turn_back_rev()

            # inconsistently reversed!
            elif key == middle:
                self.turn_middle_rev()
            elif key == middle.upper():
                self.turn_middle()

            # inconsistently reversed!
            elif key == equator:
                self.turn_equator_rev()
            elif key == equator.upper():
                self.turn_equator()

            elif key == standing:
                self.turn_standing()
            elif key == standing.upper():
                self.turn_standing_rev()

            elif key == cube_x:
                self.move_x()
            elif key == cube_x.upper():
                self.move_x_rev()

            elif key == cube_y:
                self.move_y()
            elif key == cube_y.upper():
                self.move_y_rev()

            elif key == cube_z:
                self.move_z()
            elif key == cube_z.upper():
                self.move_z_rev()

            self.refresh = True

        except curses.error:
            pass

    def loop(self):
        loop_counter = 0  # dividend for timer refresh

        while self.looping:
            current_time = time.time()

            if not self.pausing:
                self.speed_timer += current_time - self.previous_time

                if self.mode != self.modes["timer"]:
                    if int(self.speed_timer) > self.game_timer:
                        self.game_timer = int(self.speed_timer)

                        self.refresh = True

            self.previous_time = current_time

            self.get_input()

            if self.auto_buf and not loop_counter % 63:  # delay 0.25s
                self.get_input(self.auto_buf[0])
                self.auto_buf = self.auto_buf[1:]

            if self.refresh:
                self.max_y, self.max_x = self.stdscr.getmaxyx()

                self.stdscr.erase()

                self.helper()
                self.headline()

                self.display_cube()

                self.stdscr.refresh()

                self.refresh = False

            if self.mode == self.modes["timer"] and not loop_counter % 25:  # display timer every 0.1s
                self.timer()

                if timer_ticks[self.tick:] and not self.pausing and (self.speed_timer > timer_ticks[self.tick][0]):
                    os.spawnlp(os.P_NOWAIT, player, player, option, timer_ticks[self.tick][1])

                    self.tick += 1

            loop_counter += 1

            time.sleep(0.004)  # timer precision

def main(stdscr):
    cube = Cube(stdscr)
    cube.loop()

if __name__ == '__main__':
    curses.wrapper(main)

