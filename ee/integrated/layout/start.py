#!/usr/bin/env python3
"""Start A523 placement from an explicitly supplied pre-migration PCB backup.

This is a one-time migration, not a generator for subsequent hand-edited boards.
Uses the active schematic XML netlist; never overwrites its source PCB.
"""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'capture'))
from kicad import parse, children, one, dump, Atom

pcb.SwigPyIterator.next = pcb.SwigPyIterator.__next__  # KiCad 10 / Python 3.14
BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
SCALE = 1500000
ORIGIN = (65.0, 54.0)


def xy(x, y):
    return pcb.VECTOR2I(round(x * 1e6), round(y * 1e6))


def mm(p):
    return p.x / 1e6, p.y / 1e6


def route_data():
    source = next((ROOT / 'docs/a523').glob('**/A523-REF-LPDDR4-4X-32X1-S6L-V2-0_pads.asc'))
    routes, net, route = [], None, None
    for line in source.read_text().split('*ROUTE*')[1].split('*POUR*')[0].splitlines():
        a = line.split()
        if not a or a[0] == '*REMARK*':
            continue
        if a[0] == '*SIGNAL*':
            net = a[1]
        elif re.match(r'^[A-Za-z].*\.', a[0]):
            route = {'net': net, 'ends': a, 'points': []}
            routes.append(route)
        elif re.fullmatch(r'-?\d+', a[0]) and route is not None:
            route['points'].append(a)
    return source, routes


def bbox(f):
    b = f.GetBoundingBox(False, False)
    return b.GetX()/1e6, b.GetY()/1e6, b.GetRight()/1e6, b.GetBottom()/1e6


def overlap(a, b, gap=0.15):
    return a[0] < b[2]+gap and a[2] > b[0]-gap and a[1] < b[3]+gap and a[3] > b[1]-gap


def place(f, x, y, angle=0, back=True):
    f.SetLocked(False)
    if f.GetLayer() == pcb.B_Cu:
        f.Flip(f.GetPosition(), True)
    f.SetOrientationDegrees(angle)
    f.SetPosition(xy(x, y))
    if back:
        f.Flip(f.GetPosition(), True)


def six_layers(path):
    # The Python API does not expose BOARD_STACKUP. Edit the structural nodes,
    # then let KiCad parse and write the result. Mirrored Allwinner 1.6 mm stack.
    doc = parse(path.read_text())
    one(one(doc, 'general'), 'thickness')[1] = Atom('1.6')
    layers = one(doc, 'layers')
    b_index = next(i for i,n in enumerate(layers) if isinstance(n,list) and n[1] == 'B.Cu')
    layers[b_index:b_index] = [[Atom('8'), 'In3.Cu', Atom('signal')], [Atom('10'), 'In4.Cu', Atom('signal')]]
    setup = one(doc, 'setup')
    stack = one(setup, 'stackup')
    entries = []
    for name, kind, thick, er in [
        ('F.SilkS','Top Silk Screen',None,None), ('F.Paste','Top Solder Paste',None,None),
        ('F.Mask','Top Solder Mask',.0127,None), ('F.Cu','copper',.04064,None),
        ('dielectric 1','prepreg',.07366,4.0), ('In1.Cu','copper',.03048,None),
        ('dielectric 2','core',.56124,4.2), ('In2.Cu','copper',.03048,None),
        ('dielectric 3','prepreg',.1016,4.0), ('In3.Cu','copper',.03048,None),
        ('dielectric 4','core',.56124,4.2), ('In4.Cu','copper',.03048,None),
        ('dielectric 5','prepreg',.07366,4.0), ('B.Cu','copper',.04064,None),
        ('B.Mask','Bottom Solder Mask',.0127,None), ('B.Paste','Bottom Solder Paste',None,None),
        ('B.SilkS','Bottom Silk Screen',None,None)]:
        n = [Atom('layer'),name,[Atom('type'),kind]]
        if thick is not None: n.append([Atom('thickness'),Atom(str(thick))])
        if er: n += [[Atom('material'),'FR4'],[Atom('epsilon_r'),Atom(str(er))],[Atom('loss_tangent'),Atom('0.02')]]
        entries.append(n)
    stack[1:] = entries + [[Atom('copper_finish'),'ENIG'],[Atom('dielectric_constraints'),Atom('yes')]]
    path.write_text(dump(doc)+'\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--netlist', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert args.source.resolve() != args.output.resolve()
    source_doc = parse(args.source.read_text())
    source_doc[:] = [n for n in source_doc if not (isinstance(n,list) and n[0]=='zone' and not children(n,'keepout'))]
    for fp in children(source_doc,'footprint'):
        props={n[1]:n[2] for n in children(fp,'property')}
        if props.get('Reference')=='J701':
            # An inherited footprint drawing was an open board-edge segment,
            # 0.01 mm beside the actual straight board edge. It is a body guide.
            for graphic in children(fp,'fp_line'):
                if one(graphic,'layer')[1]=='Edge.Cuts':one(graphic,'layer')[1]='Dwgs.User'
    args.output.write_text(dump(source_doc)+'\n')
    b = pcb.LoadBoard(str(args.output))
    old = {f.GetReference():f for f in b.GetFootprints()}
    assert old['U201'].GetValue() == 'A33', 'Source must be the pre-A523 board'
    netlist = ET.parse(args.netlist).getroot()
    comps = {c.get('ref'):c for c in netlist.findall('components/comp') if c.find("property[@name='exclude_from_board']") is None}
    pin_net = {(n.get('ref'),n.get('pin')):net.get('name') for net in netlist.findall('nets/net') for n in net.findall('node') if n.get('ref') in comps}
    endpoints = defaultdict(set)
    for pin, net in pin_net.items(): endpoints[net].add(pin)
    old_endpoints = defaultdict(set)
    for f in old.values():
        for p in f.Pads():
            if p.GetNetCode(): old_endpoints[p.GetNetname()].add((f.GetReference(),p.GetNumber()))
    # Retain mechanics and established peripheral placements. Reused reference
    # numbers in the old CPU/power design must not imply component equivalence.
    stable_hardware = {'J101','J105','J701','J801','JP801','R703','C701','C702'}
    stable = set()
    for ref,c in comps.items():
        if ref not in old: continue
        sheet = c.find('sheetpath').get('names')
        if not sheet.startswith('/A523 system/') or ref in stable_hardware:
            libid = c.findtext('footprint')
            old_id = old[ref].GetFPID()
            if libid == str(old_id.GetLibNickname())+':'+str(old_id.GetLibItemName()) or ref in {'J4','J5','J8','PWR_BUTTON1'}:
                stable.add(ref)
    stable -= {'F1','S1'}
    removed = sorted(set(old)-stable)
    for ref in removed: b.Remove(old[ref])
    nets = {name:b.FindNet(name) for name in endpoints if b.FindNet(name) is not None}
    for name in endpoints:
        if name not in nets:
            n=pcb.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
    table = parse((BASE/'fp-lib-table').read_text())
    libraries={one(e,'name')[1]:Path(one(e,'uri')[1].replace('${KIPRJMOD}',str(BASE))) for e in children(table,'lib')}
    footprints={r:old[r] for r in stable}
    new=[]
    for ref,c in comps.items():
        lib,name = c.findtext('footprint').split(':',1)
        if ref in stable:
            f=footprints[ref]
        else:
            f=pcb.FootprintLoad(str(libraries.get(lib,Path('/usr/share/kicad/footprints')/(lib+'.pretty'))),name)
            assert f is not None, (ref,lib,name)
            b.Add(f);footprints[ref]=f;new.append(ref)
        f.SetReference(ref);f.SetValue(c.findtext('value'))
        f.SetFPID(pcb.LIB_ID(lib,name))
        f.SetPath(pcb.KIID_PATH(c.find('sheetpath').get('tstamps')+c.findtext('tstamps').split()[0]))
        props={p.get('name'):p.get('value') for p in c.findall('property')}
        f.SetSheetname(props.get('Sheetname',''))
        f.SetSheetfile(props.get('Sheetfile',''))
        f.SetDNP('dnp' in props)
        if ref in {'J8','J101'}:
            for pad in f.Pads():
                if pad.GetNumber()=='S1':pad.SetNumber('SH')
        if ref=='J101':f.SetAttributes((f.GetAttributes() & ~pcb.FP_SMD) | pcb.FP_THROUGH_HOLE)
        if ref=='J105':
            for pad in f.Pads():
                if pad.GetNumber()=='11':pad.SetNumber('SH')
        for p in f.Pads():
            name=pin_net.get((ref,p.GetNumber()))
            p.SetNet(nets[name] if name else b.FindNet(0))
        if ref in new:
            f.Value().SetVisible(False)
            f.Reference().SetTextSize(xy(.65,.65))
            f.Reference().SetTextThickness(pcb.FromMM(.1))
    remapped={}
    for name, pins in old_endpoints.items():
        if not pins or any(r not in stable for r,p in pins):continue
        candidates={pin_net.get(pin) for pin in pins}
        if len(candidates)==1 and None not in candidates:
            dest=candidates.pop()
            if endpoints[dest] == pins:remapped[name]=dest
    removed_copper=0
    # Keep detached SWIG objects alive until after SaveBoard (KiCad 10).
    old_tracks = list(b.GetTracks())
    smd_pads=[p for r in stable for p in footprints[r].Pads() if p.GetAttribute()==pcb.PAD_ATTRIB_SMD]
    for t in old_tracks:
        name=t.GetNetname()
        if remapped.get(name) in ['/USB.D+','/USB.D-'] or (isinstance(t,pcb.PCB_VIA) and any(p.HitTest(t.GetPosition(),t.GetDrillValue()//2+pcb.FromMM(.075)) for p in smd_pads)):
            b.Remove(t);removed_copper+=1;continue
        # Ground copper only retained outside the replaced upper electronics.
        if name=='GND' and min(t.GetStart().y,t.GetEnd().y)/1e6 > 90:
            t.SetNet(nets['GND'])
        elif name in remapped:
            t.SetNet(nets[remapped[name]])
        else:
            b.Remove(t);removed_copper+=1;continue
        if t.GetLayer()==pcb.In1_Cu:t.SetLayer(pcb.In2_Cu)
        elif t.GetLayer()==pcb.In2_Cu:t.SetLayer(pcb.In3_Cu)
    fixed={
        'U201':(65,54,45,True),'U301':(65+30957012/SCALE,54-1877187/SCALE,0,True),
        'U501':(101,63,0,True),'U502':(67,77,0,True),
        'U701':(47,50,90,False),
        'U901':(102,35,0,True),'U7':(95,90,0,True),
        'U402':(52,84,0,True),'U801':(76,34,0,True),
        'L501':(95,66,0,True),'L502':(101,69,90,True),'L503':(107,65,0,True),
        'L504':(107,57,0,True),'L505':(62,77,0,True),'L506':(67,72,90,True),'L507':(72,77,0,True),
        'L901':(106.8,35,0,True),'L902':(100,90,0,True),'L801':(77,29.7,0,True),
        'F1':(42,177.2,0,True),'TH901':(53,177,0,True),
        'SW101':(44,71,0,True),'J102':(41.5,83,0,True),'J103':(41.5,33,90,True),
        'Y201':(70,43,0,True),'Y202':(63,41,0,True),
        'D902':(109,43,0,True), 'S1':(91,144,0,True),
    }
    for ref,coord in fixed.items():place(footprints[ref],*coord)
    placed=set(stable)|set(fixed)
    copper_obstacles={pcb.F_Cu:[],pcb.B_Cu:[]}
    for t in b.GetTracks():
        x1,y1=mm(t.GetStart());x2,y2=mm(t.GetEnd());w=t.GetWidth()/2e6
        rect=(min(x1,x2)-w,min(y1,y2)-w,max(x1,x2)+w,max(y1,y2)+w)
        for face in copper_obstacles:
            if isinstance(t,pcb.PCB_VIA) or t.GetLayer()==face:copper_obstacles[face].append(rect)
    _,reference_routes=route_data()
    ref_vias={(int(p[0])/SCALE+ORIGIN[0],int(p[1])/SCALE+ORIGIN[1]) for r in reference_routes for p in r['points'] if 'VIA8X16' in p}
    copper_obstacles[pcb.F_Cu] += [(x-.2032,y-.2032,x+.2032,y+.2032) for x,y in ref_vias]
    # First placement pass: local passives near their connected IC pins. SoC
    # bypass parts use the opposite face, leaving the BGA escape on B.Cu.
    todo=sorted(set(new)-set(fixed),key=lambda r:(r[0]!='C',-max(footprints[r].GetBoundingBox(False,False).GetWidth(),footprints[r].GetBoundingBox(False,False).GetHeight())))
    for ref in todo:
        f=footprints[ref];sheet=comps[ref].find('sheetpath').get('names')
        core=('/SoC support/' in sheet or '/Peripheral IO/' in sheet)
        dram='/2GB LPDDR4/' in sheet
        anchor='U201' if core else 'U301' if dram else 'U501' if 'AXP717C' in sheet else 'J8'
        if 'CPU big / DNR' in sheet:anchor='U502'
        if 'MicroSD' in sheet:anchor='J105'
        if 'Wi-Fi / Bluetooth/' in sheet and not core:anchor='U701'
        if 'Display / backlight' in sheet:anchor='U801'
        if 'Recovery / UART' in sheet:anchor='U402' if ref in {'C401','JP101'} else 'J101'
        if '5V / 3.3V' in sheet:anchor='U7' if int(re.sub(r'\D','',ref))>=920 or ref=='D901' else 'U901'
        if ref in {'R201','C250','C251'}:anchor='Y201'
        if ref in {'R202','C252','C253'}:anchor='Y202'
        f_nets={p.GetNetname() for p in f.Pads()}-{'GND'}
        target=[mm(p.GetPosition()) for p in footprints[anchor].Pads() if p.GetNetname() in f_nets]
        tx,ty=(sum(p[0] for p in target)/len(target),sum(p[1] for p in target)/len(target)) if target else mm(footprints[anchor].GetPosition())
        back=not(core or dram) if anchor not in {'Y201','Y202'} else True
        if anchor=='U701':back=False
        candidates=[]
        for dx in range(-28,29):
            for dy in range(-28,29):
                x,y=round(tx*2)/2+dx*.5,round(ty*2)/2+dy*.5
                if 33 < x < 116 and 29 < y < 120:candidates.append(((x-tx)**2+(y-ty)**2,x,y))
        obstacles=[bbox(footprints[r]) for r in placed if footprints[r].GetLayer()==(pcb.B_Cu if back else pcb.F_Cu) or r.startswith(('H','J'))]
        obstacles += copper_obstacles[pcb.B_Cu if back else pcb.F_Cu]
        for _,x,y in sorted(candidates):
            place(f,x,y,0,back)
            box=bbox(f)
            if box[0]<31 or box[2]>119 or box[1]<28 or box[3]>120:continue
            if not any(overlap(box,o) for o in obstacles):break
        else:raise RuntimeError('No initial placement for '+ref)
        placed.add(ref)
    b.SetCopperLayerCount(6)
    b.GetDesignSettings().SetBoardThickness(pcb.FromMM(1.6))
    pcb.SaveBoard(str(args.output),b)
    # SetCopperLayerCount already added the copper layer definitions.
    doc=parse(args.output.read_text()); layers=one(doc,'layers')
    layers[:]=[n for n in layers if not (isinstance(n,list) and len(n)>1 and n[1] in ['In3.Cu','In4.Cu'])]
    args.output.write_text(dump(doc)+'\n')
    six_layers(args.output)
    b=pcb.LoadBoard(str(args.output))
    pcb.SaveBoard(str(args.output),b)
    report={'source':str(args.source),'netlist':str(args.netlist),'footprints':len(comps),'retained_placements':sorted(stable),
            'removed_old_footprints':removed,'removed_old_copper_items':removed_copper,'retained_copper_items':len(list(b.GetTracks())),
            'copper_layers':b.GetCopperLayerCount(),'status':'Initial placement; routing and DRC closure still required.'}
    args.output.with_suffix('.layout.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if not isinstance(v,list)},indent=2))


if __name__=='__main__':main()
