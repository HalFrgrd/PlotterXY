import vsketch


class FillTestSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("mm")

        # implement your sketch here
        # vsk.fill(1)
        # vsk.circle(0, 0, 50, mode="radius")
        # with vsk.pushMatrix():
        #     # vsk.translate(50,10)
        #     vsk.rotate(90, degrees=True)
        #     vsk.translate(-50,-10)
        #     vsk.rect(0, 0, 100, 20)
        # vsk.fill(2)
        vsk.arc(0,0,50,50,0,180,degrees=True, close="chord")
        # vsk.noFill()
        vsk.arc(0,0,40,30,90,270,degrees=True, close="chord")
        
        vsk.vpype("occult")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("occult linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    FillTestSketch.display()
