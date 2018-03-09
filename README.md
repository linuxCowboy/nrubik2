# nrubik2
An N-Curses Based, Virtual Rubik's Cube (complete)

This new version was inspired by the original **nrubik**.

![Nrubik2](nrubik2.jpg?raw=true)

 - Full movements implemented
 - Full undo/redo support
 - Stoppable timer
 - Two layouts
 - Three challenges

![Solved](nrubik2-solved.jpg?raw=true)

 - Optimized for an 80x24 screen
 - Best played with big font sizes (e.g. Monospace 20)
 - Works with both python2 and python3

New feature: to redo + to null

```
Undo:    delete from undo, add to redo, play reverse move   
Redo:    delete from redo, add to undo, play move   
Delete:  delete from undo, play reverse move   
2 Redo:  delete from undo, add to redo   
2 Null:  delete from undo   
```
Experiment with (new) moves!
