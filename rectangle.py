#!/usr/bin/python

from gcode import *
from config import *

#define operations to run here
operations = [
                rapidTravel(Point(0, 0, 1)),
                Rectangle(Point(0, 0, -.125), Point(5.5, 1.75, -.125), .25).generate(True),
                #Bore(Point(1.25, 1.25, 0), .5, .5, toolDiameter).generate(),
                #rapidTravel(Point(-3, 1, 1)),
                ]

#generate program from the list of operations
generateProgram(operations)
