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

    shift = vsketch.Param(0.2)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("cm")
        
        def genCircle():
            circleEdges = 40
            theta = np.linspace(0,2*np.pi, circleEdges, endpoint=False)
            c = np.tile(theta, (3,1)).T
            c[:,0] = np.cos(c[:,0])
            c[:,1] = np.sin(c[:,1])
            c[:,2] = 0
            return c

        circles = []
        circleRadius = 4
        numCirclesOnRings = 80
        centerOffset = 10
        for cIndex, theta in enumerate(np.linspace(0,2*np.pi, numCirclesOnRings, endpoint=False)):
            c = genCircle()
            c *= circleRadius
            c = c - np.array((centerOffset,0,0))
            r = R.from_rotvec((0,theta,0), degrees=False)
            c = r.apply(c)
            circles.append(c)
        # rings along torus1
        for cIndex, theta in enumerate(np.linspace(0,2*np.pi, 20, endpoint=False)):
            c = genCircle()
            c = R.from_rotvec((np.pi/2,0,0), degrees=False).apply(c)
            radius = centerOffset - np.cos(theta)*circleRadius
            c *= radius
            yOffset = np.sin(theta)*circleRadius
            c -= np.array([0,yOffset,0])

            circles.append(c)

        
        for cIndex, theta in enumerate(np.linspace(0,2*np.pi, numCirclesOnRings, endpoint=False)):
            c = genCircle()
            c *= circleRadius
            c = R.from_rotvec((np.pi/2,0,0), degrees=False).apply(c)
            c = c - np.array((centerOffset,0,0))
            c = R.from_rotvec((0,0,theta), degrees=False).apply(c)
            c = c + np.array((centerOffset,0,0))
            circles.append(c)
        # rings along torus 2
        for cIndex, theta in enumerate(np.linspace(0,2*np.pi, 20, endpoint=False)):
            c = genCircle()
            radius = centerOffset - np.cos(theta)*circleRadius
            c *= radius
            c += np.array((centerOffset,0,0))
            zOffset = np.sin(theta)*circleRadius
            c -= np.array([0,0,zOffset])

            circles.append(c)

        cameraZ = 60
        planeZ = 50

        for cTilted in circles:
            rotation = R.from_rotvec((self.rotationX,self.rotationY,0), degrees=False)
            cTilted = rotation.apply(cTilted)
            # cTilted = yAxisR.apply(cTilted)
            # cTilted = zAxisR.apply(cTilted)

            # shrink each point depending on how far it is on the z axis
            shrinkage =  (planeZ - cameraZ) / ( cTilted[:,2] - cameraZ) 
            # print(shrinkage.shape)
            # print(cTilted.shape)
            cTilted = cTilted * shrinkage[:, np.newaxis]


            vsk.polygon(cTilted[:,:2], close=True)



        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    Circles2Sketch.display()
