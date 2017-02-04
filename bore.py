#!/usr/bin/python

from gcode import *
from config import *

#define operations to run here
operations = [
                Bore(Point(1.25, 1.25, 0), .5, .5, toolDiameter).generate(),
                #rapidTravel(Point(-3, 1, 1)),
                ]

#generate program from the list of operations
generateProgram(operations)
