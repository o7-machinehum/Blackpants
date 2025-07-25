import pcbnew, math

# Get board and compute its centroid (approximate center)
board = pcbnew.GetBoard()

# Filter alleen Edge.Cuts-segmenten, en sla alles zonder GetShape over (tekst e.d.)
cuts = [
    d for d in board.GetDrawings()
    if hasattr(d, "GetShape")
       and d.GetShape() == pcbnew.SHAPE_T_SEGMENT
       and d.GetLayer() == pcbnew.Edge_Cuts
]

# Collect all segment endpoints to compute average
pts = []
for d in cuts:
    pts.append(d.GetStart())
    pts.append(d.GetEnd())

# Compute centroid
centroid_x = sum(p.x for p in pts) / len(pts)
centroid_y = sum(p.y for p in pts) / len(pts)

# Parameters
offset  = pcbnew.FromMM(0.5)
spacing = pcbnew.FromMM(2.0)
drill   = pcbnew.FromMM(0.2)
pad     = pcbnew.FromMM(0.6)
netcode = board.GetNetcodeFromNetname("GND")

def stitch_segment(p1, p2):
    # Vector along segment
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    length = math.hypot(dx, dy)
    ux, uy = dx/length, dy/length

    # Two normals
    n1 = (-uy, ux)
    n2 = (uy, -ux)

    # Midpoint
    mx = (p1.x + p2.x) / 2
    my = (p1.y + p2.y) / 2

    # Kies de normale kant naar binnen
    test1 = ((mx + n1[0]*offset) - centroid_x)**2 + ((my + n1[1]*offset) - centroid_y)**2
    test2 = ((mx + n2[0]*offset) - centroid_x)**2 + ((my + n2[1]*offset) - centroid_y)**2
    nx, ny = n1 if test1 < test2 else n2

    # Startpunt
    start_x = p1.x + int(nx * offset)
    start_y = p1.y + int(ny * offset)

    # Aantal vias
    steps = int((length - 2*offset) / spacing)
    for i in range(steps + 1):
        x = int(start_x + ux * spacing * i)
        y = int(start_y + uy * spacing * i)
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I(x, y))
        via.SetDrill(drill)
        via.SetWidth(pad)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNetCode(netcode)
        board.Add(via)

# Place stitching vias on all Edge.Cuts segments
for d in cuts:
    stitch_segment(d.GetStart(), d.GetEnd())

pcbnew.Refresh()
