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
NUM_PATHS = 3
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
#    @beartype
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
    
#    @beartype
    def __mul__(self, f: float):
        return SVGCoord(self.x*f, self.y*f)
    
    def __lt__(self, other):
        return self.x < other.x or self.y < other.y


    @staticmethod
#    @beartype
    def interpolateSVGCoords(start, end, proportion: float):
        return start + (end - start)*proportion


    def tup(self):
        assert self.x >=0
        assert self.x < SHEET_WIDTH
        assert self.y >=0
        assert self.y < SHEET_HEIGHT
        return (self.x, self.y)
    
    def rotate(self, toBeRotated: 'SVGCoord', angleDegrees):
        translated = toBeRotated-self
        x,y = translated.x, translated.y
        radians = angleDegrees / 360 * 2*np.pi
        c = np.cos(radians)
        s = np.sin(radians)
        rotated = SVGCoord(x * c - y * s, x*s + y*c)
        return rotated + self


class MazeSegment:
    def __init__(self, prev, point, next):
        self.prev = prev
        self.point = point
        self.next = next


class MazePath:
    def __init__(self):
        self.points: list[Coord] = []
        self.segments = []

    @staticmethod
#    @beartype
    def _genStartCoord() -> Coord:
        return Coord(np.random.randint(0, NUM_X_CELLS), np.random.randint(0, NUM_Y_CELLS), lane=NUM_LANES-1)

#    @beartype
    def addPoint(self, point: Coord):
        self.points.append(point)
        if len(self.points) == 1:
            self.segments.append(MazeSegment(None,self.points[0], None))
        else:
            self.segments[-1].next = point
            self.segments.append(MazeSegment(self.points[-2], self.points[-1], None))

    
    # @beartype
    def possNewCoords(self) -> list[Coord]:
        if len(self.points) == 0:
            return [self._genStartCoord()]
            
        lastPoint = self.points[-1]
        secondToLastPoint = self.points[-2] if len(self.points) >= 2 else None
        possPoints = [lastPoint.shiftWest(), lastPoint.shiftEast(), lastPoint.shiftSouth(), lastPoint.shiftNorth()]
        return [point for point in possPoints if (not point.equiv2d(secondToLastPoint)) and point.isValid()]

#    @beartype
    def getLastCoord(self) -> Optional[Coord]:
        if self.points:
            return self.points[-1]
        return None


class GlobalLaneTracker:
    indices = np.arange(NUM_LANES)

    # self.pathsTaken[i,j,k] == True means there is a path at coord i,j
    def __init__(self):
        self.pathsTaken = np.zeros((NUM_X_CELLS,NUM_Y_CELLS,NUM_LANES)).astype(bool)

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
        # assert (segmentStart.lane, segmentEnd.lane) in transitionsSameDir

        # # isHighestTransitionAtCoord = True
        # for (transitionZ_1, transitionZ_2) in transitionsSameDir + transitionsOppoDir:
        #     if transitionZ_1+transitionZ_2 > segmentStart.lane+ segmentEnd.lane: # TODO better height metric
        #         return False
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
            # if currentCoord is not None:
            #     self.transitions[(currentCoord.x, currentCoord.y, newCoord.x, newCoord.y)].append((currentCoord.lane, lane))

            return lane
        return None


#    @beartype
    def getHowManyLanesInUse(self, coord: Coord):
        pathsAtCoord = self.pathsTaken[coord.x, coord.y, :]
        return pathsAtCoord.sum()

def randomColor():
    return f"rgb({np.random.randint(0,256)},{np.random.randint(0,256)},{np.random.randint(0,256)})"


#@beartype
def isLeft(a: SVGCoord, b: SVGCoord, c: SVGCoord):
    return (b.x - a.x)*(c.y - a.y) - (b.y - a.y)*(c.x - a.x) > 0

class SimpleDrawing:
    @staticmethod
    # @beartype
    def drawArc(vsk, start, end):
        """
        Draw a 90 degree arc between these two points.
        To the left of the line from start to end
        """

        radius = max(abs(end.x - start.x), abs(end.y-start.y))*2
   
        if start.x < end.x:
            if start.y < end.y:
                center = (start.x ,end.y)
                rotation = 0
                # return
            else:
                center = (end.x, start.y)
                rotation = 270
                # return
        else:
            if start.y < end.y:
                center = (end.x,start.y)
                rotation = 90
                # return
            else:
                center = (start.x,end.y)
                rotation = 180
                # return

        with vsk.pushMatrix():
            vsk.translate(*center)
            # vsk.translate(0, radius)
            vsk.rotate(rotation, degrees=True)
            vsk.arc(0,0, radius, radius, 0, 90, degrees=True, mode="center")

        # vsk.line(start.x, start.y, end.x, end.y)
        # vsk.circle(start.x, start.y, 1)

        # vsk.arc(*center, radius, radius, startAngle, stopAngle, degrees=True, mode="center")
        # vsk.line(start.x, start.y, end.x, end.y)




    @staticmethod
#    @beartype
    def getLineCoords(start: SVGCoord, end: SVGCoord) -> tuple[SVGCoord, SVGCoord, SVGCoord, SVGCoord]:
        dir = end-start
        offset = CELL_WIDTH * 0.36
        if dir.y == 0:
            return start+(0, offset), start-(0, offset), end+(0,offset), end-(0,offset)
        if dir.x == 0:
            return start+(offset, 0), start-(offset, 0), end+(offset, 0), end-(offset, 0)
        assert False


    @staticmethod
    def drawSegmentMid(vsk, segmentStart: Coord, segmentEnd: Coord):
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
    def drawEndCap(vsk, dir, center):
        assert dir.x == 0 or dir.y == 0
        if dir.x > 0:
            rotation = 90
        elif dir.x < 0:
            rotation = 270
        elif dir.y >0:
            rotation = 180
        elif dir.y <0:
            rotation = 0
        r = max(abs(dir.x),abs(dir.y))*0.8
        with vsk.pushMatrix():
            vsk.translate(*center.tup())
            vsk.rotate(rotation, degrees=True)
            vsk.arc(0, 0, w=r, h=r, start=0, stop=180, degrees=True, mode="center")

    @staticmethod
    def drawStraightSegment(vsk, prevPoint, point, nextPoint):
        dir = point - prevPoint

        offset = (0, CELL_WIDTH*0.4) if dir.y == 0 else (CELL_WIDTH*0.4, 0)
        startA = SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), point.toSVGCoord(), 0.50) + offset
        startB = SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), point.toSVGCoord(), 0.50) - offset

        endA = SVGCoord.interpolateSVGCoords(point.toSVGCoord(), nextPoint.toSVGCoord(), 0.50) + offset
        endB = SVGCoord.interpolateSVGCoords(point.toSVGCoord(), nextPoint.toSVGCoord(), 0.50) - offset

        vsk.line(startA.x, startA.y, endA.x, endA.y)
        vsk.line(startB.x, startB.y, endB.x, endB.y)


    @staticmethod
    def drawCornerSegment(vsk, prevPoint, point, nextPoint):
        # rotate so prevPoint is below point
        # dir = point - prevPoint
        # assert dir.x == 0 or dir.y == 0
        # if dir.x < 0:
        #     rotation = 90
        # elif dir.x < 0:
        #     rotation = -90
        # elif dir.y > 0:
        #     rotation = 180
        # else:
        #     rotation = -180

        # with vsk.pushMatrix():
        #     vsk.translate(point.x, point.y)
        #     vsk.rotate(rotation, degrees=True)

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


        if isLeft(prevPoint.toSVGCoord(), point.toSVGCoord(), nextPoint.toSVGCoord()):
            SimpleDrawing.drawArc(vsk, startA, endA)
            SimpleDrawing.drawArc(vsk, startB, endB)
        else:
            SimpleDrawing.drawArc(vsk, endA, startA)
            SimpleDrawing.drawArc(vsk, endB, startB)

#    @beartype
    @staticmethod
    def drawSegment(vsk, segment: MazeSegment, occluderSegment: MazeSegment):
        prevPoint = segment.prev
        point = segment.point
        nextPoint = segment.next
        if nextPoint is None or prevPoint is None: # draw end cap
            if nextPoint is None: # at the end
                dir = point.toSVGCoord() - prevPoint.toSVGCoord()
                center = point.toSVGCoord() #SVGCoord.interpolateSVGCoords(prevPoint.toSVGCoord(), point.toSVGCoord(), 0.5)
            elif prevPoint is None: # at the start
                dir =  point.toSVGCoord() - nextPoint.toSVGCoord()
                center = point.toSVGCoord() #SVGCoord.interpolateSVGCoords(point.toSVGCoord(), nextPoint.toSVGCoord(), 0.5)
            SimpleDrawing.drawEndCap(vsk, dir, center)

        elif (prevPoint.x == point.x == nextPoint.x) or (prevPoint.y == point.y == nextPoint.y):
            # straight line
            SimpleDrawing.drawStraightSegment(vsk, prevPoint, point, nextPoint)

        else:
            # round a corner
            SimpleDrawing.drawCornerSegment(vsk, prevPoint, point, nextPoint)


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

            for moveIndex in range(30):
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
        
        # draw the grid
        vsk.stroke(len(paths)+1)
        for i in range(NUM_X_CELLS):
            lineStart = Coord(i, 0, 0).toSVGCoord()
            lineEnd = Coord(i, NUM_Y_CELLS -1, 0).toSVGCoord()
            vsk.line(lineStart.x, lineStart.y, lineEnd.x, lineEnd.y)
                    
        for i in range(NUM_Y_CELLS):
            lineStart = Coord(0, i, 0).toSVGCoord()
            lineEnd = Coord(NUM_X_CELLS-1, i, 0).toSVGCoord()
            vsk.line(lineStart.x, lineStart.y, lineEnd.x, lineEnd.y)

        globalSegments = defaultdict(list)
        for path in paths:
            for segment in path.segments:
                globalSegments[(segment.point.x, segment.point.y)].append(segment)
        
        def getHighestSegmentAt(point: Coord):
            segmentsAtCoord = globalSegments[(point.x, point.y)]
            assert len(segmentsAtCoord)
            return max(segmentsAtCoord, key= lambda seg: seg.point.lane )

        for pathIndex, path in enumerate(paths):
            vsk.penWidth("0.5mm",pathIndex+1)
            vsk.stroke(pathIndex+1)

            # for i, (segmentStart, segmentEnd) in enumerate(zip(path.points, path.points[1:])):
            #     completion = 1.0 #(i / len(path.points))* 0.6 + 0.4
            #     if globalLaneTracker.isHighestPathAtMid(segmentStart, segmentEnd):
            #         SimpleDrawing.drawSegmentMid(vsk, segmentStart, segmentEnd, color, completion)
            
            for i, mazeSegment in enumerate(path.segments):
                # if globalLaneTracker.isHighestPathAtEnd(point):
                occluderSeg = getHighestSegmentAt(mazeSegment.point)
                SimpleDrawing.drawSegment(vsk, mazeSegment, occluderSeg)


    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    MazeSketch.display(colorful=True, grid=True)
