import vsketch
from terraintiles import TerrainTiles, calcContourLines
import rasterio

import ipdb

from scipy import ndimage

from matplotlib import pyplot as plt
import numpy as np
from copy import copy

import time

timerA = 0.0
timerB = 0.0
timerC = 0.0

class ContoursSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def drawContourLine(self, vsk, heightMask):
        global timerA, timerB, timerC

        # heightMask = np.array(
        #     [
        #         [False,False,False,True,True,False,False],
        #         [False,False,False,True,True,False,False],
        #         [False,False,False,True,True,False,False],
        #         [False,False,True,True,True,True,False],
        #         [False,True ,True,True,True,True,False],
        #         [False,False,False,True,False,False,False],
        #         [False,False,True,False,True,False,False],
        #         [False,True,True,False,True,True,False],
        #         [False,True,True,False,True,True,False],
        #         [False,False,False,False,False,False,False],
        #     ]
        # )

        # heightMask = np.array(
        #     [
        #         [False,False,False],
        #         [False,True,False],
        #         [False,False,False],
  
        #     ]
        # )

        width = heightMask.shape[1]
        height = heightMask.shape[0]

        #walk along the contour keeping them to the left


        settingToNewDir = {
            (0,1): {
                ((False, True), (True, True)): ((-1,0), (-1, 1)),
                ((False, True), (False, True)): ((0,1), (0,1)),
                ((False, True), (False, False)): ((1,0), (0,0)),
                ((False, True), (True, False)): ((1,0), (0,0)),
            },
            (0,-1): {
                ((True, True), (True, False)): ((1,0), (1,-1)),
                ((True, False), (True, False)): ((0,-1), (0,-1)),
                ((False, False), (True, False)): ((-1,0), (0,0)),
                ((False, True), (True, False)): ((-1,0), (0,0)),
            },
            (1,0): {
                ((True, True), (False, True)): ((0,1), (1,1)),
                ((True, True), (False, False)): ((1,0), (1,0)),
                ((True, False), (False, False)): ((0,-1), (0,0)),
                ((True, False), (False, True)): ((0,-1), (0,0)),
            },
            (-1,0): {
                ((True, False), (True, True)): ((0,-1), (-1,-1)),
                ((False, False), (True, True)): ((-1,0), (-1,0)),
                ((False, False), (False, True)): ((0, 1), (0,0)),
                ((True, False), (False, True)): ((0,1), (0,0)),
            },
        }


        def getNeighbourhoodCoords(x,y,dir):
            """
            if you are in the middle of setting facing dir, back left will be True, back right will be False
            """
            if dir == (0,1):
                return ((x-1, y), (x,y), (x-1,y+1), (x, y+1))
            if dir == (0,-1):
                return ((x,y-1), (x+1,y-1), (x,y), (x+1,y))
            if dir == (1,0):
                return ((x,y), (x+1,y), (x, y+1), (x+1,y+1))
            if dir == (-1,0):
                return ((x-1,y-1), (x, y-1), (x-1,y), (x,y))
            assert False


        def getSetting(x,y, dir):
            neighborhoodCoords = getNeighbourhoodCoords(x,y,dir)
            if not all((0<=x_< width) and (0<=y_ < height) for (x_,y_) in neighborhoodCoords):
                return None
            (x0,y0), (x1,y1), (x2,y2), (x3,y3) = neighborhoodCoords
            return ((heightMask[y0,x0],heightMask[y1,x1]), (heightMask[y2,x2],heightMask[y3,x3]))
        dirs = ((0,1), (0,-1), (1,0), (-1,0))

        start = time.time()
        # find 2x2 ares of interest
        coordsNearLineAndDir = {}
        for y,x in zip(*np.nonzero(heightMask)):
            directNeighbours = heightMask[max(y-1,0):min(y+1,height), max(x-1,0):min(x+1,width)]
            if np.all(directNeighbours) or not np.any(directNeighbours):
                continue
            for dir in dirs:
                setting = getSetting(x,y,dir)
                if setting is not None and setting in settingToNewDir[dir]:
                    coordsNearLineAndDir[(x,y, dir)] = setting
        timerA += time.time() - start
        start = time.time()

        # for i in range(height):
        #     for j in range(width):
        #         if heightMask[i,j]:
        #             vsk.circle(j,i, radius=0.2)
        #         if (j,i, dirs[0]) in coordsNearLineAndDir:
        #             vsk.circle(j,i, radius=0.01)

        # ipdb.set_trace()
        paths = []
        while coordsNearLineAndDir:
            (x, y, dir), setting = coordsNearLineAndDir.popitem()
            path = []
            while True:
                path.append((x,y))
   
                dir, transition = settingToNewDir[dir][setting]
                x += transition[0]
                y += transition[1]

                if (x,y, dir) not in coordsNearLineAndDir:
                    path.append((x,y))
                    break
                setting = coordsNearLineAndDir.pop((x,y,dir))

            print(len(path))
            paths.append(path)

        timerB += time.time() - start
        start = time.time()

        # merge paths
        def findTwoPaths(paths):
            for i1, p1 in enumerate(paths):
                for i2, p2 in enumerate(paths):
                    endP1 = p1[-1]
                    startP2 = p2[0]
                    if i1 != i2 and endP1 == startP2:
                        return i1, i2
            return None

        while res := findTwoPaths(paths):
            i1, i2 = res
            paths[i1] = paths[i1] + paths[i2][1:]
            del paths[i2]

        # draw paths
        for i, path in enumerate(paths):
            vsk.stroke(i+1)
            vsk.polygon(path)
        timerC += time.time() - start



    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("mm")


        with rasterio.open('terraintile_cache/11/311/682.tif') as tileDataset:
            contourLines = calcContourLines(tileDataset.read(1))
        
        for contourLine in contourLines:
            self.drawContourLine(vsk, contourLine[:250, :250])
        
        print(f"{timerA=}")
        print(f"{timerB=}")
        print(f"{timerC=}")

        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    ContoursSketch.display()
