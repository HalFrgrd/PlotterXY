
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

NUM_LANES = 2
NUM_PATHS = 4
np.random.seed(1)

PATH_WIDTH_MULT=0.8


################## Drawing

dwg = svgwrite.Drawing(profile="full", size=(f"{SHEET_WIDTH}mm",f"{SHEET_HEIGHT}mm"))
dwg.viewbox(0,0,SHEET_WIDTH, SHEET_HEIGHT)




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


    def equiv2d(self, other):
        if other is None:
            return False
        return self.x == other.x and self.y == other.y

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
    
    def __lt__(self, other):
        return self.x < other.x or self.y < other.y


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
        return Coord(np.random.randint(0, NUM_X_CELLS), np.random.randint(0, NUM_Y_CELLS), lane=NUM_LANES-1)

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
        return [point for point in possPoints if (not point.equiv2d(secondToLastPoint)) and point.isValid()]

    @beartype
    def getLastCoord(self) -> Optional[Coord]:
        if self.points:
            return self.points[-1]
        return None


class GlobalLaneTracker:
    indices = np.arange(NUM_LANES)

    # self.pathsTaken[i,j,k] == True means there is a path at coord i,j

    
    def __init__(self):
        self.pathsTaken = np.zeros((NUM_X_CELLS,NUM_Y_CELLS,NUM_LANES)).astype(bool)
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


    @beartype
    def getHowManyLanesInUse(self, coord: Coord):
        pathsAtCoord = self.pathsTaken[coord.x, coord.y, :]
        return pathsAtCoord.sum()

paths = []
globalLaneTracker = GlobalLaneTracker()
   
for i in range(NUM_PATHS):
    path = MazePath()

    for move_num in range(30):
        possNewCoords = path.possNewCoords()
        np.random.shuffle(possNewCoords)
        possNewCoords.sort(key=globalLaneTracker.getHowManyLanesInUse)
        newCoord = possNewCoords[0]

        if (lane := globalLaneTracker.tryMoveHere(path.getLastCoord(), newCoord)) is not None:
            newCoord.lane = lane
            path.addPoint(newCoord)
        else:
            print("Length of path is ", len(path.points))
            break

    paths.append(path)

def randomColor():
    return f"rgb({np.random.randint(0,256)},{np.random.randint(0,256)},{np.random.randint(0,256)})"


@beartype
def isLeft(a: SVGCoord, b: SVGCoord, c: SVGCoord):
    return (b.x - a.x)*(c.y - a.y) - (b.y - a.y)*(c.x - a.x) > 0

class SimpleDrawing:

    @staticmethod
    @beartype
    def drawArc(start, end, radius=None):
        path = svgwrite.path.Path('m', stroke=color, fill="none")
        path.push((start.x, start.y))
        if radius is None:
            radius = max(abs((start-end).x), abs((start-end).y))
        path.push_arc(target=(end.x, end.y), rotation=0, large_arc=False, r=radius, absolute=True)
        dwg.add(path)

    @staticmethod
    @beartype
    def getRectangleStartEnd(start: SVGCoord, end: SVGCoord) -> tuple[SVGCoord, SVGCoord]:
        dir = end-start
        offset = CELL_WIDTH * 0.4
        if dir.y == 0:
            return start+(0, offset), end-(0,offset)
        if dir.x == 0:
            return start+(offset, 0), end-(offset, 0)
        assert False


    @staticmethod
    @beartype
    def getLineCoords(start: SVGCoord, end: SVGCoord) -> tuple[SVGCoord, SVGCoord, SVGCoord, SVGCoord]:
        dir = end-start
        offset = CELL_WIDTH * 0.36
        if dir.y == 0:
            return start+(0, offset), start-(0, offset), end+(0,offset), end-(0,offset)
        if dir.x == 0:
            return start+(offset, 0), start-(offset, 0), end+(offset, 0), end-(offset, 0)
        assert False

    @staticmethod
    @beartype
    def drawRectStartEnd(start: SVGCoord, end:SVGCoord, color, opacity):
        startX = min(start.x, end.x)
        startY = min(start.y, end.y)
        endX = max(start.x, end.x)
        endY = max(start.y, end.y)

        rect = dwg.rect((startX, startY), (endX-startX, endY-startY), stroke=color, fill="none")
        # rect['fill-opacity'] = opacity
        dwg.add(rect)

        # dwg.add(dwg.line((startX, startY), (endX, endY), stroke="black", stroke_width = 1))


    @staticmethod
    def drawSegmentMid(segmentStart: Coord, segmentEnd: Coord, color,completion):
        assert segmentStart.isValid() and segmentEnd.isValid()

        startA, startB, endA, endB = SimpleDrawing.getLineCoords(
                SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.45),
                SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.55)
            )
        #     color,
        #     completion,
        # )

        dwg.add(dwg.line((startA.x, startA.y), (endA.x, endA.y), stroke=color, stroke_width = 1))
        dwg.add(dwg.line((startB.x, startB.y), (endB.x, endB.y), stroke=color, stroke_width = 1))


    @staticmethod
    @beartype
    def getCornerPoints(start: SVGCoord, end: SVGCoord, applyTo: SVGCoord) -> tuple[SVGCoord, SVGCoord]:
        dir = end-start
        if dir.y == 0:
            offset = abs(dir.x) * PATH_WIDTH_MULT
            # print(offset)
            a,b = applyTo+(0, offset), applyTo-(0,offset)
            # dwg.add(dwg.line((a.x, a.y), (b.x, b.y), stroke="black", stroke_width = 1))
            return a,b

        if dir.x == 0:
            offset = abs(dir.y) * PATH_WIDTH_MULT
            a,b  = applyTo+(offset, 0), applyTo-(offset, 0)
            # dwg.add(dwg.line((a.x, a.y), (b.x, b.y), stroke="black", stroke_width = 1))
            return a,b
        assert False

    @staticmethod
    @beartype
    def getEndCapPoints(start: SVGCoord, end: SVGCoord) -> tuple[SVGCoord, SVGCoord]:
        dir = end-start
        if dir.y == 0:
            offset_y = abs(dir.x) * 0.45
            offset_x = dir.x * 0.35
            # print(offset)
            a,b = end+(-offset_x, offset_y), end-(offset_x,offset_y)
            # dwg.add(dwg.line((a.x, a.y), (b.x, b.y), stroke="black", stroke_width = 1))
            return a,b

        if dir.x == 0:
            offset_x = abs(dir.y) * 0.35
            offset_y = dir.y * 0.45
            a,b  = end+(offset_x, -offset_y), end-(offset_x, offset_y)
            # dwg.add(dwg.line((a.x, a.y), (b.x, b.y), stroke="black", stroke_width = 1))
            return a,b
        assert False

    @beartype
    @staticmethod
    def drawSegment(prevPoint: Optional[Coord], point: Coord, nextPoint: Optional[Coord], color,completion):
        # assert segmentStart.isValid() and segmentEnd.isValid()

        if nextPoint is None: # we are the end
            oldA, oldB = SimpleDrawing.getEndCapPoints(
                    prevPoint.toSVGCoord(),
                    point.toSVGCoord(),
                    )
            if isLeft(prevPoint.toSVGCoord(), point.toSVGCoord(), oldA):
                oldA, oldB = oldB, oldA
            SimpleDrawing.drawArc(oldA, oldB, CELL_WIDTH*0.35*0.5)
            return


        if prevPoint is None: # starting
            oldA, oldB = SimpleDrawing.getEndCapPoints(
                    nextPoint.toSVGCoord(),
                    point.toSVGCoord(),
                    )
            if isLeft(nextPoint.toSVGCoord(), point.toSVGCoord(), oldA):
                oldA, oldB = oldB, oldA
            SimpleDrawing.drawArc(oldA, oldB, CELL_WIDTH*0.35*0.5)
            return

        if (prevPoint.x == point.x == nextPoint.x) or (prevPoint.y == point.y == nextPoint.y):

            SimpleDrawing.drawRectStartEnd(
                *SimpleDrawing.getRectangleStartEnd(
                    SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), point.toSVGCoord(), 0.55),
                    SVGCoord.interpolateSVGCoords(point.toSVGCoord(), nextPoint.toSVGCoord(), 0.45)
                ),
                color,
                completion,
            )

        else:


            
            oldA, oldB = SimpleDrawing.getCornerPoints(
                    SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), point.toSVGCoord(), 0.55),
                    point.toSVGCoord(),
                    applyTo=SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), point.toSVGCoord(), 0.55),
                    )
            if not isLeft(prevPoint.toSVGCoord(), point.toSVGCoord(), oldA):
                oldA, oldB = oldB, oldA
            assert isLeft(prevPoint.toSVGCoord(), point.toSVGCoord(), oldA)

            newA, newB = SimpleDrawing.getCornerPoints(
                    point.toSVGCoord(),
                    SVGCoord.interpolateSVGCoords(point.toSVGCoord(), nextPoint.toSVGCoord(), 0.45),
                    applyTo=SVGCoord.interpolateSVGCoords(point.toSVGCoord(), nextPoint.toSVGCoord(), 0.45),
                )
            if not isLeft(point.toSVGCoord(), nextPoint.toSVGCoord(), newA):
                newA, newB = newB, newA
            assert isLeft(point.toSVGCoord(), nextPoint.toSVGCoord(), newA)
            # points = sorted(points)
            # shape = svgwrite.shapes.Polygon([(oldA.x, oldA.y),(oldB.x, oldB.y),(newB.x, newB.y),(newA.x, newA.y)], fill=color)
            # shape["fill-opacity"] = completion
            # dwg.add(shape)

            # def drawArc(start, end):
            #     path = svgwrite.path.Path('m', stroke=color, fill="none")
            #     path.push((start.x, start.y))
            #     path.push_arc(target=(end.x, end.y), rotation=0, large_arc=False, r=max(abs((start-end).x), abs((start-end).y)), absolute=True)
            #     dwg.add(path)

            if isLeft(prevPoint.toSVGCoord(), point.toSVGCoord(), nextPoint.toSVGCoord()):
                SimpleDrawing.drawArc(oldA, newA)
                SimpleDrawing.drawArc(oldB, newB)
            else:
                SimpleDrawing.drawArc(newA, oldA)
                SimpleDrawing.drawArc(newB, oldB)

        # SimpleDrawing.drawRectStartEnd(
        #     *SimpleDrawing.getRectangleStartEnd(
        #         SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.75),
        #         segmentEnd.toSVGCoord()
        #     ),
        #     color,
        #     completion,
        # )

for x in range(NUM_X_CELLS):
    dwg.add(dwg.line(Coord(x,0, None).toSVGCoord().tup(), Coord(x,NUM_Y_CELLS-1, None).toSVGCoord().tup(), stroke="black", stroke_width = 1))
for y in range(NUM_Y_CELLS):
    dwg.add(dwg.line(Coord(0,y, None).toSVGCoord().tup(), Coord(NUM_X_CELLS-1, y, None).toSVGCoord().tup(), stroke="black", stroke_width = 1))


for path in paths:
    color = randomColor()

    for i, (segmentStart, segmentEnd) in enumerate(zip(path.points, path.points[1:])):
        completion = 1.0 #(i / len(path.points))* 0.6 + 0.4

        if globalLaneTracker.isHighestPathAtMid(segmentStart, segmentEnd):
            SimpleDrawing.drawSegmentMid(segmentStart, segmentEnd, color, completion)
    


    for i, (prevPoint, point, nextPoint) in enumerate(zip([None] + path.points, path.points, path.points[1:]+[None])):
        completion = 1.0# (i / len(path.points))* 0.6 + 0.4
        if globalLaneTracker.isHighestPathAtEnd(point):
            SimpleDrawing.drawSegment(prevPoint, point, nextPoint, color, completion)
            text = svgwrite.text.Text(f"({i},{point.x},{point.y})", insert=(point.toSVGCoord().x, point.toSVGCoord().y),  fill = 'black')
            text['font-size'] = '30%'
            text['font-family'] = 'Courier New'
            dwg.add(text)


# drawRectStartEnd((20,20),(60,60))(stroke="black", stroke_width=1)

# path = svgwrite.path.Path('m', stroke=color, fill="black")
# path.push(Coord(0,NUM_Y_CELLS-2, None).toSVGCoord().tup())
# path.push_arc(target=Coord(1,NUM_Y_CELLS-1, None).toSVGCoord().tup(), rotation=0, large_arc=False, r=CELL_WIDTH, absolute=True)
# dwg.add(path)

dwg.saveas("maze.svg", pretty=True)
        
import ipdb
ipdb.set_trace()
