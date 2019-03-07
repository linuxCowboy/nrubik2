# nrubik2
An N-Curses Based, Virtual Rubik's Cube (complete)

![Nrubik2](image/nrubik2.jpg?raw=true)

 - Full movements implemented
 - Full undo/redo support
 - Game timer
 - Savegames
 - Macros

![New](image/nrubik2-new.jpg?raw=true)

 - Optimized for an 80x24 screen
 - Best played with big font sizes (e.g. Monospace 20)

![Solved](image/nrubik2-solved.jpg?raw=true)

This new version was inspired by the original **nrubik**.

![Nrubik-bw](image/nrubik-bw.jpg?raw=true)

![Nrubik-color](image/nrubik-color.jpg?raw=true)

-----
New Feature: to redo + to null

```
Undo:    delete from undo, add to redo, play reverse move
Redo:    delete from redo, add to undo, play move
Delete:  delete from undo, play reverse move
2 Redo:  delete from undo, add to redo
2 Null:  delete from undo

Space:   insert marker
```

-----
New Timer-Mode:

 - Speedcubing Timer 1/100s
 - optional acoustic feedback
 - program different chimes for different times
 - needs cmdline audio player
 - default: "aplay" (alsa-utils)
 - cmdline option for timer ticks

-----
Solver:

```
 1) white cross + edges
 2) white corners
 3) second layer
```

-----
Savegames:

 - auto timestamp
 - manual naming
 - circular restore
 - in-game delete
 - uses **zenity**

-----
Macros:

 - auto generate keys
 - up to 7 macros
 - Hints with *zenity*

-----
Profiler:

```
 1) search_deep_1 and scramble_moves
 2) search_deep_2 and reset_point
```

-----
Patterns:

![Nest](image/nest.jpg?raw=true)
Nest

![Z-Line](image/z-line.jpg?raw=true)
Z-line

![Zigzag](image/zigzag.jpg?raw=true)
Zigzag

![Checkerboard](image/checkerboard.jpg?raw=true)
Checkerboard
