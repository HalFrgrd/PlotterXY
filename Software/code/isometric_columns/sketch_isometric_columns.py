import vsketch
from scipy.spatial.transform import Rotation as R
from shapely import Polygon, force_2d

import numpy as np

class IsometricColumnsSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=True)
        vsk.scale("mm")

        NUM_X_POINTS = 30
        NUM_Y_POINTS = 30

        xCoords, yCoords = np.indices((NUM_X_POINTS, NUM_Y_POINTS), dtype=np.float32)
        xCoords -= NUM_X_POINTS*0.5 
        yCoords -= NUM_Y_POINTS*0.5
        # print(xCoords, yCoords)
        heightMap = np.sin((xCoords**2 + yCoords**2) * 0.04 )*0.5
        heightMap += abs(np.min(heightMap)) + 1

        coordToPolygons = {}

        
        # coords = np.zeros((NUM_X_POINTS,NUM_Y_POINTS,3), dtype=np.float32)

        zAxisRotation = R.from_euler("Z", np.pi/4 , degrees=False) 
        xAxisRotation = R.from_euler("X", np.pi/4 , degrees=False) 
        
        for x in range(NUM_X_POINTS):
            for y in range(NUM_Y_POINTS):

                polygons = []

                z = heightMap[x,y]

                polygons.append( [
                    (x,y,0),
                    (x+1,y,0),
                    (x+1,y,z),
                    (x,y,z),
                    (x,y,0)
                ])
                polygons.append( [
                    (x+1,y,0),
                    (x+1,y-1,0),
                    (x+1,y-1,z),
                    (x+1,y,z),
                    (x+1,y,0),
                ] )
                polygons.append( [
                    (x,y,z),
                    (x+1,y,z),
                    (x+1,y-1,z),
                    (x,y-1,z),
                    (x,y,z),
                ])

                rotatedPolygons = []
                for polygon in polygons:
                    rotatedPolygon = zAxisRotation.apply(polygon)
                    rotatedPolygon = xAxisRotation.apply(rotatedPolygon)
                    rotatedPolygons.append(rotatedPolygon[:, :2])

                coordToPolygons[(x,y)] = rotatedPolygons

        # reorder the list so we render front to back
        coordToPolygons = dict(sorted(coordToPolygons.items(), key = lambda keyValue : -sum(keyValue[0])))

        occlusionMask = Polygon()

        with vsk.pushMatrix():
            vsk.scale(5)
            for (x,y),polygons in coordToPolygons.items():

                for polygon in polygons:
                    shapelyPolygon = Polygon(polygon)
                    occludedPolygon = shapelyPolygon.difference(occlusionMask)

                    vsk.geometry((occludedPolygon))
                    occlusionMask = occlusionMask.union(shapelyPolygon)
        

        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    IsometricColumnsSketch.display()
