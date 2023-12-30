import vsketch
import numpy as np
from beartype import beartype
from dataclasses import dataclass
from collections import defaultdict
from typing import Optional
from shapely import Point, LineString, Polygon, MultiPolygon, box
import ipdb

SHEET_HEIGHT=297 #mm Y
SHEET_WIDTH=420 #mm X


CELL_WIDTH=30 #mm
NUM_X_CELLS=(SHEET_WIDTH - 50) // CELL_WIDTH
NUM_Y_CELLS=(SHEET_HEIGHT - 50) // CELL_WIDTH
VSK_SCALE = 10 * (CELL_WIDTH / 3)


NUM_LANES = 6
NUM_PATHS = 2
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

    def equiv2d(self, other):
        if other is None:
            return False
        return self.x == other.x and self.y == other.y



class MazePath:
    def __init__(self):
        self.points: list[Coord] = []

    @staticmethod
#    @beartype
    def _genStartCoord() -> Coord:
        return Coord(np.random.randint(0, NUM_X_CELLS), np.random.randint(0, NUM_Y_CELLS), lane=NUM_LANES-1)

#    @beartype
    def addPoint(self, point: Coord):
        self.points.append(point)

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
    
    def tryMoveHere(self, currentCoord: Optional[Coord], newCoord: Coord):
        pathsAtCoord = self.pathsTaken[newCoord.x, newCoord.y, :]
        unusedLanes = self.indices[~pathsAtCoord]

        if currentCoord is not None:
            currentLane = currentCoord.lane
        elif len(unusedLanes) > 0:
            currentLane = np.random.choice(unusedLanes)
        else:
            return None

        if currentLane in unusedLanes:
            possNewLanes = []
            if currentLane + 1 in unusedLanes:
                possNewLanes.append(currentLane + 1)
            if currentLane - 1 in unusedLanes:
                possNewLanes.append(currentLane - 1)
            if possNewLanes:
                newLane = np.random.choice(possNewLanes)
                pathsAtCoord[newLane] = True
                pathsAtCoord[currentLane] = True
                return newLane
        return None


#    @beartype
    def getHowManyLanesInUse(self, coord: Coord):
        pathsAtCoord = self.pathsTaken[coord.x, coord.y, :]
        return pathsAtCoord.sum()

def randomColor():
    return f"rgb({np.random.randint(0,256)},{np.random.randint(0,256)},{np.random.randint(0,256)})"

class ShapelyDrawing:
    @staticmethod
    def drawPaths(vsk, paths):
        # ipdb.set_trace()

               

        nonOccluded = defaultdict(list)

        def getGridSquare(x,y):
            return box(x-0.5,y-0.5,x+0.5,y+0.5)

        for pathIndex, path in enumerate(paths):
            coords = path.points
            coordsExtended = [coords[0]] + coords + [coords[-1]]
            for seg in zip(coordsExtended, coordsExtended[1:],coordsExtended[2:]):
                point = seg[1]
                segSimple = [(p.x,p.y) for p in seg]

                line = LineString(segSimple)
                buffered = line.buffer(0.4)
                gridSquare = getGridSquare(point.x,point.y)
                geomToDraw = buffered.boundary.intersection(gridSquare)
                geomMask = buffered.intersection(gridSquare)
                nonOccluded[segSimple[1]].append((point.lane, pathIndex, geomToDraw, geomMask))

        for coord, geomAtCoord in nonOccluded.items():
            geomAtCoord = sorted(geomAtCoord, key = lambda tup: tup[0])[::-1]
    
            occlusionGeom = Polygon()             
            for lane, pathIndex, geomToDraw, geomMask in geomAtCoord:
                geomToDrawOccluded = geomToDraw.difference(occlusionGeom)
                with vsk.pushMatrix():
                    vsk.scale(VSK_SCALE)
                    vsk.stroke(pathIndex+1)
                    vsk.strokeWeight(3)
                    vsk.geometry(geomToDrawOccluded)
                occlusionGeom = occlusionGeom.union(geomMask)



class RandomPathGenerator:
    @staticmethod
    def getPaths():
        paths = []
        globalLaneTracker = GlobalLaneTracker()
        
        for i in range(NUM_PATHS):
            path = MazePath()

            for moveIndex in range(500):
                possNewCoords = path.possNewCoords()
                np.random.shuffle(possNewCoords)
                possNewCoords.sort(key=globalLaneTracker.getHowManyLanesInUse)
                newCoord = possNewCoords[0]

                if (lane := globalLaneTracker.tryMoveHere(path.getLastCoord(), newCoord)) is not None:
                    newCoord.lane = lane
                    path.addPoint(newCoord)
            print("Length of path is ", len(path.points))

            paths.append(path)

        return paths

class MazeSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        # vsk.penWidth("5mm")

        paths = RandomPathGenerator.getPaths()

        ### Drawing
        
        # draw the grid
        # vsk.stroke(len(paths)+1)
        # for i in range(NUM_X_CELLS):
        #     lineStart = Coord(i, 0, 0).toSVGCoord()
        #     lineEnd = Coord(i, NUM_Y_CELLS -1, 0).toSVGCoord()
        #     vsk.line(lineStart.x, lineStart.y, lineEnd.x, lineEnd.y)
                    
        # for i in range(NUM_Y_CELLS):
        #     lineStart = Coord(0, i, 0).toSVGCoord()
        #     lineEnd = Coord(NUM_X_CELLS-1, i, 0).toSVGCoord()
            # vsk.line(lineStart.x, lineStart.y, lineEnd.x, lineEnd.y)

        ShapelyDrawing.drawPaths(vsk, paths)


    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    MazeSketch.display(colorful=True, grid=True)
