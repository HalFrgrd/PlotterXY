Install vpype:
https://github.com/abey79/vpype

Install vpype-gcode
https://github.com/plottertools/vpype-gcode/

Understand how to use the supplied toml file here; https://vpype.readthedocs.io/en/latest/cookbook.html?highlight=vpype.toml#creating-a-custom-configuration-file – hint; you need to rename "vpype.toml" to ".vpype.toml" and put it in your user folder.

You should then be able to run: "vpype read input.svg gwrite output.gcode" to create a gcode file.

`vpype ... linemerge --tolerance 0.1 linesimplify --tolerance 0.1 reloop --tolerance 0.1 linesort --two-opt ...`


vpype --config vpype.toml text --font timesr --size 30 --wrap 100 --position 250 250 "pen plotter here and also over here" linemerge --tolerance 0.1 linesimplify --tolerance 0.1 reloop --tolerance 0.1 linesort --two-opt gwrite output.gcode

