#!/usr/bin/python

from config import *

class Point:
    def __init__(self, x=None, y=None, z=None):
        self.x = x
        self.y = y
        self.z = z

class Arc:
    def __init__(self, endPoint, radius):
        self.endPoint = endPoint
        self.radius = radius

    def generate(self):
        return "G2 X%f Y%f R%s F%f" % (self.endPoint.x, self.endPoint.y, self.radius, feedRate)

class CounterArc:
    def __init__(self, endPoint, radius):
        self.endPoint = endPoint
        self.radius = radius

    def generate(self):
        return "G3 X%f Y%f R%s F%f" % (self.endPoint.x, self.endPoint.y, self.radius, feedRate)

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
            commands.append("G0 Z%f" % safeZ)
            commands.append("G0 X%f Y%f" % (self.points[0].x, self.points[0].y))
            commands.append("G1 Z%f F%f" % (self.center.z, plungeRate))
        else:
            commands.append("G1 X%f Y%f Z%f F%f" % (self.points[0].x, self.points[0].y, self.points[0].z, feedRate))
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
    def __init__(self, lowerLeft, topRight):
        self.lowerLeft = lowerLeft
        self.topRight = topRight

    @property
    def boundaries(self):
        return {
                "minX": self.lowerLeft.x,
                "minY": self.lowerLeft.y,
                "maxX": self.topRight.x,
                "maxY": self.topRight.y
                }

    def generateRoughInterior(self):
        pass

    def generatePerimeter(self):
        pass

    def generate(self):
        pass

def goTo(point):
    command = "G0"
    if point.x:
        command = "%s X%f" % (command, point.x)
    if point.y:
        command = "%s Y%f" % (command, point.y)
    if point.z:
        command = "%s Z%f" % (command, point.z)
    return command

def gCommand(g, x=None, y=None, z=None, point=None, f=None, r=None):
    if point:
        x = point.x
        y = point.y
        y = point.z
    command = "G%d" % g
    if x:
        command = "%s X%f" % (command, point.x)
    if y:
        command = "%s Y%f" % (command, point.y)
    if z:
        command = "%s Z%f" % (command, point.z)
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
