#!/usr/bin/python

from gcode import *
from config import *

#define operations to run here
operations = [
                Rectangle(Point(0, 0, -.125), Point(1, 1, -.125), .25).generate(True),
                #Bore(Point(1.25, 1.25, 0), .5, .5, toolDiameter).generate(),
                #rapidTravel(Point(-3, 1, 1)),
                ]

#generate program from the list of operations
generateProgram(operations)
