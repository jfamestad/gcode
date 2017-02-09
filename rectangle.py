#!/usr/bin/python

from gcode import *
from config import *

#define operations to run here
operations = [
                rapidTravel(Point(0, 0, 1)),
                Rectangle(Point(0, 0, -.125), Point(5.5, 1.75, -.125), .25).generate(True),
                #Rectangle(Point(0, 0, -.125), Point(1, 1, -.125), .25).generateRoughInterior(True),
                #Rectangle(Point(0, 0, -.125), Point(1, 1, -.125), .25).generatePerimeter(True),
                ]

#generate program from the list of operations
generateProgram(operations)
