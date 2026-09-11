#!/usr/bin/env python3
"""Sync fields and pad nets after the initial migration; preserve PCB geometry.

KiCad XML netlists unescape slash characters inside sheet/pin names. Use the
native S-expression export for canonical PCB net names and parity checks.
This does not place new parts or reroute copper if a schematic net splits.
"""
import argparse
from collections import defaultdict
from pathlib import Path
import subprocess
import tempfile
import pcbnew as pcb
from start import BASE, parse, children, one


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board',type=Path)
    args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='a523-netlist-') as tmp:
        netfile=Path(tmp)/'current.net'
        subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadsexpr','-o',str(netfile),str(BASE/'blackpants.kicad_sch')],check=True)
        doc=parse(netfile.read_text())
    comps={one(c,'ref')[1]:c for c in children(one(doc,'components'),'comp')
           if not any(one(p,'name')[1]=='exclude_from_board' for p in children(c,'property'))}
    pin_net={(one(p,'ref')[1],one(p,'pin')[1]):one(n,'name')[1]
             for n in children(one(doc,'nets'),'net') for p in children(n,'node')}
    b=pcb.LoadBoard(str(args.board))
    fs={f.GetReference():f for f in b.GetFootprints()}
    assert fs.keys()==comps.keys(), 'Component set changed; update placement first'
    # The installed HRO footprint calls its shell S1; the USB-C symbol uses SH.
    for ref in ['J8','J101']:
        for p in fs[ref].Pads():
            if p.GetNumber()=='S1':p.SetNumber('SH')
    for p in fs['J105'].Pads():
        if p.GetNumber()=='11':p.SetNumber('SH')
    f=fs['J101'];f.SetAttributes((f.GetAttributes() & ~pcb.FP_SMD) | pcb.FP_THROUGH_HOLE)
    nets={}
    for name in set(pin_net.values()):
        n=b.FindNet(name)
        if n is None:n=pcb.NETINFO_ITEM(b,name);b.Add(n)
        nets[name]=n
    mapping=defaultdict(set)
    for ref,f in fs.items():
        for p in f.Pads():
            if p.GetNetCode() and (ref,p.GetNumber()) in pin_net:
                mapping[p.GetNetCode()].add(pin_net[ref,p.GetNumber()])
    for t in b.GetTracks():
        dest=mapping[t.GetNetCode()]
        assert len(dest)==1,(t.GetNetname(),'Existing copper cannot be mapped unambiguously')
        t.SetNet(nets[next(iter(dest))])
    for ref,f in fs.items():
        c=comps[ref]
        f.SetValue(one(c,'value')[1])
        lib,name=one(c,'footprint')[1].split(':',1)
        f.SetFPID(pcb.LIB_ID(lib,name))
        props={one(p,'name')[1]:(one(p,'value')[1] if children(p,'value') else '') for p in children(c,'property')}
        f.SetExcludedFromBOM('exclude_from_bom' in props)
        f.SetDNP('dnp' in props)
        for field in children(one(c,'fields'),'field'):
            name=one(field,'name')[1]
            if name=='Footprint':continue
            value=field[-1] if isinstance(field[-1],str) else ''
            dest=f.GetField(name)
            if dest is None:
                dest=pcb.PCB_FIELD(f,pcb.FIELD_T_USER,name)
                dest.SetPosition(f.GetPosition());dest.SetVisible(False);f.Add(dest)
            dest.SetText(value)
        for name in ['ki_keywords','ki_fp_filters']:
            if name not in props:continue
            dest=f.GetField(name)
            if dest is None:
                dest=pcb.PCB_FIELD(f,pcb.FIELD_T_USER,name)
                dest.SetPosition(f.GetPosition());dest.SetVisible(False);f.Add(dest)
            dest.SetText(props[name])
        for p in f.Pads():
            name=pin_net.get((ref,p.GetNumber()))
            p.SetNet(nets[name] if name else b.FindNet(0))
    pcb.SaveBoard(str(args.board),b)
    print('Synchronized',len(fs),'footprints, fields and canonical pad nets.')


if __name__=='__main__':main()
