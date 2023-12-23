import vsketch
import numpy as np


def signPow(x, pow):
    return np.power(abs(x), pow) * np.sign(x)

class BulbsSketch(vsketch.SketchClass):
    # Sketch parameters:
    numLines = vsketch.Param(40)
    WIDTH = 270

    displacementMult = vsketch.Param(40)
    pow = vsketch.Param(1.0)
    pow2 = vsketch.Param(1.0)

    numPeriods = vsketch.Param(1.0)

    shift = vsketch.Param(0.5)


    def getPoint(self, i,j, flip):
        ratioX = i / (self.numLines - 1)

        sinX = np.sin(ratioX * self.numPeriods* 2*np.pi)

        def amplitude(ratioX, ratioY):

            # a = signPow( sinX, 1.0)
            b = signPow( np.sin(sinX ), self.pow2)

            c = min(np.mod(ratioY,0.5), 1.0-np.mod(ratioY,0.5))

            return self.displacementMult * b

        
        ratioY = j / (self.numLines - 1)
        # sinY = np.sin(ratioY * self.numPeriods* 2*np.pi)

        sign = -1 if flip else 1

        # a = signPow(np.sin( (ratioY ) * self.numPeriods *2*np.pi  ),1.5)
        # b = signPow(np.sin( (ratioY ) * self.numPeriods *2*np.pi  ),0.8)


        return  ratioX*self.WIDTH + sign* amplitude(ratioX, ratioY) * np.sin( (ratioY ) * self.numPeriods *2*np.pi  ), ratioY*self.WIDTH 


    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        # vsk.penWidth("1mm")
        vsk.scale("mm")
        vsk.strokeWeight(5)

        self.LINE_SPACING = self.WIDTH/self.numLines


        # for i in range(self.numLines):
        #     vsk.line(0, i*LINE_SPACING, WIDTH, i*LINE_SPACING)
        #     vsk.line(i*LINE_SPACING, 0, i*LINE_SPACING, WIDTH)



        for i in range(self.numLines):
            x,y = None, None
            for j in range(self.numLines):
                newX,newY = self.getPoint(i,j, flip=True)
                if x is not None:
                    vsk.line(x,y, newX, newY)
                x,y = newX, newY

        for i in range(self.numLines):
            x,y = None, None
            for j in range(self.numLines):
                newY,newX = self.getPoint(i,j, flip=False)
                if x is not None:
                    vsk.line(x,y, newX, newY)
                x,y = newX, newY


        # implement your sketch here
        # vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    BulbsSketch.display()
