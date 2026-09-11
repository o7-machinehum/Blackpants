#!/usr/bin/env python3
"""Nanya 16Gb, dual-channel LPDDR4: datasheet V1.8 p8 ball map, p10 package."""
import csv
import json
import re
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
PDF=HERE.parents[2]/'docs/a523/NT6AN512T32AV_LPDDR4_V1.8.pdf'
NAME='NT6AN512T32AV-J2'
FP='FBGA-200_10x15mm_P0.8x0.65mm'
ROWS='A B C D E F G H J K L M N P R T U V W Y AA AB'.split()
q=json.dumps


def pins():
    text=subprocess.check_output(['pdftotext','-f','8','-l','8','-layout',str(PDF),'-'],text=True)
    result=[]
    for line in text.splitlines():
        fields=line.split()
        if len(fields)==12 and fields[0] in ROWS and fields[-1]==fields[0]:
            for col,name in zip([1,2,3,4,5,8,9,10,11,12],fields[1:-1]):
                name=name.replace('\uf044\uf051\uf053','DQS_N').replace('\uf043\uf04b','CK_N').replace('\uf052\uf045\uf053\uf045\uf054','RESET_N')
                # Give true/complement clocks explicit P/N suffixes.
                name=re.sub(r'^DQS([01])_',r'DQS_P\1_',name)
                name=re.sub(r'^CK_',r'CK_P_',name) if name.startswith('CK_a') or name.startswith('CK_b') else name
                etype=('power_in' if name in ['VDD1','VDD2','VDDQ','VSS'] else
                       'no_connect' if name in ['NC','DNU'] else
                       'bidirectional' if name.startswith(('DQ','DMI')) else 'passive' if name=='ZQ' else 'input')
                result.append(dict(ball=fields[0]+str(col),name=name,type=etype))
    assert len(result)==200 and len({p['ball'] for p in result})==200
    assert {p['name'] for p in result if p['ball'] in ['E3','J9','T11']}=={'DQS_N0_a','CK_N_a','RESET_N'}
    return result


def main():
    data=pins()
    # Arrange the data pins in A523 signal order while retaining every physical
    # Nanya pin name/ball number. This keeps the swizzled schematic wires straight.
    swizzle=json.loads((HERE/'a523-swizzle.json').read_text())['soc_to_ram_dq']
    assert sorted(swizzle)==list(range(32))
    assert all(i//8==j//8 for i,j in enumerate(swizzle))
    strobes=['DMI0','DMI1','DQS_P0','DQS_N0','DQS_P1','DQS_N1']
    by_name={p['name']:p for p in data}
    channel_a=[by_name[n+'_a'] for n in [f'DQ{i}' for i in swizzle[:16]]+strobes]
    channel_b=[by_name[n+'_b'] for n in [f'DQ{i-16}' for i in swizzle[16:]]+strobes]
    groups=[('Channel A data',channel_a), ('Channel B data',channel_b),
            ('Command / clock / reset / ZQ',[p for p in data if (p['name'].endswith(('_a','_b')) or p['name'] in ['RESET_N','ZQ']) and p not in channel_a+channel_b]),
            ('Power',[p for p in data if p['name'].startswith('VDD')]),
            ('Ground',[p for p in data if p['name']=='VSS']),
            ('Do not connect',[p for p in data if p['name'] in ['NC','DNU']])]
    assert sum(len(g) for _,g in groups)==200
    lib=['(kicad_symbol_lib (version 20241209) (generator "lpddr4_generator")',f'(symbol "{NAME}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
         '(property "Reference" "U" (at 0 12.7 0) (effects (font (size 1.27 1.27))))',
         f'(property "Value" "{NAME}" (at 0 10.16 0) (effects (font (size 1.27 1.27))))',
         f'(property "Footprint" "LPDDR4:{FP}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
         '(property "Datasheet" "${KIPRJMOD}/../../docs/a523/NT6AN512T32AV_LPDDR4_V1.8.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
         '(property "Description" "Nanya 16Gb (2GB) LPDDR4, dual die, 2 x 16-bit channels, FBGA-200" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))']
    for unit,(title,group) in enumerate(groups,1):
        if unit>2:
            group.sort(key=lambda p:(p['name'],ROWS.index(re.sub(r'\d','',p['ball'])),int(re.sub(r'\D','',p['ball']))))
        half=len(group) if unit<=2 else (len(group)+1)//2
        width=17.78 if unit<=2 else 22.86
        lib += [f'(symbol "{NAME}_{unit}_1"',
                f'(rectangle (start {-width} 7.62) (end {width} {-half*2.54}) (stroke (width 0.254) (type default)) (fill (type background)))',
                f'(text {q(title)} (at 0 5.08 0) (effects (font (size 1.016 1.016))))']
        for i,p in enumerate(group):
            side=(1 if unit==1 else -1) if unit<=2 else (-1 if i<half else 1)
            p['unit']=unit
            lib.append(f'(pin {p["type"]} line (at {side*(width+5.08)} {-(i%half)*2.54:.2f} {0 if side<0 else 180}) (length 5.08) (name {q(p["name"])} (effects (font (size 1.016 1.016)))) (number {q(p["ball"])} (effects (font (size 1.016 1.016)))))')
        lib.append(')')
    lib.append('))')
    (HERE/'LPDDR4.kicad_sym').write_text('\n'.join(lib)+'\n')
    with (HERE/'pinout.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=['ball','name','type','unit']);w.writeheader();w.writerows(data)
    fp=[f'(footprint "{FP}" (version 20241229) (generator "lpddr4_generator") (layer "F.Cu") (attr smd)',
        '(descr "Nanya NT6AN512T32AV, 200 balls, 10x15mm body; 0.8mm X / 0.65mm Y pitch")',
        '(solder_mask_margin 0.05)',
        '(fp_text reference "REF**" (at 0 -8.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
        '(fp_text value "NT6AN512T32AV" (at 0 8.5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
        '(fp_rect (start -5 -7.5) (end 5 7.5) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',
        '(fp_rect (start -5.55 -8.05) (end 5.55 8.05) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
        '(fp_rect (start -5.12 -7.62) (end 5.12 7.62) (stroke (width 0.12) (type default)) (fill none) (layer "F.SilkS"))',
        '(fp_line (start -5 -6.5) (end -4 -7.5) (stroke (width 0.1) (type default)) (layer "F.Fab"))',
        '(fp_poly (pts (xy -5.35 -7.85) (xy -5.85 -7.85) (xy -5.35 -8.35)) (stroke (width 0.1) (type default)) (fill solid) (layer "F.SilkS"))']
    for p in data:
        row,col=re.fullmatch(r'([A-Z]+)(\d+)',p['ball']).groups()
        x=(int(col)-6.5)*0.8;y=(ROWS.index(row)-10.5)*0.65
        fp.append(f'(pad "{p["ball"]}" smd circle (at {x:.3f} {y:.3f}) (size 0.3 0.3) (layers "F.Cu" "F.Mask" "F.Paste"))')
    fp.append(')')
    (HERE/'LPDDR4.pretty'/f'{FP}.kicad_mod').write_text('\n'.join(fp)+'\n')
    print('Generated 200-pin Nanya LPDDR4 in 6 units.')


if __name__=='__main__':main()
