import vsketch
from scipy.spatial.transform import Rotation as R
from shapely import Polygon

import numpy as np
from tqdm import tqdm

from vsketch.fill import generate_fill


class IsometricColumnsSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a1", landscape=True)
        vsk.scale("mm")

        NUM_X_POINTS = 28
        NUM_Y_POINTS = 28


        noiseScale = 0.1
        noise = vsk.noise(
            np.arange(0, NUM_X_POINTS+1)*noiseScale,
            np.arange(0, NUM_Y_POINTS+1)*noiseScale
            )

        heightMap = np.sin(noise*8)*1.2 
        heightMap += abs(np.min(heightMap))
        minHeight = np.min(heightMap)
        maxHeight = np.max(heightMap)
        heightMap += 1

        heightMap[8:10,:] = 0
        heightMap[18:20,:] = 0

        heightMap[:, 8:10] = 0
        heightMap[:, 18:20] = 0
        
        coordToPolygons = {}

        
        # coords = np.zeros((NUM_X_POINTS,NUM_Y_POINTS,3), dtype=np.float32)

        zAxisRotation = R.from_euler("Z", np.pi/4 , degrees=False) 
        xAxisRotation = R.from_euler("X", np.pi/4 , degrees=False) 
        
        for x in range(NUM_X_POINTS):
            for y in range(NUM_Y_POINTS):
                polygons = []
                z = heightMap[x,y]
                if z > 0:
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
            vsk.scale(15)
            for (x,y),polygons in tqdm(coordToPolygons.items()):
                unionOfPolygons = Polygon()

                for polygonIndex, polygon in enumerate(polygons):
                    # if polygonIndex != 1:
                    #     continue

                    shapelyPolygon = Polygon(polygon)
                    occludedPolygon = shapelyPolygon.difference(occlusionMask)
                    unionOfPolygons = unionOfPolygons.union(shapelyPolygon)
                    if polygonIndex == 1:

                        filled = generate_fill(occludedPolygon, 0.05,0)
                        vsk.stroke(2)
                        vsk.geometry(filled.as_mls())

                    elif polygonIndex == 2:
                        minWidth = 0.03
                        maxWidth = 0.12

                        widthRange = maxWidth - minWidth
                        
                        height = heightMap[x,y]
                        penWidth = minWidth + widthRange*( (height - minHeight) / (maxHeight - minHeight) )
                        vsk.stroke(3)
                        # vsk.penWidth(penWidth)
                        vsk.geometry(generate_fill(occludedPolygon,penWidth,0).as_mls())
                    # else:
                    vsk.stroke(1)
                    vsk.geometry((occludedPolygon))
                occlusionMask = occlusionMask.union(unionOfPolygons)
        

        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    IsometricColumnsSketch.display()
