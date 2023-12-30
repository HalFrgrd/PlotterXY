import vsketch

from shapely import Point, LineString, Polygon, MultiPolygon, box, LinearRing
import ipdb


class FillTestSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("cm")


        # smallBox = box(0,0,1,1)
        # largerBox = box(-0.5, 0, 1.5, 1)
        # toDraw = smallBox.intersection(largerBox.boundary)
        # vsk.geometry(toDraw)
        # vsk.geometry(largerBox)

        s = LineString([(-1,-1, 0), (0, -1, 1), (0, 1, 1), (1, 1, 1), (1,0, 0), (-1,0, 0)])
        buffered = s.buffer(0.3)

        boundary = None
        
        pointsExtended = [s.coords[0]]*2 + list(s.coords) + [s.coords[-1]]*2
        segments = zip(pointsExtended,pointsExtended[1:],pointsExtended[2:],pointsExtended[3:])

        for p1, p2, p3, p4 in segments:
            # square = box(coord.x-0.5,coord.y-0.5,coord.x+0.5,coord.y+0.5)
            # square.
            l1 = LineString((p1,p2)).buffer(0.3, cap_style = "round")
            l2 = LineString((p2,p3)).buffer(0.3, cap_style = "round")
            l3 = LineString((p3,p4)).buffer(0.3, cap_style = "round")

            segBoundary = l1.union(l2).union(l3).boundary

            l = l2.boundary.intersection(segBoundary)
            # vsk.geometry(l)

            if boundary is None:
                boundary = l
            else:
                boundary = boundary.union(l)

        vsk.geometry(boundary.intersection(buffered))
        # vsk.geometry(boundary)

        # implement your sketch here
        # vsk.fill(19)
        # vsk.circle(0, 0, 50, mode="radius")
        # # with vsk.pushMatrix():
        # #     # vsk.translate(50,10)
        # #     vsk.rotate(90, degrees=True)
        # #     vsk.translate(-50,-10)
        # #     vsk.rect(0, 0, 100, 20)
        # # vsk.fill(2)
        # vsk.arc(0,0,50,50,0,180,degrees=True, close="chord")
        # # vsk.noFill()
        # vsk.arc(0,0,40,3000,90,270,degrees=True, close="chord")
        
        # vsk.vpype("occult")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("occult linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    FillTestSketch.display()
