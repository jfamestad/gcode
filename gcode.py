#!/usr/bin/python

safeZ = .5
feedRate = 4
plungeRate = 3
toolDiameter = .25
depthPerPass = toolDiameter / 2
overlap = .1 # multiplier for overlap between passes such that stepover = toolDiameter * (1 - overlap)

class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Arc:
    def __init__(self, endPoint, radius):
        self.endPoint = endPoint
        self.radius = radius

    def generate(self):
        return "G2 X%f Y%f F%f" % (self.endPoint.x, self.endPoint.y, feedRate)

class CounterArc:
    def __init__(self, endPoint, radius):
        self.endPoint = endPoint
        self.radius = radius

    def generate(self):
        return "G2 X%f Y%f F%f" % (self.endPoint.x, self.endPoint.y, feedRate)

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

    def generate(self, safeZ=True):
        commands = []
        if safeZ:
            commands.append("G0 Z%f" % safeZ)
            commands.append("G0 X%f Y%f" % (self.points[0].x, self.points[0].y))
            commands.append("G1 Z%f F%f" % (self.center.z, plungeRate))
        else:
            commands.append("G1 X%f Y%f" % (self.points[0].x, self.points[0].y))
            commands.append("G1 Z%f F%f" % (self.points[0].z, plungeRate))
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

    def generate(self):
        commands = []
        for circle in self.circles:
            commands.extend(circle.generate())
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

    def generate(self):
        commands = []
        for disk in self.disks:
            commands.extend(disk.generate())
        return commands
        

program = []
program.extend(Bore(Point(0, 0, 0), 1, .5, toolDiameter).generate())
for line in program:
    print line
