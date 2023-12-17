
import svgwrite
import numpy as np
from beartype import beartype
from dataclasses import dataclass
from collections import defaultdict
from typing import Optional
import ipdb

################## CONFIG

SHEET_HEIGHT=297 #mm Y
SHEET_WIDTH=420 #mm X

STROKE_WIDTH = 10

CELL_WIDTH=30 #mm
NUM_X_CELLS=(SHEET_WIDTH - 50) // CELL_WIDTH
NUM_Y_CELLS=(SHEET_HEIGHT - 50) // CELL_WIDTH



################## Drawing

dwg = svgwrite.Drawing(profile="full", size=(f"{SHEET_WIDTH}mm",f"{SHEET_HEIGHT}mm"))
dwg.viewbox(0,0,SHEET_WIDTH, SHEET_HEIGHT)
np.random.seed(0)




@dataclass
class Coord:
    x: int
    y: int
    lane: int

    def shiftWest(self):
        return Coord(self.x - 1, self.y, None)
    def shiftEast(self):
        return Coord(self.x + 1, self.y, None)
    def shiftNorth(self):
        return Coord(self.x, self.y+1, None)
    def shiftSouth(self):
        return Coord(self.x, self.y-1, None)

    def isValid(self):
        return 0<= self.x < NUM_X_CELLS and 0<=self.y < NUM_Y_CELLS
    

    def __sub__(self, other):
        if isinstance(other, tuple):
            assert len(other) == 2
            other = Coord(other[0], other[1])
        
        return Coord(self.x - other.x, self.y - other.y, None)

    _SVG_OFFSET_X = (SHEET_WIDTH - CELL_WIDTH * NUM_X_CELLS) * 0.5
    _SVG_OFFSET_Y = (SHEET_HEIGHT- CELL_WIDTH * NUM_Y_CELLS) * 0.5
    @beartype
    def toSVGCoord(self) -> 'SVGCoord':
        return SVGCoord(self._SVG_OFFSET_X + self.x * CELL_WIDTH, self._SVG_OFFSET_Y + self.y * CELL_WIDTH)

@dataclass
class SVGCoord:
    x: float
    y: float

    def __add__(self, other):
        if isinstance(other, tuple):
            assert len(other) == 2
            other = SVGCoord(other[0], other[1])
        
        return SVGCoord(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        if isinstance(other, tuple):
            assert len(other) == 2
            other = SVGCoord(other[0], other[1])
        
        return SVGCoord(self.x - other.x, self.y - other.y)
    
    @beartype
    def __mul__(self, f: float):
        return SVGCoord(self.x*f, self.y*f)


    @staticmethod
    @beartype
    def interpolateSVGCoords(start:  'SVGCoord', end:  'SVGCoord', proportion: float):
        return start + (end - start)*proportion


    def tup(self):
        assert self.x >=0
        assert self.x < SHEET_WIDTH
        assert self.y >=0
        assert self.y < SHEET_HEIGHT
        return (self.x, self.y)

class MazePath:
    def __init__(self):
        self.points: list[Coord] = []

    @staticmethod
    @beartype
    def _genStartCoord() -> Coord:
        return Coord(np.random.randint(0, NUM_X_CELLS), np.random.randint(0, NUM_Y_CELLS), 2)

    @beartype
    def addPoint(self, point: Coord):
        self.points.append(point)
    
    @beartype
    def possNewCoords(self) -> list[Coord]:
        if len(self.points) == 0:
            return [self._genStartCoord()]
            
        lastPoint = self.points[-1]
        secondToLastPoint = self.points[-2] if len(self.points) >= 2 else None
        possPoints = [lastPoint.shiftWest(), lastPoint.shiftEast(), lastPoint.shiftSouth(), lastPoint.shiftNorth()]
        return [point for point in possPoints if point != secondToLastPoint and point.isValid()]

    @beartype
    def getLastCoord(self) -> Optional[Coord]:
        if self.points:
            return self.points[-1]
        return None


class GlobalLaneTracker:
    NUM_SPOTS_PER_CELL = 5
    indices = np.arange(NUM_SPOTS_PER_CELL)

    # self.pathsTaken[i,j,k] == True means there is a path at coord i,j

    
    def __init__(self):
        self.pathsTaken = np.zeros((NUM_X_CELLS,NUM_Y_CELLS,self.NUM_SPOTS_PER_CELL)).astype(bool)
        self.transitions = defaultdict(list)

    def isHighestPathAtStart(self, coord: Coord):
        pathsAtCoord = self.pathsTaken[coord.x, coord.y, :]
        assert coord.lane >= 0
        # ipdb.set_trace()
        assert pathsAtCoord[coord.lane]
        return np.any(pathsAtCoord[coord.lane+1:]) == False

    def isHighestPathAtMid(self, segmentStart: Coord, segmentEnd: Coord):
        # pathsAtStart = self.pathsTaken[segmentStart.x, segmentStart.y, :]
        # pathsAtEnd = self.pathsTaken[segmentEnd.x, segmentEnd.y, :]
        # assert pathsAtStart[segmentStart.z]
        # assert pathsAtEnd[segmentEnd.z]
        


        transitionsSameDir = self.transitions[(segmentStart.x, segmentStart.y, segmentEnd.x, segmentEnd.y)]
        transitionsOppoDir = self.transitions[(segmentEnd.x, segmentEnd.y, segmentStart.x, segmentStart.y)]

        assert (segmentStart.lane, segmentEnd.lane) in transitionsSameDir

        # isHighestTransitionAtCoord = True
        for (transitionZ_1, transitionZ_2) in transitionsSameDir + transitionsOppoDir:
            if transitionZ_1+transitionZ_2 > segmentStart.lane+ segmentEnd.lane: # TODO better height metric
                return False
        return True

    
    def isHighestPathAtEnd(self, coord: Coord):
        pathsAtCoord = self.pathsTaken[coord.x, coord.y, :]
        assert pathsAtCoord[coord.lane]
        return np.any(pathsAtCoord[coord.lane+1:]) == False
    
    def tryMoveHere(self, currentCoord: Optional[Coord], newCoord: Coord):
        pathsAtCoord = self.pathsTaken[newCoord.x, newCoord.y, :]
        unusedIndices = self.indices[~pathsAtCoord]
        if unusedIndices.size > 0:
            lane = np.random.choice(unusedIndices)
            pathsAtCoord[lane] = True
            # ipdb.set_trace()
            if currentCoord is not None:
                self.transitions[(currentCoord.x, currentCoord.y, newCoord.x, newCoord.y)].append((currentCoord.lane, lane))

            return lane
        return None



paths = []
globalLaneTracker = GlobalLaneTracker()
   
for i in range(1):
    path = MazePath()

    for move_num in range(30):
        possNewCoords = path.possNewCoords()
        newCoord = np.random.choice(possNewCoords)

        if (lane := globalLaneTracker.tryMoveHere(path.getLastCoord(), newCoord)) is not None:
            newCoord.lane = lane
            path.addPoint(newCoord)
        else:
            print("Length of path is ", len(path.points))
            break

    paths.append(path)

def randomColor():
    return f"rgb({np.random.randint(0,256)},{np.random.randint(0,256)},{np.random.randint(0,256)})"




class SimpleDrawing:

    @staticmethod
    @beartype
    def getRectangleStartEnd(start: SVGCoord, end: SVGCoord) -> tuple[SVGCoord, SVGCoord]:
        dir = end-start
        offset = CELL_WIDTH * 0.2
        if dir.y == 0:
            return start+(0, offset), end-(0,offset)
        if dir.x == 0:
            return start+(offset, 0), end-(offset, 0)
        assert False

    @staticmethod
    @beartype
    def drawRectStartEnd(start: SVGCoord, end:SVGCoord, color, opacity):
        startX = min(start.x, end.x)
        startY = min(start.y, end.y)
        endX = max(start.x, end.x)
        endY = max(start.y, end.y)

        rect = dwg.rect((startX, startY), (endX-startX, endY-startY), fill=color)
        rect['fill-opacity'] = opacity

        return dwg.add(rect)

    # @staticmethod
    # def drawSegmentStart(prevSegmentEnd: Coord, segmentStart: Coord, segmentEnd: Coord, color, completion):
    #     assert segmentStart.isValid() and segmentEnd.isValid()

    #     SimpleDrawing.drawRectStartEnd(
    #         *SimpleDrawing.getRectangleStartEnd(
    #             segmentStart.toSVGCoord(),
    #             SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.25)
    #         ),
    #         color,
    #         completion,

    #     )

    @staticmethod
    def drawSegmentMid(segmentStart: Coord, segmentEnd: Coord, color,completion):
        assert segmentStart.isValid() and segmentEnd.isValid()

        SimpleDrawing.drawRectStartEnd(
            *SimpleDrawing.getRectangleStartEnd(
                SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.25),
                SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.75)
            ),
            color,
            completion,
        )

    @staticmethod
    @beartype
    def getCornerPoints(pointA: SVGCoord, pointB: SVGCoord) -> tuple[SVGCoord, SVGCoord]:
        dir = end-start
        offset = CELL_WIDTH * 0.2
        if dir.y == 0:
            return start+(0, offset), end-(0,offset)
        if dir.x == 0:
            return start+(offset, 0), end-(offset, 0)
        assert False

    @staticmethod
    def drawSegment(prevPoint: Coord, point: Coord, nextPoint: Coord, color,completion):
        # assert segmentStart.isValid() and segmentEnd.isValid()

        if (prevPoint.x == point.x == nextPoint.x) or (prevPoint.y == point.y == nextPoint.y):

            SimpleDrawing.drawRectStartEnd(
                *SimpleDrawing.getRectangleStartEnd(
                    SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), point.toSVGCoord(), 0.85),
                    SVGCoord.interpolateSVGCoords(point.toSVGCoord(), nextPoint.toSVGCoord(), 0.15)
                ),
                color,
                completion,
            )

        else:

            points = [
                *SimpleDrawing.getCornerPoints(prevPoint.toSVGCoord(), point.toSVGCoord())
            ]

            # points = [
            #     *SimpleDrawing.getRectangleStartEnd(
            #         SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), segmentEnd.toSVGCoord(), 0.25),
            #         SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.75)
            #     ),
            #     *SimpleDrawing.getRectangleStartEnd(
            #         SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.25),
            #         SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.75)
            #     ),
            # ]

            dwg.add(svgwrite.shapes.Polygon(points, fill=color))
            

        # SimpleDrawing.drawRectStartEnd(
        #     *SimpleDrawing.getRectangleStartEnd(
        #         SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.75),
        #         segmentEnd.toSVGCoord()
        #     ),
        #     color,
        #     completion,
        # )


for path in paths:
    color = randomColor()

    for i, (segmentStart, segmentEnd) in enumerate(zip(path.points, path.points[1:])):
        completion = (i / len(path.points))* 0.8 + 0.2
        # if globalLaneTracker.isHighestPathAtMid(segmentStart, segmentEnd):
        SimpleDrawing.drawSegmentMid(segmentStart, segmentEnd, color, completion)
    
    for i, (prevPoint, point, nextPoint) in enumerate(zip(path.points, path.points[1:], path.points[2:])):
        completion = (i / len(path.points))* 0.8 + 0.2
        if globalLaneTracker.isHighestPathAtEnd(segmentEnd):
            SimpleDrawing.drawSegment(prevPoint, point, nextPoint, color, completion)


for x in range(NUM_X_CELLS):
    dwg.add(dwg.line(Coord(x,0, None).toSVGCoord().tup(), Coord(x,NUM_Y_CELLS-1, None).toSVGCoord().tup(), stroke="black", stroke_width = 1))
for y in range(NUM_Y_CELLS):
    dwg.add(dwg.line(Coord(0,y, None).toSVGCoord().tup(), Coord(NUM_X_CELLS-1, y, None).toSVGCoord().tup(), stroke="black", stroke_width = 1))

# drawRectStartEnd((20,20),(60,60))(stroke="black", stroke_width=1)


dwg.saveas("maze.svg", pretty=True)
        
import ipdb
ipdb.set_trace()
