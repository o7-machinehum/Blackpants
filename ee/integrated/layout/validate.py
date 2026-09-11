#!/usr/bin/env python3
"""Check schematic parity and via restrictions, and report full connectivity.

Use --require-complete as a routing-completion gate. Physical checks alone do
not establish signal integrity, power integrity or manufacturing readiness.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import tempfile
import pcbnew as pcb
from start import BASE, parse, children, one
from ddr_frozen import ddr_snapshot


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board',type=Path,default=BASE/'blackpants.kicad_pcb')
    ap.add_argument('--report',type=Path,default=BASE/'layout/validation.json')
    ap.add_argument('--require-complete',action='store_true')
    args=ap.parse_args()
    project=json.loads(args.board.with_suffix('.kicad_pro').read_text())
    assert project['board']['design_settings']['rule_severities']['clearance']=='error'
    with tempfile.TemporaryDirectory(prefix='a523-pcb-check-') as tmp:
        net=Path(tmp)/'board.net'
        subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadsexpr','-o',str(net),str(BASE/'blackpants.kicad_sch')],check=True)
        doc=parse(net.read_text())
    comps={one(c,'ref')[1]:c for c in children(one(doc,'components'),'comp')
           if not any(one(p,'name')[1]=='exclude_from_board' for p in children(c,'property'))}
    pin_net={(one(p,'ref')[1],one(p,'pin')[1]):one(n,'name')[1]
             for n in children(one(doc,'nets'),'net') for p in children(n,'node') if one(p,'ref')[1] in comps}
    b=pcb.LoadBoard(str(args.board))
    baseline=json.loads((BASE/'layout/ddr-frozen.json').read_text())
    assert ddr_snapshot(b)==baseline, 'DDR routing or SoC/RAM placement changed from the frozen baseline'
    fs={f.GetReference():f for f in b.GetFootprints()}
    assert fs.keys()==comps.keys()
    assert b.GetCopperLayerCount()==6
    assert abs(b.GetDesignSettings().GetBoardThickness()/1e6-1.6)<.001
    actual={}
    for ref,f in fs.items():
        assert f.GetValue()==one(comps[ref],'value')[1],ref
        for p in f.Pads():
            if not p.GetNumber():continue
            key=(ref,p.GetNumber())
            assert p.GetNetname()==pin_net.get(key,''),(key,p.GetNetname(),pin_net.get(key))
            actual[key]=p.GetNetname()
    assert actual.keys()>=pin_net.keys(),pin_net.keys()-actual.keys()
    assert fs['U201'].GetValue()=='A523'
    vias=[t for t in b.GetTracks() if isinstance(t,pcb.PCB_VIA)]
    smd=[(ref,p) for ref,f in fs.items() for p in f.Pads() if p.GetAttribute()==pcb.PAD_ATTRIB_SMD and
         (p.IsOnLayer(pcb.F_Cu) or p.IsOnLayer(pcb.B_Cu))]
    thermal_pads={('U501','53'),('U502','21'),('U901','11'),('U1','49')}
    thermal_vias=defaultdict(set)
    for v in vias:
        assert v.GetViaType()==pcb.VIATYPE_THROUGH
        assert (v.TopLayer(),v.BottomLayer())==(pcb.F_Cu,pcb.B_Cu)
        assert v.GetWidth(pcb.F_Cu)==pcb.FromMM(.4), ('Via pad diameter', v.m_Uuid.AsString())
        assert v.GetDrillValue()==pcb.FromMM(.2), ('Via drill diameter', v.m_Uuid.AsString())
        for ref,p in smd:
            if ((ref,p.GetNumber()) in thermal_pads and
                    v.GetNetname()==p.GetNetname()=='GND' and
                    p.HitTest(v.GetPosition())):
                thermal_vias[ref].add(v.m_Uuid.AsString())
                continue
            assert not p.HitTest(v.GetPosition(),v.GetDrillValue()//2),('Via drill in solder pad',ref,p.GetNumber())
    planes=[z for z in b.Zones() if not z.GetIsRuleArea()]
    assert {(pcb.In1_Cu,'GND'),(pcb.In4_Cu,'GND')} <= {(z.GetLayer(),z.GetNetname()) for z in planes}
    assert all(z.GetNetCode()>0 for z in planes)
    assert all(z.GetNetname()=='GND' for z in planes
               if z.IsOnLayer(pcb.In1_Cu) or z.IsOnLayer(pcb.In4_Cu))
    connectivity=b.GetConnectivity()
    connectivity.Build(b)
    connectivity.RecalculateRatsnest()
    # Native DRC truncates the unconnected-items list. This is the full count.
    open_connections=connectivity.GetUnconnectedCount(False)
    soc={p.GetNetname():p for p in fs['U201'].Pads() if '/DDR_' in p.GetNetname()}
    ram={p.GetNetname():p for p in fs['U301'].Pads() if '/DDR_' in p.GetNetname()}
    ddr_paths={net:any(item.m_Uuid==ram[net].m_Uuid
                       for item in connectivity.GetConnectedItems(soc[net]))
               for net in sorted(soc.keys() & ram.keys())}
    assert len(ddr_paths)==65
    seen=set()
    groups=defaultdict(list)
    pad_refs={pad.m_Uuid.AsString():(ref,pad) for ref,f in fs.items() for pad in f.Pads()}
    for uid,(ref,pad) in pad_refs.items():
        if uid in seen or not pad.GetNetCode():continue
        items=list({item.m_Uuid.AsString():item
                    for item in [pad,*connectivity.GetConnectedItems(pad)]}.values())
        seen.update(item.m_Uuid.AsString() for item in items)
        members=[]
        for item in items:
            key=item.m_Uuid.AsString()
            if key not in pad_refs:continue
            r,p=pad_refs[key]
            members.append({'reference':r,'pad':p.GetNumber(),
                            'position_mm':[p.GetPosition().x/1e6,p.GetPosition().y/1e6]})
        groups[pad.GetNetname()].append(members)
    outstanding={net:parts for net,parts in sorted(groups.items()) if len(parts)>1}
    result={'physical_components':len(fs),'schematic_pins_checked':len(pin_net),
            'copper_layers':6,'through_vias':len(vias),
            'via_pad_diameter_mm':0.4,'via_drill_diameter_mm':0.2,
            'exposed_ground_pad_thermal_vias':{ref:len(ids) for ref,ids in sorted(thermal_vias.items())},
            'ddr_routing_matches_frozen_baseline':True,
            'ddr_soc_to_ram_connections':sum(ddr_paths.values()),
            'ddr_soc_to_ram_total':len(ddr_paths),
            'ddr_soc_to_ram_unconnected':[net for net,connected in ddr_paths.items() if not connected],
            'unconnected_count':open_connections,
            'routing_complete':open_connections==0,
            'status':'Pin/net and via geometry checks pass; timing and power integrity are not approved.'}
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    args.report.with_name('unconnected-nets.json').write_text(json.dumps(outstanding,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if args.require_complete and open_connections:
        raise SystemExit(f'Routing incomplete: {open_connections} open connections')


if __name__=='__main__':main()
