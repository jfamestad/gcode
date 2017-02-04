safeZ = .1 # obstruction free height assumed safe for rapid movement
feedRate = 6
plungeRate = 3 
toolDiameter = .25 
depthPerPass = min(.05, toolDiameter / 4)
overlap = .4 # multiplier for overlap between passes such that stepover = toolDiameter * (1 - overlap)
