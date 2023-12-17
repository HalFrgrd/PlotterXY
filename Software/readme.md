
## vpype


Install vpype:
https://github.com/abey79/vpype

Install vpype-gcode
https://github.com/plottertools/vpype-gcode/

Use `vpype.toml`

Sample command (and good for calibrating position / scale):
`vpype --config vpype.toml rect 0cm 0cm 30cm 10cm linemerge --tolerance 0.1 linesimplify --tolerance 0.1 reloop --tolerance 0.1 linesort --two-opt layout --landscape a3 gwrite output.gcode`


- reloop: randomize seam location

## Useful projects
- https://anvaka.github.io/peak-map/#7.68/47.727/-122.574
- https://github.com/abey79/lines