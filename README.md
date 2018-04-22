# nrubik2
An N-Curses Based, Virtual Rubik's Cube (complete)

![Nrubik2](nrubik2.jpg?raw=true)

 - Full movements implemented
 - Full undo/redo support
 - Game timer

![Solved](nrubik2-solved.jpg?raw=true)

 - Optimized for an 80x24 screen
 - Best played with big font sizes (e.g. Monospace 20)

This new version was inspired by the original **nrubik**.

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
 - default: "/usr/bin/aplay"

-----
Cheats:

```
 1) white cross + edges
 2) white corners
 3) second layer
```

 \+ Profiler

-----
Patterns:

![Nest](nest.jpg?raw=true)

![Z-Line](z-line.jpg?raw=true)

![Zigzag](zigzag.jpg?raw=true)

![Checkerboard](checkerboard.jpg?raw=true)
