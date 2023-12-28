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
        #         [False,False,False,False,False,False,False],
        #         [False,False,False,False,True,False,False],
        #         [False,False,False,True,True,False,False],
        #         [False,False,True,True,True,True,False],
        #         [False,True ,True,True,True,True,False],
        #         [False,False,True,True,False,False,False],
        #         [False,True,True,False,False,False,False],
        #         [False,True,True,False,False,False,False],
        #         [False,True,True,False,False,False,False],
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

        # walk along the contour keeping them to the left
        # this is the first part of Potrace

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


        start = time.time()
        # find 2x2 areas of interest
        coordsNearLineAndDir = {}
        
        # get 2x2 views sliding over heightMask, copy to get better lookup speed
        settings = np.lib.stride_tricks.sliding_window_view(heightMask, (2,2)).copy()
        assert settings.flags.c_contiguous
        
        # convert the 2x2 bools into int32's
        settingsAsInt = settings.reshape((settings.shape[0],settings.shape[1]*4))
        settingsAsInt = settingsAsInt.view(np.int32)

        for dir in settingToNewDir.keys():
            for setting in settingToNewDir[dir].keys():
                # convert this setting to an int32
                settingAsInt = np.array(setting, dtype=bool).reshape(-1).view(np.int32)[0]
                matches = settingsAsInt == settingAsInt
                yMatches, xMatches = np.nonzero(matches)

                # change match coordinates by +/- 1 depending on dir
                # xMatches, yMatches will be for the top left, so we need to adjust
                if dir == (0,1):
                    xMatches += 1
                elif dir == (0,-1):
                    yMatches += 1
                elif dir == (1,0):
                    pass
                elif dir == (-1,0):
                    xMatches += 1
                    yMatches += 1

                for x,y in zip(xMatches, yMatches):
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
        import random
        while coordsNearLineAndDir:
            # random choice is better than popitem, much longer paths
            (x, y, dir)  = random.choice(list(coordsNearLineAndDir.keys()))
            setting = coordsNearLineAndDir.pop((x,y,dir))
            path = []
            while True:
                path.append((x,y))
   
                dir, (dx, dy) = settingToNewDir[dir][setting]
                x += dx
                y += dy

                if (x,y, dir) not in coordsNearLineAndDir:
                    path.append((x,y))
                    break
                setting = coordsNearLineAndDir.pop((x,y,dir))

            # print(len(path))
            paths.append(path)
            # vsk.stroke(len(paths)+1)
            # vsk.polygon(path)

        timerB += time.time() - start

        # merge paths
        def findTwoPaths(paths):
            startCoordToPathIndex = {}
            for i1, p1 in enumerate(paths):
                # if p1[0] in startCoordToPathIndex:
                #     ipdb.set_trace()
                p1EndCoord = p1[-1]
                if p1EndCoord in startCoordToPathIndex:
                    return i1, startCoordToPathIndex[p1EndCoord]
                startCoordToPathIndex[p1[0]] = i1
            return None
        originalNumPaths = len(paths)
        while res := findTwoPaths(paths):
            i1, i2 = res
            paths[i1] = paths[i1] + paths[i2][1:]
            del paths[i2]
        print(f"{originalNumPaths=} {len(paths)=}")

        start = time.time()


        # draw paths
        for i, path in enumerate(paths):
            vsk.stroke(i+1)
            # vsk.polygon(path)
            vsk.stroke(i+2)
            self.drawSmoothedPath(vsk, path)
            # corner = 0.5

        timerC += time.time() - start

    def drawSmoothedPath(self,vsk, path):
        windowWidth = 5
        smoothedPath = []
        # assert len(path) > windowWidth
        # if len(path) < window
        # ipdb.set_trace()
        # originalNumPoints = len(path)
        
        path = np.array([path[0]] * (windowWidth-1) + path + [path[-1]] * (windowWidth-1))
        slidingWindow = np.lib.stride_tricks.sliding_window_view(path, windowWidth, axis=0)
        for window in slidingWindow:
            p = window.mean(axis=1) * self.scale
            smoothedPath.append(p)
        
        vsk.polygon(smoothedPath)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("mm")

        tt = TerrainTiles(
            # bounds=[5.567466,  44.920668, 6.059677,45.321544],
            # bounds=[3.474233, 43.409836, 8.729127, 46.578498],
            bounds = [-12.036425, 49.627792 ,2.918008, 60.814924],
            zoom=8,
        )

        maxDim = 2000
        self.scale = 270/maxDim
        heights = tt.getCombinedTileDatasets(maxDimension=maxDim)

        contourLines = calcContourLines(heights)
        
        for contourLine in contourLines[:]:
            self.drawContourLine(vsk, contourLine[:, :])
        
        print(f"{timerA=}")
        print(f"{timerB=}")
        print(f"{timerC=}")

        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    ContoursSketch.display()
