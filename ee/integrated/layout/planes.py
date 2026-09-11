#!/usr/bin/env python3
"""Add the two ground reference planes to the six-layer placement."""
import argparse
from pathlib import Path
import pcbnew as pcb
from start import xy

pcb.SwigPyIterator.next=pcb.SwigPyIterator.__next__
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('board',type=Path)
args=ap.parse_args()
b=pcb.LoadBoard(str(args.board))
assert b.GetCopperLayerCount()==6
assert not any(not z.GetIsRuleArea() for z in b.Zones())
zones=[]
for layer in [pcb.In1_Cu,pcb.In4_Cu]:
    z=pcb.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('GND'))
    z.SetZoneName('GND reference '+b.GetLayerName(layer))
    z.SetLocalClearance(pcb.FromMM(.15));z.SetMinThickness(pcb.FromMM(.1))
    z.SetPadConnection(pcb.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(pcb.FromMM(.2));z.SetThermalReliefSpokeWidth(pcb.FromMM(.25))
    z.SetIslandRemovalMode(pcb.ISLAND_REMOVAL_MODE_ALWAYS)
    poly=z.Outline();poly.NewOutline()
    for x,y in [(30,27),(120,27),(120,180),(30,180)]:poly.Append(xy(x,y))
    b.Add(z);zones.append(z)
pcb.SaveBoard(str(args.board),b)
print('Added In1.Cu and In4.Cu GND planes; refill with the active project rules.')
