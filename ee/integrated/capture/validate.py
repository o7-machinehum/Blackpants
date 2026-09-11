#!/usr/bin/env python3
"""Check source pin maps, saved KiCad parts, and critical captured connections."""
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from kicad import BASE, parse, children, one

DOCS=BASE.parents[1]/'docs/a523'


def symbol_pins(path,name):
    sym=next(s for s in children(parse(path.read_text()),'symbol') if s[1]==name)
    found={}
    for unit in children(sym,'symbol'):
        positions=set()
        for p in children(unit,'pin'):
            number=one(p,'number')[1]
            assert number not in found
            at=tuple(one(p,'at')[1:3]);assert at not in positions
            positions.add(at);found[number]=one(p,'name')[1]
    return found


def main():
    checked={}
    with tempfile.TemporaryDirectory(prefix='a523-capture-check-') as tmp:
        tmp=Path(tmp)
        for name,n in [('AXP717C',52),('AXP323',20)]:
            pdf=DOCS/f'pmu_xpowers/{name}_Datasheet_V1.1_en.pdf'
            text=subprocess.check_output(['pdftotext','-f','7','-l','8' if n==52 else '7','-layout',str(pdf),'-'],text=True)
            vendor={}
            for numbers,label in re.findall(r'^\s*(\d+(?:/\d+)*)\s+([A-Z][A-Z0-9]+)\s+',text,re.M):
                for number in numbers.split('/'):
                    if 1<=int(number)<=n:vendor[number]=label
            assert len(vendor)==n,(name,len(vendor))
            vendor[str(n+1)]='EP'
            assert symbol_pins(BASE/'AXP/AXP.kicad_sym',name)==vendor
            checked[name]=vendor
        # Package-corner and complementary-clock spot checks from the PDF ball map.
        ram={p['ball']:p['name'] for p in csv.DictReader((BASE/'LPDDR4/pinout.csv').open())}
        assert len(ram)==200
        assert symbol_pins(BASE/'LPDDR4/LPDDR4.kicad_sym','NT6AN512T32AV-J2')==ram
        for ball,name in [('B2','DQ0_a'),('AA2','DQ0_b'),('E3','DQS_N0_a'),('V10','DQS_N1_b'),('J9','CK_N_a'),('P9','CK_N_b'),('T11','RESET_N'),('A5','ZQ')]:
            assert ram[ball]==name,(ball,name)
        checked['NT6AN512T32AV-J2']=ram
        for folder in ['AXP','LPDDR4']:
            original=BASE/f'{folder}/{folder}.kicad_sym';canonical=tmp/f'{folder}.kicad_sym'
            subprocess.run(['kicad-cli','sym','upgrade','--force','--output',str(canonical),str(original)],check=True,capture_output=True)
            for name,pins in checked.items():
                if (name.startswith('AXP'))==(folder=='AXP'):
                    assert symbol_pins(canonical,name)==pins
        import pcbnew
        for folder,name,count,anchors in [
            ('AXP','QFN-52-1EP_6x6mm_P0.4mm_EP4.6x4.6mm',53,{'1':(-2.885,-2.4),'14':(-2.4,2.885),'27':(2.885,2.4),'40':(2.4,-2.885),'53':(0,0)}),
            ('AXP','QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm',21,{'1':(-1.385,-.8),'6':(-.8,1.385),'11':(1.385,.8),'16':(.8,-1.385),'21':(0,0)}),
            ('LPDDR4','FBGA-200_10x15mm_P0.8x0.65mm',200,{'A1':(-4.4,-6.825),'A12':(4.4,-6.825),'AB1':(-4.4,6.825),'AB12':(4.4,6.825)})]:
            fp=pcbnew.FootprintLoad(str(BASE/f'{folder}/{folder}.pretty'),name);assert fp
            pads=[p for p in fp.Pads() if p.GetNumber()]
            assert len(pads)==len({p.GetNumber() for p in pads})==count
            by_number={p.GetNumber():p for p in pads}
            for number,(x,y) in anchors.items():
                pos=by_number[number].GetPosition()
                assert abs(pos.x-pcbnew.FromMM(x))<=1 and abs(pos.y-pcbnew.FromMM(y))<=1
        netfile=tmp/'capture.xml'
        subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(netfile),str(BASE/'blackpants.kicad_sch')],check=True,capture_output=True)
        xml=ET.parse(netfile).getroot()
        nets={n.get('name'):{(p.get('ref'),p.get('pin')) for p in n} for n in xml.find('nets')}
        pin_net={p:name for name,ps in nets.items() for p in ps}
        # Pin groups are independent electrical assertions, not a rendering test.
        expected={
            '/PMU_SCL':{('U501','52'),('U502','6'),('U201','AJ7'),('R501','2')},
            '/PMU_SDA':{('U501','51'),('U502','5'),('U201','AH7'),('R502','2')},
            '/AP_RESET_N':{('U501','1'),('U502','13'),('U201','AC11'),('C259','1'),('R504','2')},
            '/AP_NMI':{('U501','37'),('U201','AD11'),('C258','1'),('R503','2')},
            '/VDD_CPUB_FB':{('U502','16'),('U502','1'),('U201','M19')},
            '/VDD_CPUL_FB':{('U501','12'),('U201','V16')},
            '/VDD_SYS_FB':{('U501','34'),('U201','L15')},
            '/VDD_DNR_FB':{('U502','4'),('U201','W10')},
            '/VCC_DRAM_FB':{('U501','29'),('NT301','2')},
            'VBUS':{('U501','49'),('U501','50'),('C501','1'),('J8','A4'),('J8','A9'),('J8','B4'),('J8','B9'),('U12','5'),('C901','1'),('R905','1')},
            'VBAT':{('U501','41'),('U501','42'),('C506','1'),('C507','1'),('F1','1')},
            'PMIC_VMID':{('U501','47'),('U501','48'),('C502','1')},
        }
        for name,pins in expected.items():
            name='/A523 system'+name if name.startswith('/') else name
            assert nets[name]==pins,(name,nets[name]^pins)
        for pin,net in {'13':'ALDO1_UNUSED','14':'VCC_PE','16':'VCC_PL','17':'VCC_AVCC','18':'VCC_PG','19':'VDD18_LPDDR','21':'BLDO3_UNUSED','22':'BLDO4_UNUSED','23':'VCC_1V8','24':'CLDO2_UNUSED','26':'VCC_3V3','27':'VCC_LCD','28':'VDD_CPUS','35':'VCC_RTC'}.items():
            assert pin_net['U501',pin]==net,(pin,net)
        assert pin_net['U502','14']=='VDD18_LPDDR'
        for ref,pins in [('U501',['9','32','31','15','20','25']),('U502',['17','20','2'])]:
            for pin in pins:assert pin_net[ref,pin]=='VSYS',(ref,pin,pin_net[ref,pin])
        for name in ['GND','VCC_AVCC','VCC_1V8','VCC_3V3','VDD18_LPDDR','VCC_DRAM','VDD_SYS','VDD_CPUB','VDD_CPUL','VDD_DNR','VCC_PL','VCC_RTC','VDD_CPUS']:
            assert name in nets and len(nets[name])>1,name
        assert pin_net['L505','2']==pin_net['L506','2']=='VDD_CPUB'
        assert pin_net['L505','1']!=pin_net['L506','1']
        assert pin_net['U201','Y14']==pin_net['U201','T20']=='VCC_DRAM'
        assert pin_net['U201','AA21']=='VCC_AVCC'
        assert pin_net['U301','F1']=='VDD18_LPDDR'
        assert pin_net['U301','A4']==pin_net['U301','B3']=='VCC_DRAM'
        # Every memory signal reaches exactly the intended SoC pad.
        soc={p['name']:p['ball'] for p in csv.DictReader((BASE/'A523/pinout.csv').open())}
        # Independently compare the chosen permutation with the vendor PCB,
        # rather than only checking it against the schematic generator's table.
        swizzle=json.loads((BASE/'LPDDR4/a523-swizzle.json').read_text())
        source=BASE.parents[1]/swizzle['source_pcb']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==swizzle['source_pcb_sha256']
        vendor_pairs={int(bit):dict(pin.split('.') for pin in line.split())
                      for bit,line in re.findall(r'\*SIGNAL\* SDQ(\d+) [^\n]*\n([^\n]+)',source.read_text())}
        assert set(vendor_pairs)==set(range(32))
        assert sorted(swizzle['soc_to_ram_dq'])==list(range(32))
        for bit,pair in vendor_pairs.items():
            assert pair['U1']==soc[f'SDQ{bit}']
            assert nets[pin_net['U201',pair['U1']]]=={('U201',pair['U1']),('U301',pair['UD1'])}
            ram_name=ram[pair['UD1']]
            ram_bit=int(re.fullmatch(r'DQ(\d+)_[ab]',ram_name)[1])+(16 if ram_name.endswith('_b') else 0)
            assert swizzle['soc_to_ram_dq'][bit]==ram_bit
            assert bit//8==ram_bit//8
        from memory import dram_net
        for ball,name in ram.items():
            if name.startswith(('DQ','DMI')):
                net=dram_net(name)
                socname=net.replace('DDR_DQ','SDQ').replace('DDR_DM','SDQM').replace('DDR_DQS','SDQS')
                assert nets[pin_net['U301',ball]]=={('U301',ball),('U201',soc[socname])},net
            elif name in ['VDD1','VDD2','VDDQ','VSS']:
                assert pin_net['U301',ball]==dram_net(name),(ball,name)
        for a,b in {'SA1':'CA2_a','SA2':'CA0_a','SA4':'CA1_b','SA6':'CKE_b','SA8':'CA2_b',
                    'SA9':'CA5_a','SA10':'CA3_a','SA11':'CA1_a','SA13':'CS_b','SA14':'CK_P_b',
                    'SA15':'CK_N_b','SA16':'CA4_b','SA17':'CA4_a','SBA0':'CA3_b','SBA1':'CA0_b',
                    'SACT':'CA5_b','SCS0':'CS_a','SCKP':'CK_P_a','SCKN':'CK_N_a',
                    'SCKE0':'CKE_a','SRST':'RESET_N'}.items():
            rb=next(ball for ball,name in ram.items() if name==b)
            assert nets[pin_net['U301',rb]]=={('U301',rb),('U201',soc[a])},(a,b)
        for p in csv.DictReader((BASE/'A523/pinout.csv').open()):
            if p['name'] in ['GND','AVSS','AGND']:
                assert pin_net['U201',p['ball']]=='GND',p['ball']
        assert pin_net['Y201','2']==pin_net['Y201','4']=='GND'
        assert pin_net['Y201','1']==pin_net['U201','AH13']==pin_net['C250','1']
        assert pin_net['Y201','3']==pin_net['C251','1']==pin_net['R201','1']
        assert pin_net['R201','2']==pin_net['U201','AJ13']
        assert pin_net['Y202','1']==pin_net['U201','AH12']==pin_net['C252','1']==pin_net['R202','1']
        assert pin_net['Y202','2']==pin_net['U201','AH11']==pin_net['C253','1']==pin_net['R202','2']
        # End-to-end board interfaces, using physical pad numbers rather than labels.
        for a,b in [
            (('U201','D20'),('U3','31')),(('U201','E20'),('U3','30')),
            (('U201','A18'),('U101','4')),(('U201','B18'),('U101','6')),
            (('J101','A6'),('U101','3')),(('J101','A7'),('U101','1')),
            (('J8','A6'),('U12','3')),(('J8','A7'),('U12','1')),
            (('U12','4'),('U11','7')),(('U12','6'),('U11','6')),
            (('U3','4'),('U11','5')),(('U3','3'),('U11','4')),
            (('U3','9'),('U402','5')),(('U3','8'),('U402','6')),
            (('U501','4'),('R901','2')),(('U501','5'),('R902','2')),
            (('U501','3'),('R903','2')),(('U501','2'),('R904','2')),
            (('U501','39'),('TH901','1')),(('U501','6'),('PWR_BUTTON1','1')),
            (('U201',soc['PB9']),('U402','3')),(('U201',soc['PB10']),('JP101','2')),
            (('U402','2'),('JP101','1')),
            (('U201',soc['FEL']),('SW101','1')),
        ]:assert pin_net[a]==pin_net[b],(a,b,pin_net.get(a),pin_net.get(b))
        for name,pin in [('PF0','8'),('PF1','7'),('PF3','3'),('PF4','2'),('PF5','1'),('PF6','9')]:
            assert pin_net['U201',soc[name]]==pin_net['J105',pin],name
        assert pin_net['R203','2']==pin_net['J105','5']
        for name,pin in [('PD0','4'),('PD1','3'),('PD2','10'),('PD3','9'),('PD4','7'),('PD5','6'),('PB7','12'),('PB6','13')]:
            assert pin_net['U201',soc[name]]==pin_net['J801',pin],name
        assert pin_net['U201',soc['PB8']]==pin_net['U801','1']
        for name,pin in [('PG1','16'),('PG2','18'),('PG3','19'),('PG4','14'),('PG5','15'),('PG6','43'),('PG7','42'),('PG8','44'),('PG9','41'),('PH0','12'),('PH1','13'),('PH2','34'),('PH3','6'),('PH4','7'),('X32KFOUT','24')]:
            assert pin_net['U201',soc[name]]==pin_net['U701',pin],name
        assert pin_net['R208','2']==pin_net['U701','17']
        assert pin_net['U701','22']=='VCC_PG'
        assert pin_net['U701','9']=='VCC_WIFI'
        assert pin_net['U402','4']==pin_net['U402','16']=='+3V3'
        assert pin_net['U901','9']=='VCC_3V3'
        assert pin_net['U901','3']==pin_net['U7','5']=='+5V'
        assert pin_net['U901','1']==pin_net['L901','2']
        assert pin_net['L901','1']=='VSYS'
        assert pin_net['U7','6']==pin_net['D901','1']==pin_net['L902','1']
        assert pin_net['D901','2']=='GND'
        assert pin_net['L902','2']=='+3V3'
        assert len({pin_net['J8','A4'],pin_net['J101','A4'],pin_net['U901','3'],pin_net['BT1','1']})==4
        for c in xml.find('components'):
            ref=c.get('ref')
            assert c.findtext('value') not in {'A33','IP5306','AS4C512M16D3L'},ref
            if ref.startswith(('C','R','L')):
                assert (ref,'1') in pin_net and (ref,'2') in pin_net,ref
                assert pin_net[ref,'1']!=pin_net[ref,'2'],f'{ref} shorted by drawing'
        for ref,count in [('U201',522),('U301',200),('U501',53),('U502',21)]:
            assert sum(p[0]==ref for p in pin_net)==count,(ref,count)
        active=[]
        def visit(file):
            assert file.exists(),file
            assert file not in active,f'Duplicate sheet instance: {file}'
            active.append(file)
            tree=parse(file.read_text())
            for symbol in children(tree,'symbol'):
                assert not one(symbol,'lib_id')[1].startswith(('Allwinner_A33:','AS4C512M16D3L:','IP5306:'))
            for child in children(tree,'sheet'):
                visit(BASE/next(p[2] for p in children(child,'property') if p[1]=='Sheetfile'))
        visit(BASE/'blackpants.kicad_sch')
        assert len(active)==33
        for file in active:
            tree=parse(file.read_text());assert not children(tree,'global_label'),file.name
            if not (file.name.startswith('a523_') or file.name in ['hardware.kicad_sch','power.kicad_sch','peripheral_power.kicad_sch','sdcard.kicad_sch','wifi.kicad_sch','console.kicad_sch']):continue
            for wire in children(tree,'wire'):
                a,b=children(one(wire,'pts'),'xy')
                assert a[1]==b[1] or a[2]==b[2],(file.name,a,b)
        print('PASS: PMIC pin tables, 200 RAM pins, KiCad symbol round-trips and three footprint loads.')
        print('PASS: 796 IC pins; PMIC rails/bus/reset/sense, 44 DRAM data and 21 command signals, crystal networks, ground balls.')
        print('PASS: no shorted passives; generated circuits have orthogonal wires; no global labels in the active hierarchy.')
        print('PASS: active blackpants hierarchy, USB hub/mux/console/recovery, SD, DSI, Wi-Fi/BT, battery controls and peripheral supplies.')


if __name__=='__main__':main()
