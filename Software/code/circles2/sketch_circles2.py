import vsketch
import numpy as np
from shapely import LineString
from scipy.spatial.transform import Rotation as R

class Circles2Sketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)
    numPoints = vsketch.Param(50)
    numLines = vsketch.Param(50)
    rotationX = vsketch.Param(2.0)
    rotationY = vsketch.Param(2.0)
    zThreshold = vsketch.Param(0.01)

    shift = vsketch.Param(0.2)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.scale("cm")
        vsk.size("445mmx340mm")
        
        def genCircle():
            circleEdges = 200
            theta = np.linspace(0,2*np.pi, circleEdges, endpoint=True)
            c = np.tile(theta, (3,1)).T
            c[:,0] = np.cos(c[:,0])
            c[:,1] = np.sin(c[:,1])
            c[:,2] = 0
            return c

        polygons = []
        
        def genTorus(circleRadius = 4, centerOffset = 10, power=1.0):
            numCirclesOnRings = 40
            torusCircles = []
            # for cIndex, theta in enumerate(np.linspace(0,2*np.pi, numCirclesOnRings, endpoint=False)):
            #     c = genCircle()
            #     c *= circleRadius
            #     c = c - np.array((centerOffset,0,0))
            #     r = R.from_euler("Y", theta, degrees=False)
            #     c = r.apply(c)
            #     torusCircles.append(c)
            # rings along torus
            for cIndex, theta in enumerate(np.linspace(0,2*np.pi, 41, endpoint=False)):
                c = genCircle()
                c = R.from_euler("X", np.pi/2, degrees=False).apply(c)
                radius = centerOffset - np.sign(np.cos(theta)) *np.abs(np.cos(theta))**power *circleRadius
                c *= radius
                yOffset = np.sin(theta)*circleRadius
                c -= np.array([0,yOffset,0])

                torusCircles.append(c)
            return torusCircles
        

        # metaTorusOffset = 4
        # torus1Circles = genTorus(circleRadius = 1, centerOffset=metaTorusOffset)
        # for c in torus1Circles:
        #     polygons.append(c)

        NUM_TORUSES = 4
        
        for torusIndex, theta in enumerate(np.linspace(0,0.2*np.pi, NUM_TORUSES, endpoint=False)):
            torusCircles = genTorus(circleRadius = 0.6, centerOffset=2.5, power=np.linspace(0.3,1.0,NUM_TORUSES)[torusIndex])
            translateX = torusIndex*2.0
            translateY = 0
            for c in torusCircles:
                c = R.from_euler("X", np.pi/2, degrees=False).apply(c)
                c = R.from_euler("Y",  np.pi/2 - theta, degrees=False).apply(c)
                c -= np.array((translateX, 0, translateY))
                polygons.append(c)

        # polygons.append(np.array([[0,0,0], [20,0,0]]))
        # polygons.append(np.array([[0,0,0], [0,20,0]]))
        # polygons.append(np.array([[0,0,0], [0,20,20]]))

        cameraZ = 20
        planeZ = 4

        maxX = max([np.max(polygon[:,0]) for polygon in polygons])
        maxY = max([np.max(polygon[:,1]) for polygon in polygons])
        maxZ = max([np.max(polygon[:,2]) for polygon in polygons])
        minX = min([np.min(polygon[:,0]) for polygon in polygons])
        minY = min([np.min(polygon[:,1]) for polygon in polygons])
        minZ = min([np.min(polygon[:,2]) for polygon in polygons])
        maxs = np.array((maxX, maxY, maxZ))
        mins = np.array((minX, minY, minZ))

        centeringTranslation = mins + (maxs-mins)/2
        centeringScaling = 1/np.min(maxs-mins)

        # finalXRotation = R.from_euler("X", self.rotationX, degrees=False) 
        # finalYRotation = R.from_euler("Y", self.rotationY, degrees=False) 
        
        # vsk.fill(1)
        for cTilted in polygons:
            # meanZ = cTilted[:,2].mean()
            # zNormalized = ( (maxZ- meanZ) / (maxZ-minZ))
            # vsk.penWidth(f"{zNormalized:.2f}mm")

            cTilted -= centeringTranslation
            cTilted *= centeringScaling

            # cTilted = finalXRotation.apply(cTilted)
            # cTilted = finalYRotation.apply(cTilted)

            # shrink each point depending on how far it is on the z axis
            shrinkage =    (cameraZ - planeZ)  / ( cameraZ - cTilted[:,2])
            cTilted = cTilted * shrinkage[:, np.newaxis]

            # cTilted = cTilted[cTilted[:,2] > 0 ]

            segmentsTrue = []
            segmentsFalse = []
            cTilted[:,2] += self.zThreshold
            points = cTilted[:,:]*40
            cond = cTilted[:,2] > -100

            def appendSegment(segment, segmentCond):
                if segmentCond:
                    segmentsTrue.append(segment)
                else:
                    segmentsFalse.append(segment)

            segmentCond = None
            segment = []
            pointIndex = 0
            while pointIndex < len(points):
                point = points[pointIndex]
                if segmentCond is not None and segmentCond != cond[pointIndex]:
                    lastPoint = segment[-1]
                    joiningPointDistance = point[2] / (point[2] - lastPoint[2])
                    joiningPoint = lastPoint * joiningPointDistance + point*(1-joiningPointDistance)
                    segment.append(joiningPoint)
                    appendSegment(segment, segmentCond)
                    segment = [joiningPoint]
                segmentCond = cond[pointIndex]
                segment.append(point)
                pointIndex  += 1
            appendSegment(segment, segmentCond)

            vsk.stroke(2)
            for segment in segmentsTrue:
                segment2d = [point[:2] for point in segment]
                vsk.polygon(segment2d, close=False)

            vsk.stroke(3)
            for segment in segmentsFalse:
                segment2d = [point[:2] for point in segment]
                # vsk.polygon(segment2d, close=False)



        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    Circles2Sketch.display()
