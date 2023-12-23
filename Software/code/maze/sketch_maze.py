import vsketch
import numpy as np
from beartype import beartype
from dataclasses import dataclass
from collections import defaultdict
from typing import Optional

SHEET_HEIGHT=297 #mm Y
SHEET_WIDTH=420 #mm X


CELL_WIDTH=30 #mm
NUM_X_CELLS=(SHEET_WIDTH - 50) // CELL_WIDTH
NUM_Y_CELLS=(SHEET_HEIGHT - 50) // CELL_WIDTH


NUM_LANES = 2
NUM_PATHS = 1
np.random.seed(1)



################## Drawing


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
    def toSVGCoord(self):
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
    def interpolateSVGCoords(start, end, proportion: float):
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
            if currentCoord is not None:
                self.transitions[(currentCoord.x, currentCoord.y, newCoord.x, newCoord.y)].append((currentCoord.lane, lane))

            return lane
        return None


    @beartype
    def getHowManyLanesInUse(self, coord: Coord):
        pathsAtCoord = self.pathsTaken[coord.x, coord.y, :]
        return pathsAtCoord.sum()

def randomColor():
    return f"rgb({np.random.randint(0,256)},{np.random.randint(0,256)},{np.random.randint(0,256)})"


@beartype
def isLeft(a: SVGCoord, b: SVGCoord, c: SVGCoord):
    return (b.x - a.x)*(c.y - a.y) - (b.y - a.y)*(c.x - a.x) > 0

class SimpleDrawing:
    @staticmethod
    @beartype
    def drawArc(vsk, start, end, clockwise):
        """
        Draw a 90 degree arc between these two points
        """



   
        if start.x < end.x:
            if start.y < end.y:
                startAngle, stopAngle = 0, 270
            else:
                startAngle, stopAngle = 180, 90
        else:
            if start.y < end.y:
                startAngle, stopAngle = 90, 0
            else:
                startAngle, stopAngle = 90, 180

        vsk.line(start.x, start.y, end.x, end.y)
        vsk.circle(start.x, start.y, 1)

        if clockwise:
            vsk.arc(topLeft.x, topLeft.y, bottomRight.x, bottomRight.y, startAngle, stopAngle, degrees=True, mode="")
        # vsk.line(start.x, start.y, end.x, end.y)
        else:

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
    def drawRectStartEnd(vsk, start: SVGCoord, end:SVGCoord):
        startX = min(start.x, end.x)
        startY = min(start.y, end.y)
        endX = max(start.x, end.x)
        endY = max(start.y, end.y)

        vsk.rect(startX, startY, endX-startX, endY-startY)



    @staticmethod
    def drawSegmentMid(vsk, segmentStart: Coord, segmentEnd: Coord, color,completion):
        assert segmentStart.isValid() and segmentEnd.isValid()

        startA, startB, endA, endB = SimpleDrawing.getLineCoords(
                SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.45),
                SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.55)
            )
        #     color,
        #     completion,
        # )

        vsk.line(startA.x, startA.y, endA.x, endA.y)
        vsk.line(startB.x, startB.y, endB.x, endB.y)


    @staticmethod
    @beartype
    def getCornerPoints(start: SVGCoord, end: SVGCoord, applyTo: SVGCoord) -> tuple[SVGCoord, SVGCoord]:
        dir = end-start
        if dir.y == 0:
            offset = abs(dir.x) * 0.8
            a,b = applyTo+(0, offset), applyTo-(0,offset)
            return a,b

        if dir.x == 0:
            offset = abs(dir.y) * 0.8
            a,b  = applyTo+(offset, 0), applyTo-(offset, 0)
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
    def drawSegment(vsk, prevPoint: Optional[Coord], point: Coord, nextPoint: Optional[Coord]):
        # assert segmentStart.isValid() and segmentEnd.isValid()

        if nextPoint is None: # at the end
            startA, startB = SimpleDrawing.getEndCapPoints(
                    prevPoint.toSVGCoord(),
                    point.toSVGCoord(),
                    )
            if isLeft(prevPoint.toSVGCoord(), point.toSVGCoord(), startA):
                startA, startB = startB, startA
            # SimpleDrawing.drawArc(vsk, startA, startB, CELL_WIDTH*0.35*0.5)
            return


        if prevPoint is None: # at the start
            startA, startB = SimpleDrawing.getEndCapPoints(
                    nextPoint.toSVGCoord(),
                    point.toSVGCoord(),
                    )
            if isLeft(nextPoint.toSVGCoord(), point.toSVGCoord(), startA):
                startA, startB = startB, startA
            # SimpleDrawing.drawArc(vsk, startA, startB, CELL_WIDTH*0.35*0.5)
            return

        # straight line
        if (prevPoint.x == point.x == nextPoint.x) or (prevPoint.y == point.y == nextPoint.y):
            dir = point - prevPoint

            offset = (0, CELL_WIDTH*0.4) if dir.y == 0 else (CELL_WIDTH*0.4, 0)
            startA = SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), point.toSVGCoord(), 0.50) + offset
            startB = SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), point.toSVGCoord(), 0.50) - offset

            endA = SVGCoord.interpolateSVGCoords(point.toSVGCoord(), nextPoint.toSVGCoord(), 0.50) + offset
            endB = SVGCoord.interpolateSVGCoords(point.toSVGCoord(), nextPoint.toSVGCoord(), 0.50) - offset

            vsk.line(startA.x, startA.y, endA.x, endA.y)
            vsk.line(startB.x, startB.y, endB.x, endB.y)


        else: # round a corner

            startMidPoint = SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), point.toSVGCoord(), 0.50)
            startDir = point - prevPoint
            offset = (0, CELL_WIDTH*0.4) if startDir.y == 0 else (CELL_WIDTH*0.4, 0)            
            startA, startB = startMidPoint+offset, startMidPoint-offset
            if not isLeft(prevPoint.toSVGCoord(), point.toSVGCoord(), startA):
                startA, startB = startB, startA
            assert isLeft(prevPoint.toSVGCoord(), point.toSVGCoord(), startA)

            endMidPoint = SVGCoord.interpolateSVGCoords(point.toSVGCoord(), nextPoint.toSVGCoord(), 0.50)
            endDir = nextPoint - point
            offset = (0, CELL_WIDTH*0.4) if endDir.y == 0 else (CELL_WIDTH*0.4, 0)            
            endA, endB = endMidPoint+offset, endMidPoint-offset
            if not isLeft(point.toSVGCoord(), nextPoint.toSVGCoord(), endA):
                endA, endB = endB, endA
            assert isLeft(point.toSVGCoord(), nextPoint.toSVGCoord(), endA)


            # if isLeft(prevPoint.toSVGCoord(), point.toSVGCoord(), nextPoint.toSVGCoord()):
            SimpleDrawing.drawArc(vsk, startA, endA)
            SimpleDrawing.drawArc(vsk, startB, endB)
            # else:
            #     SimpleDrawing.drawArc(vsk, endA, startA)
            #     SimpleDrawing.drawArc(vsk, endB, startB)

        # SimpleDrawing.drawRectStartEnd(
        #     *SimpleDrawing.getRectangleStartEnd(
        #         SVGCoord.interpolateSVGCoords(segmentStart.toSVGCoord(), segmentEnd.toSVGCoord(), 0.75),
        #         segmentEnd.toSVGCoord()
        #     )
        # )


class MazeSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        # vsk.scale("mm")


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

        ### Drawing
        
        vsk.stroke(len(paths)+1)
            
        for i in range(NUM_X_CELLS):
            lineStart = Coord(i, 0, 0).toSVGCoord()
            lineEnd = Coord(i, NUM_Y_CELLS -1, 0).toSVGCoord()
            vsk.line(lineStart.x, lineStart.y, lineEnd.x, lineEnd.y)
                    
        for i in range(NUM_Y_CELLS):
            lineStart = Coord(0, i, 0).toSVGCoord()
            lineEnd = Coord(NUM_X_CELLS-1, i, 0).toSVGCoord()
            vsk.line(lineStart.x, lineStart.y, lineEnd.x, lineEnd.y)

        for pathIndex, path in enumerate(paths):
            color = None
            vsk.penWidth("0.5mm",pathIndex+1)
            vsk.stroke(pathIndex+1)

            # for i, (segmentStart, segmentEnd) in enumerate(zip(path.points, path.points[1:])):
            #     completion = 1.0 #(i / len(path.points))* 0.6 + 0.4
            #     if globalLaneTracker.isHighestPathAtMid(segmentStart, segmentEnd):
            #         SimpleDrawing.drawSegmentMid(vsk, segmentStart, segmentEnd, color, completion)
            

            for i, (prevPoint, point, nextPoint) in enumerate(zip([None] + path.points, path.points, path.points[1:]+[None])):
                if globalLaneTracker.isHighestPathAtEnd(point):
                    SimpleDrawing.drawSegment(vsk, prevPoint, point, nextPoint)
                    # text = svgwrite.text.Text(f"({i},{point.x},{point.y})", insert=(point.toSVGCoord().x, point.toSVGCoord().y),  fill = 'black')
                    # text['font-size'] = '30%'
                    # text['font-family'] = 'Courier New'
                    # dwg.add(text)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    MazeSketch.display(colorful=True, grid=True)
