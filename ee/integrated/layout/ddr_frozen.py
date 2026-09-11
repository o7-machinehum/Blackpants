"""Fingerprint the DDR copper and component placement the user asked to retain."""
import hashlib,json
from collections import defaultdict
import pcbnew as pcb

def ddr_snapshot(board):
    tracks=defaultdict(list)
    memory_nets={pad.GetNetname() for fp in board.GetFootprints()
                 if fp.GetReference()=='U301' for pad in fp.Pads()
                 if '/DDR_' in pad.GetNetname()}
    for item in board.GetTracks():
        if item.GetNetname() not in memory_nets:
            continue
        a=item.GetStart();z=item.GetEnd()
        via=isinstance(item,pcb.PCB_VIA)
        tracks[item.GetNetname()].append([
            'via' if via else 'track',a.x,a.y,z.x,z.y,
            item.GetLayer(),item.GetWidth(pcb.F_Cu) if via else item.GetWidth(),
            item.GetDrillValue() if via else 0,
            [item.TopLayer(),item.BottomLayer()] if via else [],
        ])
    components={}
    for fp in board.GetFootprints():
        if fp.GetReference() in {'U201','U301'}:
            pos=fp.GetPosition()
            components[fp.GetReference()]=[pos.x,pos.y,fp.GetOrientationDegrees(),fp.GetLayer()]
    return {'components':components,'nets':{
        net:{'objects':len(items),'sha256':hashlib.sha256(json.dumps(sorted(items),separators=(',',':')).encode()).hexdigest()}
        for net,items in sorted(tracks.items())}}
