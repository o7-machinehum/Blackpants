#!/usr/bin/env python3
"""Import vendor DDR routes whose physical endpoints match this netlist.

The capture uses the reference's within-byte DQ swizzle. Both physical endpoints
must still match; unused rank-control routes are skipped.
"""
import argparse
import json
import math
from pathlib import Path
import pcbnew as pcb
from start import route_data, SCALE, ORIGIN, xy, mm

pcb.SwigPyIterator.next = pcb.SwigPyIterator.__next__


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board',type=Path)
    args=ap.parse_args()
    b=pcb.LoadBoard(str(args.board))
    assert b.GetCopperLayerCount()==6
    fs={f.GetReference():f for f in b.GetFootprints()}
    pads={(r,p.GetNumber()):p for r,f in fs.items() for p in f.Pads()}
    assert mm(fs['U201'].GetPosition())==ORIGIN
    assert not any('/DDR_' in t.GetNetname() for t in b.GetTracks()), 'Already imported'
    source,routes=route_data()
    layer={1:pcb.B_Cu,2:pcb.In4_Cu,3:pcb.In3_Cu,4:pcb.In2_Cu,5:pcb.In1_Cu,6:pcb.F_Cu}
    report={'source':str(source),'imported':[],'skipped':[]}
    seen=set()
    for r in routes:
        if set(e.split('.')[0] for e in r['ends'])!={'U1','UD1'}:continue
        ends=[pads[{'U1':'U201','UD1':'U301'}[e.split('.')[0]],e.split('.')[1]] for e in r['ends']]
        net=ends[0].GetNetname()
        if ends[1].GetNetname()!=net:
            report['skipped'].append({'reference_net':r['net'],'pins':r['ends'],'reason':'Physical endpoints differ in the active schematic'})
            continue
        if '/DDR_' not in net:continue
        pts=[p for p in r['points'] if int(p[2])!=65]
        coords=[xy(ORIGIN[0]+int(p[0])/SCALE,ORIGIN[1]+int(p[1])/SCALE) for p in pts]
        for i,pad in [(0,ends[0]),(-1,ends[1])]:
            assert math.dist(mm(coords[i]),mm(pad.GetPosition()))<.001,(r['net'],i)
            coords[i]=pad.GetPosition()
        lengths={}
        for i in range(len(pts)-1):
            src=pts[i];l=int(src[2]);assert l in layer,(r['net'],src)
            t=pcb.PCB_TRACK(b);t.SetStart(coords[i]);t.SetEnd(coords[i+1])
            t.SetWidth(round(int(src[3])*1e6/SCALE));t.SetLayer(layer[l]);t.SetNet(ends[0].GetNet())
            # Preserve reference widths. Any conflicts with the selected lands
            # require path changes and DRC, not automatic electrical neckdowns.
            b.Add(t)
            lengths[l]=lengths.get(l,0)+math.dist(mm(coords[i]),mm(coords[i+1]))
        nvias=0
        for p,coord in zip(pts,coords):
            if 'VIA8X16' not in p:continue
            key=(coord.x,coord.y,net)
            if key in seen:continue
            seen.add(key)
            # No drill is permitted to intersect either BGA's copper pads.
            for ref in ['U201','U301']:
                for pad in fs[ref].Pads():
                    assert math.dist(mm(coord),mm(pad.GetPosition())) > .1+pad.GetSize().x/2e6+.075,(r['net'],pad.GetNumber())
            v=pcb.PCB_VIA(b);v.SetPosition(coord);v.SetWidth(pcb.FromMM(.4));v.SetDrill(pcb.FromMM(.2))
            v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(ends[0].GetNet());b.Add(v);nvias+=1
        report['imported'].append({'net':net,'reference_net':r['net'],'pins':r['ends'],'length_mm':sum(lengths.values()),'layer_lengths_mm':lengths,'vias':nvias})
    pcb.SaveBoard(str(args.board),b)
    args.board.with_suffix('.ddr.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Imported',len(report['imported']),'matching DDR routes; skipped',len(report['skipped']),'different/unused connections.')


if __name__=='__main__':main()
