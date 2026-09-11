#!/usr/bin/env python3
"""Wire the dual-channel 16Gb LPDDR4 to A523 (STD DRAM mux table)."""
import json
import re
from kicad import BASE, Sheet
from soc import PINS, RAM, soc
from power import cap, bank

PART='NT6AN512T32AV-J2'
SOC_TO_RAM_DQ=json.loads((BASE/'LPDDR4/a523-swizzle.json').read_text())['soc_to_ram_dq']
assert sorted(SOC_TO_RAM_DQ)==list(range(32))
assert all(soc//8==ram//8 for soc,ram in enumerate(SOC_TO_RAM_DQ))
RAM_TO_SOC_DQ={ram:soc for soc,ram in enumerate(SOC_TO_RAM_DQ)}


def dram_net(name):
    if name in ['NC','DNU']:return None
    if name in ['VDD2','VDDQ']:return 'VCC_DRAM'
    if name=='VDD1':return 'VDD18_LPDDR'
    if name=='VSS':return 'GND'
    if name=='ZQ':return 'DDR_ZQ'
    if name=='RESET_N':return 'DDR_RESET_N'
    ch=0 if name.endswith('_a') else 1
    stem=name[:-2]
    if re.fullmatch(r'DQ\d+',stem):return 'DDR_DQ'+str(RAM_TO_SOC_DQ[int(stem[2:])+16*ch])
    if stem.startswith('DMI'):return 'DDR_DM'+str(int(stem[3:])+2*ch)
    if stem.startswith('DQS_'):return 'DDR_DQS'+str(int(stem[-1])+2*ch)+stem[-2]
    if stem.startswith('CA'):return f'DDR_CA{ch}_{stem[2:]}'
    if stem in ['CK_P','CK_N']:return f'DDR_CK{ch}_{stem[-1]}'
    if stem=='CKE':return f'DDR_CKE{ch}'
    if stem=='CS':return f'DDR_CS{ch}'
    if stem=='ODT_CA':return 'VCC_DRAM'
    raise ValueError(name)


def data_sheet():
    s=Sheet('a523_dram_data.kicad_sch','A523 - LPDDR4 data and channel pins')
    s.text('2 GB LPDDR4 / 2 x 16-bit channels / single rank per channel',20.32,15.24,2.032)
    names={p['name'] for p in PINS if p['unit']=='A'}
    nets={n: ('DDR_DQ'+n[3:] if re.fullmatch(r'SDQ\d+',n) else
              'DDR_DM'+n[4:] if n.startswith('SDQM') else 'DDR_DQS'+n[4:]) for n in names}
    sp=s.symbol('A523:A523','U201','A523',147.32,45.72,1)
    soc_nodes={nets[p['name']]:sp[p['ball']] for p in PINS if p['unit']=='A'}
    for unit,x in [(1,48.26),(2,246.38)]:
        ps=[p for p in RAM if int(p['unit'])==unit]
        rp=s.symbol('LPDDR4:'+PART,'U301',PART,x,43.18,unit)
        for p in ps:
            net=dram_net(p['name']);a=rp[p['ball']];b=soc_nodes[net]
            assert a[1]==b[1],(net,a,b)
            s.wire(a,b);s.label(net,((a[0]+b[0])/2,a[1]))
    s.text('Channel A: DQ[0..15], DQS/DM[0..1]\nChannel B: DQ[16..31], DQS/DM[2..3]\nOne rank per channel. Command and power on following pages.',25.4,119.38)
    s.text('Vendor-qualified clock target: 1200MHz.\nUse NT6AN512T32AV-J2 parameters in the DRAM firmware.\nFinal clock and timings require board validation.',25.4,147.32)
    s.text('DQ bit swaps follow Allwinner S6L V2.0 (C0402).\nDDR_DQ labels identify SoC bits; RAM pin names show the swizzle.\nSwaps stay within each byte. DQS and DMI assignments are unchanged.',25.4,165.1,1.016)
    s.save()


def main():
    data_sheet()
    s=Sheet('a523_dram_control.kicad_sch','A523 - LPDDR4 command mux and SoC DRAM power')
    s.text('A523 LPDDR4 command mapping / load-side feedback',20.32,15.24,2.032)
    nets={'SA1':'DDR_CA0_2','SA2':'DDR_CA0_0','SA4':'DDR_CA1_1','SA6':'DDR_CKE1','SA8':'DDR_CA1_2',
          'SA9':'DDR_CA0_5','SA10':'DDR_CA0_3','SA11':'DDR_CA0_1','SA13':'DDR_CS1',
          'SA14':'DDR_CK1_P','SA15':'DDR_CK1_N','SA16':'DDR_CA1_4','SA17':'DDR_CA0_4',
          'SBA0':'DDR_CA1_3','SBA1':'DDR_CA1_0','SACT':'DDR_CA1_5','SCS0':'DDR_CS0',
          'SCKP':'DDR_CK0_P','SCKN':'DDR_CK0_N','SCKE0':'DDR_CKE0','SRST':'DDR_RESET_N',
          'SZQ':'SOC_DDR_ZQ','VCC-DRAM':'VCC_DRAM','VCC-DRAML':'VCC_DRAM','VDD18-DRAM':'VCC_AVCC'}
    soc(s,2,76.2,40.64,nets,local_nets=set(nets.values()))
    ps=[p for p in RAM if int(p['unit'])==3]
    mapping={p['ball']:dram_net(p['name']) for p in ps}
    s.ic('LPDDR4:'+PART,'U301',PART,213.36,40.64,mapping,3,local_nets=set(mapping.values()))
    s.passive('R','R301','120 / 1%',33.02,116.84,'SOC_DDR_ZQ',local_nets={'SOC_DDR_ZQ'})
    s.passive('R','R302','240 / 1%',96.52,116.84,'VCC_DRAM','DDR_ZQ',local_nets={'DDR_ZQ'})
    p=s.symbol('Device:NetTie_2','NT301','DRAM sense',213.36,96.52,
               footprint='NetTie:NetTie-2_SMD_Pad0.5mm')
    s.tag('VCC_DRAM',p['1'],-1);s.tag('VCC_DRAM_FB',p['2'])
    sense=(p['2'][0]+10.16,p['2'][1])
    p=s.symbol('power:PWR_FLAG','#FLG301','PWR_FLAG',sense[0],104.14)
    s.wire(p['1'],sense);s.junction(sense)
    bank(s,301,'VCC_DRAM',['2.2uF','2.2uF','2.2uF','2.2uF'],160.02,124.46)
    bank(s,305,'VCC_DRAM',['2.2uF','2.2uF','2.2uF','2.2uF'],160.02,149.86)
    cap(s,'C309','100nF','VCC_AVCC',33.02,144.78)
    s.text('NT301: load-side sense to U501 FB3; allow >= 30mA.\nVCC_DRAM and VCC_DRAML both use 1.1V for LPDDR4.\nC301..C308 belong at the SoC DRAM ball clusters.\nUnused DDR3 command functions are unconnected.',20.32,170.18,1.016)
    s.save()

    s=Sheet('a523_dram_power.kicad_sch','A523 - Nanya LPDDR4 power and ground')
    s.text('Nanya LPDDR4 supply balls and bypass',20.32,15.24,2.032)
    for unit,x,y in [(4,76.2,40.64),(5,220.98,40.64),(6,76.2,137.16)]:
        ps=[p for p in RAM if int(p['unit'])==unit]
        s.ic('LPDDR4:'+PART,'U301',PART,x,y,{p['ball']:dram_net(p['name']) for p in ps},unit)
    bank(s,310,'VCC_DRAM',['10uF','2.2uF','2.2uF','2.2uF','2.2uF','2.2uF','2.2uF'],152.4,121.92)
    bank(s,317,'VDD18_LPDDR',['2.2uF','100nF'],167.64,149.86)
    s.text('VDD1 = 1.8V BLDO2. VDD2 = VDDQ = 1.1V DCDC3.\nDNU pads: no tracks or vias.\nPlace the capacitors beside the DRAM package.\nFollow Allwinner DDR constraints and the selected stack-up.',20.32,175.26,1.016)
    s.save()


if __name__=='__main__':main()
