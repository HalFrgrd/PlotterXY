import vsketch

import numpy as np

class CirclesSketch(vsketch.SketchClass):
    # Sketch parameters:
    radius = vsketch.Param(15.0)
    radiusMult = vsketch.Param(0.3)
    noiseMult1 = vsketch.Param(0.1)
    noiseMult2 = vsketch.Param(0.0)
    numCircles = vsketch.Param(250)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("cm")

        for circleIndex, theta in enumerate(np.linspace(0, 2*np.pi, self.numCircles, endpoint=False)):
            s = np.sin(theta)
            c = np.cos(theta)

            r = self.radius*self.radiusMult

            # xNoise = vsk.randomGaussian()*self.noiseMult
            xNoise = np.sin(circleIndex)*self.noiseMult1+vsk.randomGaussian()*self.noiseMult2
            # yNoise = vsk.randomGaussian()*self.noiseMult
            yNoise = np.sin(circleIndex)*self.noiseMult1+vsk.randomGaussian()*self.noiseMult2

            # vsk.stroke(circleIndex%2 + 1)
            vsk.circle(r*c+xNoise, r*s+yNoise, self.radius)
        
        vsk.vpype("reloop")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    CirclesSketch.display()
