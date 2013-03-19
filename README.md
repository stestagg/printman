printman
========

Code for the world's slowest game of pacman.

Designed as a little printer[http://bergcloud.com/littleprinter/] publication, 
this app allows people to play very slow games of pacman, with one move per day.

Design
------
Code takes ascii-art board definitions like this:
```
+----+--------+----+
|....|........|....|
|.+-.|.------.|.-+.|
|.|..............|.|
|.|.--.+-==-+.--.|.|
|......|MNOP|......|
|.|.--.+----+.--.|.|
|.|..............|.|
|.+-.|.------.|.-+.|
|....|....c...|....|
+------------------+
```
And from that, generates graphics for board outline, and correctly sized pacmans etc.. (gfx.py)
Also calculated routes and information needed for playing game, and allows games to be started.