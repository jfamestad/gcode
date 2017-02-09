#!/usr/bin/python

import inspect

from config import *

verbose = True
log_filename = 'gcode.log'

def log(message):
    with open(log_filename, 'w') as log_file:
        log_file.write(message)


class Point:
    def __init__(self, x=None, y=None, z=None):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        string = ''
        if self.x:
            string += "X%f " % self.x
        if self.y:
            string += "Y%f " % self.y
        if self.z:
            string += "Z%f" % self.z
        return string

class Arc:
    def __init__(self, endPoint, radius):
        self.endPoint = endPoint
        self.radius = radius

    def generate(self):
        return gCommand(2, point=self.endPoint, r=self.radius, f=feedRate)

class CounterArc:
    def __init__(self, endPoint, radius):
        self.endPoint = endPoint
        self.radius = radius

    def generate(self):
        return gCommand(3, point=self.endPoint, r=self.radius, f=feedRate)

class Circle:
    def __init__(self, center, radius, toolDiameter=0, mode='OD'):
        self.center = center
        self.radius = radius - toolDiameter / 2 if mode == 'OD' else radius + toolDiameter / 2
        self.findPoints()

    def findPoints(self):
        p1 = Point(self.center.x, self.center.y + self.radius, self.center.z)
        p2 = Point(self.center.x - self.radius, self.center.y, self.center.z)
        p3 = Point(self.center.x, self.center.y - self.radius, self.center.z)
        p4 = Point(self.center.x + self.radius, self.center.y, self.center.z)
        self.points = [p1, p2, p3, p4]

    def generate(self, startFromSafeZ=True):
        commands = []
        if startFromSafeZ:
            commands.append(gCommand(0, z=safeZ))
            commands.append(gCommand(0, x=self.points[0].x, y=self.points[0].y))
            commands.append(gCommand(1, z=self.center.z, f=plungeRate))
        else:
            commands.append(gCommand(1, point=self.points[0], f=feedRate))
        commands.append(CounterArc(self.points[1], self.radius).generate())
        commands.append(CounterArc(self.points[2], self.radius).generate())
        commands.append(CounterArc(self.points[3], self.radius).generate())
        commands.append(CounterArc(self.points[0], self.radius).generate())
        return commands

class Disk:
    def __init__(self, center, radius, toolDiameter):
        self.center = center
        self.radius = radius
        self.toolDiameter = toolDiameter
        self.findCircles()

    def findCircles(self):
        c1 = Circle(self.center, self.radius, self.toolDiameter, 'OD')
        self.circles = [c1]
        nextRadius = self.radius - self.toolDiameter * (1 - overlap)
        while (nextRadius >= 0):
            c = Circle(self.center, nextRadius, self.toolDiameter, 'OD')
            self.circles.append(c)
            nextRadius -= self.toolDiameter * (1-overlap)

    def generate(self, startFromSafeZ=True):
        commands = []
        firstCircle = self.circles.pop(0)
        commands.extend(firstCircle.generate(startFromSafeZ))
        for circle in self.circles:
            commands.extend(circle.generate(False))
        return commands

class Bore:
    def __init__(self, centerTop, radius, depth, toolDiameter):
        self.centerTop = centerTop
        self.radius = radius
        self.depth = depth
        self.toolDiameter = toolDiameter
        self.findDisks()

    def findDisks(self):
        centerX = self.centerTop.x
        centerY = self.centerTop.y
        nextZ = self.centerTop.z - depthPerPass
        disks = []
        while nextZ > self.centerTop.z - self.depth:
            center = Point(centerX, centerY, nextZ)
            disks.append(Disk(center, self.radius, self.toolDiameter))
            nextZ -= depthPerPass
        bottomDiskCenter = Point(self.centerTop.x, self.centerTop.y, self.centerTop.z - self.depth)
        disks.append(Disk(bottomDiskCenter, self.radius, self.toolDiameter))
        self.disks = disks

    def generate(self, startFromSafeZ=True):
        commands = []
        firstDisk = self.disks.pop(0)
        commands.extend(firstDisk.generate(startFromSafeZ))
        for disk in self.disks:
            commands.extend(disk.generate(False))
        return commands

class Rectangle:
    def __init__(self, lowerLeft, topRight, toolDiameter):
        self.lowerLeft = lowerLeft
        self.topRight = topRight
        self.toolDiameter = toolDiameter
        self.commands = []

    @property
    def boundaries(self):
        return {
                "minX": self.lowerLeft.x,
                "minY": self.lowerLeft.y,
                "maxX": self.topRight.x,
                "maxY": self.topRight.y
                }

    def generateRoughInterior(self, startFromSafeZ=True):
        log("generating toolpath to rough interior")
        if startFromSafeZ:
            self.commands.append(goTo(Point(z=safeZ)))
            self.commands.append(goTo(Point(x=self.lowerLeft.x, y=self.lowerLeft.y, z=safeZ)))
        self.commands.append(feed(self.lowerLeft))
        y = self.boundaries['minY'] + self.toolDiameter / 2
        while y < self.boundaries['maxY'] - self.toolDiameter / 2:
            self.commands.append(feed(Point(x=(self.boundaries['minX'] + self.toolDiameter / 2), y=y, z=0)))
            self.commands.append(feed(Point(x=(self.boundaries['maxX'] - self.toolDiameter / 2), y=y, z=0)))
            y += self.toolDiameter * ( 1 - overlap )
        log("roughing toolpath: %s" % self.commands)
        return self.commands
               
    def generatePerimeter(self, startFromSafeZ=True):
        if startFromSafeZ:
            self.commands.append(goTo(Point(z=safeZ)))
        self.commands.append(feed(Point(self.boundaries['maxX'], self.boundaries['maxY'])))
        self.commands.append(feed(Point(self.boundaries['maxX'], self.boundaries['minY'])))
        self.commands.append(feed(Point(self.boundaries['minX'], self.boundaries['minY'])))
        self.commands.append(feed(Point(self.boundaries['minX'], self.boundaries['maxY'])))
        self.commands.append(feed(Point(self.boundaries['maxX'], self.boundaries['maxY'])))
        return self.commands

    def generate(self, startFromSafeZ=True):
        self.generateRoughInterior(startFromSafeZ)
        self.generatePerimeter(startFromSafeZ)
        return self.commands

def feed(point):
    return gCommand(1, point=point, f=feedRate)

def goTo(point):
    return gCommand(0, point=point)

def gCommand(g, x=None, y=None, z=None, point=None, f=None, r=None):
    if point:
        x = point.x
        y = point.y
        z = point.z
    command = "G%d" % g
    if x:
        command = "%s X%f" % (command, x)
    if y:
        command = "%s Y%f" % (command, y)
    if z:
        command = "%s Z%f" % (command, z)
    if r:
        command = "%s R%f" % (command, r)
    if f:
        command = "%s F%f" % (command, f)
    return command

def rapidTravel(point):
    return(
            goTo(Point(z=safeZ)),
        
        goTo(Point(point.x, point.y, safeZ)),
            goTo(point),
          )

def generateProgram(operations):
    program = []
    for operation in operations:
        program.extend(operation)
    print "%"
    print goTo(Point(z=safeZ))
    for line in program:
        print line
    print goTo(Point(z=safeZ))
    print "%"
