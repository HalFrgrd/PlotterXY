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

    def drawContourLine(self, vsk, contourHeight, heightMask):
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


        """
        if you are in the middle of setting facing dir, back left will be True, back right will be False
        """

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
            # vsk.stroke(i+1)
            # vsk.polygon(path)
            # vsk.stroke(i+2)
            self.drawSmoothedPath(vsk, path)

        timerC += time.time() - start

    def drawSmoothedPath(self,vsk, path):
        windowWidth = 5
        path = np.array([path[0]] * (windowWidth-1) + path + [path[-1]] * (windowWidth-1))
        slidingWindow = np.lib.stride_tricks.sliding_window_view(path, windowWidth, axis=0)
        # for window in slidingWindow:
        #     p = window.mean(axis=1) * self.scale
        #     smoothedPath.append(p)

        polygonPoints = slidingWindow.mean(axis=2)*self.scale
        
        vsk.polygon(polygonPoints)

    def drawFrame(self, vsk, heightMaskShape):
        height, width = heightMaskShape
        height -= 1
        width -= 1

        startX = 0
        endX =  width*self.scale

        startY = 0
        endY = height*self.scale

        vsk.rect(startX, startY, endX, endY)
        size = 1.3
        sizeOffset = 1.3
        
        numLongitudeMarkers = 10
        longitudes = np.linspace(self.west, self.east, numLongitudeMarkers)
        markerXPoses = np.linspace(startX, endX, numLongitudeMarkers)
        for markerXPos, long in zip(markerXPoses, longitudes):
            vsk.line(markerXPos, startY, markerXPos, startY-sizeOffset)
            vsk.text(f"{long:.6f}", markerXPos+sizeOffset*0.5, startY-sizeOffset*0.7, size=size)

        numLatitudeMarkers = 8
        latitudes = np.linspace(self.north, self.south, numLatitudeMarkers)
        markerYPoses = np.linspace(startY, endY, numLatitudeMarkers)
        for markerYPos, lat in zip(markerYPoses, latitudes):
            vsk.line(startX, markerYPos, startX-sizeOffset, markerYPos)
            with vsk.pushMatrix():
                vsk.translate(startX-7*sizeOffset, markerYPos)
                # vsk.rotate(90, degrees=True)
                vsk.text(f"{lat:.6f}", 0, 0, size=size, mode="transform")

        
        

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("mm")

        boundsUK = [-12.036425, 49.627792 ,2.918008, 60.814924]
        boundsAlps = [3.474233, 43.409836, 8.729127, 46.578498]
        boundsGrenoble = [5.666199,44.986170, 5.879059, 45.213004]
        boundsIceland = [-25.129087, 63.166260, -13.341700, 66.558755]

        tt = TerrainTiles(
            # bounds=[5.567466,  44.920668, 6.059677,45.321544],
            bounds = boundsIceland,
            zoom=9,
        )
        self.west, self.south, self.east, self.north = tt.bounds_ll

        maxDim = 3000
        self.scale = 360/maxDim
        heights = tt.getCombinedTileDatasets(maxDimension=maxDim)
        print(f"{heights.shape}")
        # ipdb.set_trace()


        contourAtHeight = calcContourLines(heights, contourDiff=75)
        
        for contourHeight, contourHeightMask in contourAtHeight.items():
            self.drawContourLine(vsk, contourHeight, contourHeightMask)
        
        # self.drawFrame(vsk, heights.shape)
        
        print(f"{timerA=}")
        print(f"{timerB=}")
        print(f"{timerC=}")

        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    ContoursSketch.display()
