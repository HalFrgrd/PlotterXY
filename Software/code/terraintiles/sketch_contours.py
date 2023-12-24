import vsketch
from terraintiles import TerrainTiles, calcContourLines
import rasterio

import ipdb

from scipy import ndimage

from matplotlib import pyplot as plt
import numpy as np
from copy import copy

class ContoursSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def drawContourLine(self, vsk, contourLine):

        # sobel_x = ndimage.sobel(contourLine, 0, mode="constant", cval=0)
        # sobel_y = ndimage.sobel(contourLine, 1, mode="constant", cval=0)
        # roughMag = sobel_x**2 + sobel_y**2

        # contourLine = np.array(
        #     [
        #         [False,False,False,True,True,False,False],
        #         [False,False,False,True,True,False,False],
        #         [False,False,False,True,True,False,False],
        #         [False,False,True,True,True,True,False],
        #         [False,True ,True,True,True,True,False],
        #         [False,False,False,True,True,True,False],
        #         [False,False,True,True,True,False,False],
        #         [False,False,False,False,False,False,False],
        #         [False,False,False,False,False,False,False],
        #         [False,False,False,False,False,False,False],
        #     ]
        # )

        width = contourLine.shape[1]
        height = contourLine.shape[0]

        # plt.subplot(221)
        # plt.imshow(contourLine)
        # plt.subplot(222)
        # plt.imshow(sobel_x)
        # plt.subplot(223)
        # plt.imshow(sobel_y)
        # plt.subplot(224)
        # plt.imshow(roughMag)
        # plt.show()


        #walk along the contour keeping them to the left

        settingToPaths = {
            (0,1): {
                ((False, True), (True, True)): (-1,0),
                ((False, True), (False, True)): (0,1),
                ((False, True), (False, False)): (1,0),
            },
            (0,-1): {
                ((True, True), (True, False)): (1,0),
                ((True, False), (True, False)): (0,-1),
                ((False, False), (True, False)): (-1,0),
            },
            (1,0): {
                ((True, True), (False, True)): (0,1),
                ((True, True), (False, False)): (1,0),
                ((True, False), (False, False)): (0,-1),
            },
            (-1,0): {
                ((True, False), (True, True)): (0,-1),
                ((False, False), (True, True)): (-1,0),
                ((False, False), (False, True)): (0, 1),
            },
        }

        # ipdb.set_trace()
        a,b=np.nonzero(contourLine)
        coordsAboveHeight = set(zip(b,a))

        coordsNearLine = set()

        # for x,y in coordsAboveHeight:
        #     for dx in [0,1]:
        #         for dy in [0,1]:
        #             a = x+dx
        #             b = y+dy
        #             if (0<=a<width) and (0<=b<height) and not contourLine[b,a]:
        #                 coordsNearLine.add((x,y))
        
        for x in range(width):
            for y in range(height):
                neighborhood = contourLine[y:y+2,x:x+2]
                if np.any(neighborhood) and not np.all(neighborhood):
                    coordsNearLine.add((x,y))

        # for i in range(height):
        #     for j in range(width):
        #         if contourLine[i,j]:
        #             vsk.circle(j,i, radius=0.5)
        #         if (j,i) in coordsNearLine:
        #             vsk.circle(j,i, radius=0.1)

        def getSetting(x,y):
            return ((contourLine[y,x],contourLine[y,x+1]), (contourLine[y+1,x],contourLine[y+1,x+1]))
        
        def getPointToPlotFromDir(x,y,dir):
            return x+.5, y+.5
            # if dir == (0,1):
            #     return x+.5,y+.5
            # if dir == (0,-1):
            #     return x+.5,y+.5
            # if dir == (1,0):
            #     return x+.5,y+.5
            # if dir == (-1,0):
            #     return x+.5,y+.5
            assert False
        # ipdb.set_trace()

        coordsVisited = set()
        paths = []
        while (remaining := coordsNearLine - coordsVisited):
            x,y = remaining.pop()
            # if x == 2 and y == 4:
            #     ipdb.set_trace()
            
            path = []
            coordsNearLine.remove((x,y))


            if not( 0<= x and x + 1 < width and 0 <= y and y+1 < height):
                continue
            
            setting = getSetting(x,y)

            for dir_, dirSettings in settingToPaths.items():
                if setting in dirSettings:
                    dir = dir_
                    break
            else:
                continue
            
            while True:
                if not( 0<= x and x + 1 < width and 0 <= y and y+1 < height):
                    break
                setting = getSetting(x,y)
                try:
                    dir = settingToPaths[dir][setting]
                except KeyError:
                    # ipdb.set_trace()
                    break
                
                coordsVisited.add((x,y))
            
                newX = x + dir[0]
                newY = y + dir[1]
                path.append(getPointToPlotFromDir(x,y, dir))

                x,y = newX, newY

                if (x,y) in coordsVisited:
                    path.append(getPointToPlotFromDir(x,y, dir))

                    break
            
            print(len(path))
            # if len(path) == 5:
            #     ipdb.set_trace()

            # for (x,y), (x2,y2) in path:
            #     vsk.line(x,y,x2,y2)
            paths.append(path)

        while True:
            found = False
            for i1, p1 in enumerate(paths):
                for i2, p2 in enumerate(paths):
                    endP1 = p1[-1]
                    startP2 = p2[0]
                    if i1 != i2 and endP1 == startP2:
                        found = True
                        break
                if found:
                    break
            if found:
                paths[i1] = p1 + p2[1:]
                del paths[i2]
            else:
                break

                

        for i, path in enumerate(paths):
            vsk.stroke(i+1)
            # for (a,b), (c,d) in path:
            #     vsk.line(a,b,c,d)
            # if (2,4) in [p1 for p1,p2 in path]:
            #     ipdb.set_trace()
            vsk.polygon([p1 for p1 in path])






        # for x in range(contourLine.shape[0]):
        #     for y in range(contourLine.shape[1]):
        #         if contourLine[x,y]:

        #             # if (x-1,y-1) in 

        #             if y+1 < contourLine.shape[1] and contourLine[x,y+1]:
        #                 vsk.line(x,y,x,y+1)
                    
        #             if x+1 < contourLine.shape[0] and contourLine[x+1,y]:
        #                 vsk.line(x,y,x+1,y)
                    
        #             if y+1 < contourLine.shape[1] and x+1 < contourLine.shape[0] and contourLine[x+1,y+1]:
        #                 vsk.line(x,y,x+1,y+1)
                    
        #             if y-1 > 0 and x+1 < contourLine.shape[0] and contourLine[x+1,y-1]:
        #                 vsk.line(x,y,x+1,y-1)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("mm")


        with rasterio.open('terraintile_cache/11/311/682.tif') as tileDataset:
            contourLines = calcContourLines(tileDataset.read(1))
        
        for contourLine in contourLines:
            self.drawContourLine(vsk, contourLine[:, :])

        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    ContoursSketch.display()
