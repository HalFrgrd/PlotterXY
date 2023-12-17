
import svgwrite
import numpy as np
from beartype import beartype

################## CONFIG

# X is across, Y is down
SHEET_HEIGHT=297 #mm
SHEET_WIDTH=420 #mm
# SHEET_WIDTH, SHEET_HEIGHT = SHEET_HEIGHT, SHEET_WIDTH

STROKE_WIDTH = min(SHEET_WIDTH, SHEET_HEIGHT)*0.0005
NUM_AUTOMATA=4
NUM_AUTOMATON_CELLS=50
SPACING_BETWEEN_AUTOMATA = int(max(SHEET_HEIGHT, SHEET_WIDTH)*0.01)

SVG_SIDE_PADDING = 0.1 * SHEET_WIDTH
SVG_MIN_AUTOMATON_X, SVG_MAX_AUTOMATON_X = SVG_SIDE_PADDING, SHEET_WIDTH - SVG_SIDE_PADDING
SVG_MIN_AUTOMATON_Y, SVG_MAX_AUTOMATON_Y = SVG_SIDE_PADDING, SHEET_HEIGHT - SVG_SIDE_PADDING

SINGLE_AUTOMATA_WIDTH = (SVG_MAX_AUTOMATON_X - SVG_MIN_AUTOMATON_X - SPACING_BETWEEN_AUTOMATA*(NUM_AUTOMATA-1)) / NUM_AUTOMATA
SINGLE_AUTOMATA_HEIGHT = SVG_MAX_AUTOMATON_Y - SVG_MIN_AUTOMATON_Y
NUM_AUTOMATA_ITERATIONS=int(SINGLE_AUTOMATA_HEIGHT/SINGLE_AUTOMATA_WIDTH*NUM_AUTOMATON_CELLS)

SVG_AUTOMATA_CELL_WIDTH=SINGLE_AUTOMATA_WIDTH*0.3/NUM_AUTOMATON_CELLS

################## Automata logic

@beartype
def next_from_rule(rule: np.int8, row):
    padded_row = np.hstack([row[:1], row, row[-1:]])
    slide = np.lib.stride_tricks.sliding_window_view(padded_row, 3)
    nextRow = ((1 << (np.packbits(slide, axis=-1) >> 5)) & rule) != 0
    return nextRow.reshape((-1,))

@beartype
def generate_grid(rule, height: int, width: int) -> np.ndarray:
    row = np.random.binomial(1, 0.3, size=(width, )).astype(bool)
    # row = np.zeros(width).astype(bool)
    # row[width//2] = True
    grid = np.zeros((height, width), dtype=bool)

    for r in range(height):
        grid[r] = row
        row = next_from_rule(rule, row)
    return grid


################## Drawing

dwg = svgwrite.Drawing(profile="full", size=(f"{SHEET_WIDTH}mm",f"{SHEET_HEIGHT}mm"))
dwg.viewbox(0,0,SHEET_WIDTH, SHEET_HEIGHT)
np.random.seed(0)

# text = svgwrite.text.Text(f"One Dimensional Cellular Automata", insert =("50%","10%"), fill="black")
# text['font-size'] = '100%'
# text['font-family'] = 'Courier New'
# text['text-anchor'] = 'middle'
# dwg.add(text)


@beartype
def draw_dot(x,y,radius, fill):
    return dwg.circle(center=(x,y), r=radius, fill=fill, stroke="black", stroke_width=STROKE_WIDTH)


for automaton in range(NUM_AUTOMATA):
    automaton_rule = np.int8([30, 122, 126, 150][automaton])
    svg_automaton_start_x = SVG_MIN_AUTOMATON_X + automaton * (SPACING_BETWEEN_AUTOMATA + SINGLE_AUTOMATA_WIDTH)
    # automaton_svg = dwg.svg(insert=(svg_automaton_start_x, SVG_MIN_AUTOMATON_Y), size=(SINGLE_AUTOMATA_WIDTH, SINGLE_AUTOMATA_HEIGHT))


    SVG_HEADER_HEIGHT = SINGLE_AUTOMATA_HEIGHT * 0.01
    assert SVG_HEADER_HEIGHT < SINGLE_AUTOMATA_HEIGHT * 0.5

    # text = svgwrite.text.Text(f"{automaton_rule:08b}", insert = ("50%", "6%"), fill = 'black')
    # text['font-size'] = '50%'
    # text['font-family'] = 'Courier New'
    # text['text-anchor'] = 'middle'
    # automaton_svg.add(text)

    assert NUM_AUTOMATA_ITERATIONS > 0
    grid = generate_grid(automaton_rule, NUM_AUTOMATA_ITERATIONS, NUM_AUTOMATON_CELLS)

    def grid_cell_to_svg_pos(x,y):
        SIDE_PADDING = 0.04*SINGLE_AUTOMATA_WIDTH
        DRAWABLE_WIDTH = SINGLE_AUTOMATA_WIDTH - 2 * SIDE_PADDING
        relative_grid_x = x / NUM_AUTOMATON_CELLS
        relative_grid_y = y/NUM_AUTOMATA_ITERATIONS

        svg_x = SIDE_PADDING + DRAWABLE_WIDTH*relative_grid_x
        svg_y = SVG_HEADER_HEIGHT + (SINGLE_AUTOMATA_HEIGHT-SVG_HEADER_HEIGHT)*relative_grid_y
        return svg_x, svg_y
    
    def connection_line_between_parent_and_child(parent_idx, child_idx, parent_iteration):
        parent_svg_pos = grid_cell_to_svg_pos(parent_idx, parent_iteration)
        correction = (parent_idx-child_idx)*SVG_AUTOMATA_CELL_WIDTH / np.sqrt(2)
        poss_y_correction = (parent_idx == child_idx)*SVG_AUTOMATA_CELL_WIDTH
        line_start_x = parent_svg_pos[0] - correction
        line_start_y = parent_svg_pos[1] + abs(correction) + poss_y_correction
        line_end_x = x + correction
        line_end_y = y - abs(correction) - poss_y_correction
        connection_line = dwg.line(
            (svg_automaton_start_x+line_start_x, SVG_MIN_AUTOMATON_Y+line_start_y), 
            (svg_automaton_start_x+line_end_x, SVG_MIN_AUTOMATON_Y+line_end_y),
            stroke='black',
            stroke_width=STROKE_WIDTH,
            )
        return connection_line
    
    for iteration in range(0, NUM_AUTOMATA_ITERATIONS):
        row = grid[iteration]
        for i in range(NUM_AUTOMATON_CELLS):
            if not row[i]:
                continue
            x,y = grid_cell_to_svg_pos(i, iteration)
            dwg.add(draw_dot(x=svg_automaton_start_x+x,y=SVG_MIN_AUTOMATON_Y+y,radius=SVG_AUTOMATA_CELL_WIDTH, fill="none"))
            if iteration == 0:
                continue
            for parent_idx in range(i-1, i+2):
                if parent_idx < 0 or parent_idx >= NUM_AUTOMATON_CELLS:
                    continue
                parent_iteration = iteration -1
                if grid[parent_iteration][parent_idx]:
                    connection_line = connection_line_between_parent_and_child(parent_idx, i, parent_iteration)
                    dwg.add(connection_line)

    # dwg.add(automaton_svg)

dwg.saveas("cellular_automata.svg", pretty=True)
        

