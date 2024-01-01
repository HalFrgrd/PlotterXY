import vsketch
import numpy as np

from scipy.spatial.transform import Rotation as R
from shapely import Point, LineString, Polygon, MultiPolygon, box


class EdgeDeformationSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("mm")

        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")
        polygons = []

        def genCircle():
            circleEdges = 100
            theta = np.linspace(0,2*np.pi, circleEdges, endpoint=True)
            c = np.tile(theta, (3,1)).T
            c[:,0] = np.cos(c[:,0])
            c[:,1] = np.sin(c[:,1])
            c[:,2] = 0
            return c
        
        def genSphere():
            arcs = []
            def genArc():
                theta2 = np.linspace(-np.pi/2,np.pi/2, 40, endpoint=True)
                c = np.tile(theta2, (3,1)).T
                c[:,0] = np.cos(c[:,0])
                c[:,1] = np.sin(c[:,1])
                c[:,2] = 0
                return c
            for arcIndex, theta1 in enumerate(np.linspace(0,np.pi, 21, endpoint=True)):
                c = genArc()
                c = R.from_euler("Y", theta1, degrees=False).apply(c)
                if arcIndex % 2:
                    c = c[::-1, :]
                arcs.append(c)
            arcs.append(np.array([(np.nan,np.nan,np.nan)]))
            for arcIndex, theta1 in enumerate(np.linspace(0,np.pi, 21, endpoint=True)):
                c = genArc()
                c = R.from_euler("Z", np.pi/2, degrees=False).apply(c)
                c = R.from_euler("X", theta1, degrees=False).apply(c)
                if arcIndex % 2:
                    c = c[::-1, :]
                arcs.append(c)

            return np.vstack(arcs)
        
        s = genSphere()*0.7
        s -= np.array((.3,.3,0))
        print(s.shape)
        polygons.append(s)
                        

        # for i in range(5):
        #     c= genCircle()
        #     c *= vsk.random(0.3, 2)
        #     c += np.array((vsk.random(-1,1),vsk.random(-1,1),0))

        #     polygons.append(c)

        c = genCircle()
        c *= 0.7
        c += np.array((0.3,0.3,0))
        polygons.append(c)


        thresh = 0.8
        maxVal = 1.0

        def getDeformedPoint(a):
            absA = abs(a)
            f_absA = (1+1/-(absA-1.1055+1))*0.2 + 0.8

            cutoff = 0.5585

            if absA <= cutoff:
                deformedA = a
            else:
                deformedA =f_absA * np.sign(a)
            return deformedA

        with vsk.pushMatrix():
            vsk.scale(100)
            # vsk.rect(-maxVal,-maxVal,maxVal,maxVal, mode="corners")
            # vsk.rect(-thresh,-thresh,thresh,thresh, mode="corners")

            globalGeomMask = Polygon()
            for polygon in polygons:
                # geomMask
                print(np.ma.masked_invalid(polygon))
                subPolygons = [polygon[s] for s in np.ma.clump_unmasked(np.ma.masked_invalid(polygon))]
                print(subPolygons)
                # splitIndices = np.isnan(polygon).any(axis=1)
                # if splitIndices.sum():
                #     splitIndices = np.nonzero(splitIndices)
                #     splitIndices = [splitIndex[0] for splitIndex in splitIndices]
                #     subPolygons = np.vsplit(polygon, splitIndices)
                for p in subPolygons:
                    print(p.shape)
                # else:
                #     subPolygons = [polygon]

                for subPolygon in subPolygons:
                    points = []
                    for point in subPolygon:

                        x = getDeformedPoint(point[0])
                        y = getDeformedPoint(point[1])
                        points.append((x,y))
                    
                    vsk.polygon(points)


    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    EdgeDeformationSketch.display()
