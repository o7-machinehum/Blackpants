#!/usr/bin/env python3
"""Readable AXP717C/AXP323 capture from Allwinner STD sheet 7."""
from kicad import Sheet, BASE, uid, ROOT, HW, save_power_library, parse, children, one, effects, q, is_supply

IND='Inductor_SMD:L_Coilcraft_XAL4020-XXX'
PMIC_ID='1b72ccf8-21bd-4dc7-b102-09d524005a44'


def sheet(file,title):
    return Sheet(file,title,path=f'/{ROOT}/{HW}/{PMIC_ID}/{uid(file)}',paper='A4')


def raw_cap(s,ref,value,x,y,dnp=False):
    large=value in ['10uF','22uF']
    package='0603_1608' if large else '0402_1005'
    if ref.startswith('C2') and len(ref)==4:
        package='0201_0603' if value=='100nF' else '0402_1005'
    return s.symbol('Device:C_Small',ref,value,x,y,
        footprint=f'Capacitor_SMD:C_{package}Metric',
        fields={'Voltage':'10V','Dielectric':'C0G' if 'pF' in value else 'X5R/X7R'},dnp=dnp)


def cap(s,ref,value,net,x,y,dnp=False):
    p=raw_cap(s,ref,value,x,y,dnp)
    s.wire(p['1'],(x,y-5.08))
    if is_supply(net):s.power(net,(x,y-5.08))
    else:s.label(net,(x,y-5.08),0,global_=False)
    s.wire(p['2'],(x,y+3.81));s.power('GND',(x,y+3.81))
    return p


def bank(s,start,net,values,x,y):
    # A common supply and ground bus, with ordinary bypass spacing.
    top,bottom=y-5.08,y+5.08
    for i,value in enumerate(values):
        px=x+i*15.24
        p=raw_cap(s,f'C{start+i}',value,px,y)
        s.wire(p['1'],(px,top));s.wire(p['2'],(px,bottom))
        if i:
            s.wire((px-15.24,top),(px,top));s.wire((px-15.24,bottom),(px,bottom))
            if i<len(values)-1:s.junction((px,top));s.junction((px,bottom))
    s.power(net,(x,top));s.power('GND',(x,bottom))


def rail(s,points,net,x,up=5.08):
    ys=sorted({p[1] for p in points})
    for p in points:s.wire(p,(x,p[1]))
    if len(ys)>1:s.wire((x,ys[0]),(x,ys[-1]));s.junction((x,ys[0]))
    out=(x,ys[0]-up if net!='GND' else ys[-1]+abs(up))
    s.wire((x,ys[0] if net!='GND' else ys[-1]),out);s.power(net,out)


def signal(s,p,net,side=-1,length=10.16,shape='bidirectional'):
    end=(p[0]+side*length,p[1]);s.wire(p,end);s.port(net,end,side,shape)


def shunt(s,ref,value,node,x,dnp=False):
    # Capacitor hangs directly off the supplied node; no signal labels.
    y=node[1]
    s.wire(node,(x,y))
    p=raw_cap(s,ref,value,x,y+2.54,dnp)
    s.wire(p['2'],(x,y+6.35));s.power('GND',(x,y+6.35))
    return (x,y)


def resistor(s,ref,value,a,b,x,y,horizontal=False,dnp=False):
    p=s.symbol('Device:R_Small',ref,value,x,y,angle=90 if horizontal else 0,
               footprint='Resistor_SMD:R_0402_1005Metric',dnp=dnp)
    if a:s.wire(a,p['1'])
    if b:s.wire(b,p['2'])
    return p


def buck(s,p,vin,lx,fb,ref,cin,cout,net,y,x=76.2,second=None,fbnet=None):
    # VIN and LX are on the same row. Input decoupling and output loop stay local.
    rail(s,[p[str(vin)]],'VSYS',x-35.56)
    shunt(s,cin,'1uF' if ref in ['L501','L502','L503'] else '2.2uF',p[str(vin)],x-45.72)
    s.junction((x-35.56,p[str(vin)][1]))
    switch=(x+30.48,y)
    for n in lx:s.wire(p[str(n)],(switch[0],p[str(n)][1]))
    if len(lx)>1:s.wire(switch,(switch[0],p[str(lx[-1])][1]));s.junction(switch)
    lp=s.symbol('Device:L_Small',ref,'1uH',x+45.72,y,angle=90,footprint=IND,
        fields={'MPN':'XAL4020-102MEB','Rating':'Check peak/RMS current and DC bias at selected limit'})
    s.wire(switch,min(lp.values()))
    out=(x+63.5,y)
    s.wire(max(lp.values()),out);s.power(net,out)
    if ref!='L506':
        s.symbol('power:PWR_FLAG','#FLG'+ref[1:],'PWR_FLAG',out[0]+7.62,y)
        s.junction((out[0]+7.62,y))
    shunt(s,cout,'22uF' if ref in ['L501','L502','L503'] else '10uF',out,x+78.74)
    if second:shunt(s,second[0],second[1],(x+78.74,y),x+99.06,second[2]);s.junction((x+78.74,y))
    signal(s,p[str(fb)],fbnet,1,10.16,'input')


def main():
    s=sheet('a523_charger.kicad_sch','A523 - charger and PMIC control')
    p=s.symbol('AXP:AXP717C','U501','AXP717C',83.82,35.56,1)
    rail(s,[p['49'],p['50']],'VBUS',45.72)
    shunt(s,'C501','10uF',p['49'],30.48)
    rail(s,[p['41'],p['42']],'VBAT',45.72,up=2.54)
    shunt(s,'C506','4.7uF',p['41'],30.48)
    shunt(s,'C507','100nF',(30.48,p['41'][1]),15.24);s.junction((30.48,p['41'][1]))
    for n,net in [(2,'PMIC_USB_DM'),(3,'PMIC_USB_DP'),(4,'PMIC_CC1'),(5,'PMIC_CC2'),
                  (51,'PMU_SDA'),(52,'PMU_SCL'),(6,'PWRON'),(39,'BAT_TS')]:signal(s,p[str(n)],net)
    # VMID is distinct from VBUS in the battery configuration.
    rail(s,[p['47'],p['48']],'PMIC_VMID',121.92,up=12.7)
    shunt(s,'C502','22uF',(121.92,22.86),139.7)
    s.junction((121.92,22.86))
    sw=p['45'][1]
    s.wire(p['45'],(116.84,sw));s.wire(p['46'],(116.84,p['46'][1]));s.wire((116.84,sw),(116.84,p['46'][1]));s.junction((116.84,sw))
    lp=s.symbol('Device:L_Small','L504','1uH',132.08,sw,angle=90,footprint=IND,fields={'MPN':'XAL4020-102MEB'})
    s.wire((116.84,sw),min(lp.values()));s.wire(max(lp.values()),(162.56,sw));s.power('VSYS',(162.56,sw))
    s.wire(p['43'],(116.84,p['43'][1]));s.wire(p['44'],(116.84,p['44'][1]));s.wire((116.84,p['43'][1]),(116.84,p['44'][1]))
    s.wire((116.84,p['43'][1]),(152.4,p['43'][1]));s.wire((152.4,p['43'][1]),(152.4,sw));s.junction((152.4,sw));s.junction((116.84,p['43'][1]))
    for i,(ref,value) in enumerate([('C503','22uF'),('C504','22uF'),('C505','10uF')]):
        shunt(s,ref,value,(162.56+i*20.32,sw),182.88+i*20.32)
        if i<2:s.junction((182.88+i*20.32,sw))
    shunt(s,'C508','1uF',p['7'],127)
    shunt(s,'C509','1uF',p['35'],147.32)
    s.power('VCC_RTC',(147.32,p['35'][1]));s.junction((147.32,p['35'][1]))
    for n,net in [(1,'AP_RESET_N'),(37,'AP_NMI'),(38,'CHGLED_N')]:signal(s,p[str(n)],net,1)
    for n in ['36','40']:s.label(None,p[n])
    rail(s,[p['8'],p['53']],'GND',116.84)
    s.text('Single-cell Li-ion / 3.9-5.5V USB input\nA523 factory configuration required\nI2C: 0x34 (7-bit)',165.1,68.58,1.27)
    s.text('Do not bridge VMID to VBUS in the battery design.\nPlace the charger input/output capacitors at U501.',165.1,93.98,1.016)
    # Bus pull-ups are adjacent, on one shared rail, with signal ports below.
    for i,(ref,net,value,power) in enumerate([('R501','PMU_SCL','2.2k','VCC_PL'),('R502','PMU_SDA','2.2k','VCC_PL'),('R503','AP_NMI','10k','VCC_RTC'),('R504','AP_RESET_N','10k','VCC_RTC')]):
        x=35.56+i*43.18;y=137.16
        rp=resistor(s,ref,value,None,None,x,y,dnp=ref=='R504')
        s.wire(rp['1'],(x,y-6.35));s.power(power,(x,y-6.35))
        s.wire(rp['2'],(x,y+6.35));signal(s,(x,y+6.35),net,1,7.62)
    cap(s,'C510','100nF','PWRON',228.6,137.16)
    s.text('R504 is not fitted: retain the reference reset pull-up option.\nDP/DM sense resistors (470 ohm) belong at the USB interface.\nBAT_TS connects to the battery NTC; PWRON to the power key.',25.4,165.1,1.016)
    s.save()

    s=sheet('a523_bucks.kicad_sch','A523 - main buck regulators')
    p=s.symbol('AXP:AXP717C','U501','AXP717C',76.2,30.48,2)
    buck(s,p,9,[10,11],12,'L501','C511','C514','VDD_CPUL',p['10'][1],fbnet='VDD_CPUL_FB')
    buck(s,p,32,[33],34,'L502','C512','C515','VDD_SYS',p['33'][1],second=('C517','4.7uF',False),fbnet='VDD_SYS_FB')
    buck(s,p,31,[30],29,'L503','C513','C516','VCC_DRAM',p['30'][1],fbnet='VCC_DRAM_FB')
    s.text('0.9V default / DVFS\n4A converter',190.5,27.94)
    s.text('0.9V\n3A converter',190.5,58.42)
    s.text('1.1V / LPDDR4\n1.5A converter',190.5,88.9)
    s.text('Remote feedback',25.4,125.73,1.524)
    s.text('FB1 -> SoC VDD-CPULFB (V16)\nFB2 -> SoC VDD-SYSFB (L15)\nFB3 -> VCC_DRAM at the load, through NT301',25.4,133.35)
    s.text('FB3 also supplies CPUSLDO: allow at least 30mA.\nDo not pick up feedback at the inductor output.\nKeep each VIN bypass capacitor close to its pin.\nInductors: 1uH, DCR < 100mOhm; check saturation margin.',152.4,125.73)
    s.save()

    s=sheet('a523_ldos.kicad_sch','A523 - LDO and standby rails')
    p=s.symbol('AXP:AXP717C','U501','AXP717C',76.2,25.4,3)
    for i,n in enumerate([15,20,25]):
        rail(s,[p[str(n)]],'VSYS',40.64)
        shunt(s,f'C{520+i}','1uF',p[str(n)],30.48)
        s.junction((40.64,p[str(n)][1]))
    outs=[(13,'ALDO1_UNUSED','off'),(14,'VCC_PE','camera IO / off'),(16,'VCC_PL','3.3V / standby USB + PL'),
          (17,'VCC_AVCC','1.8V / analog + PLL + DCXO'),(18,'VCC_PG','Wi-Fi IO / off'),(19,'VDD18_LPDDR','1.8V / LPDDR VDD1 + PM + AXP323 EN'),
          (21,'BLDO3_UNUSED','off'),(22,'BLDO4_UNUSED','off'),(23,'VCC_1V8','1.8V / eFuse + MCSI + MIPI'),
          (24,'CLDO2_UNUSED','off'),(26,'VCC_3V3','3.3V / IO + SD'),(27,'VCC_LCD','LCD / off'),(28,'VDD_CPUS','0.9V / standby CPU + USB')]
    for i,(n,net,note) in enumerate(outs):
        y=p[str(n)][1]
        # One short rail, one capacitor, one ground. No disconnected bypass islands.
        node=shunt(s,f'C{523+i}','2.2uF',p[str(n)],129.54)
        s.wire(node,(154.94,y));s.power(net,(154.94,y));s.junction(node)
        s.text(note,182.88,y-1.27,1.016)
    s.text('Keep equal-voltage rails separate: they have different startup / sleep behavior.\nUnloaded LDO inputs remain connected. Leave unused outputs disabled in firmware.',25.4,173.99,1.016)
    s.save()

    s=sheet('a523_axp323.kicad_sch','A523 - CPU big and DNR supply')
    p=s.symbol('AXP:AXP323','U502','AXP323',76.2,25.4)
    buck(s,p,17,[18],16,'L505','C540','C543','VDD_CPUB',p['18'][1],fbnet='VDD_CPUB_FB')
    buck(s,p,20,[19],1,'L506','C541','C544','VDD_CPUB',p['19'][1],fbnet='VDD_CPUB_FB')
    buck(s,p,2,[3],4,'L507','C542','C545','VDD_DNR',p['3'][1],fbnet='VDD_DNR_FB')
    # Wire the two converter outputs in parallel after their separate inductors.
    outx=76.2+104.14
    s.wire((154.94,p['18'][1]),(outx,p['18'][1]));s.wire((154.94,p['19'][1]),(outx,p['19'][1]))
    s.wire((outx,p['18'][1]),(outx,p['19'][1]))
    s.junction((154.94,p['18'][1]));s.junction((154.94,p['19'][1]))
    s.text('DCDC1 + DCDC2\nFactory parallel mode\n0.9V default / DVFS',195.58,27.94)
    s.text('DCDC3: 0.9V',195.58,86.36)
    rail(s,[p['14']],'VDD18_LPDDR',40.64)
    signal(s,p['13'],'AP_RESET_N',-1,10.16)
    signal(s,p['5'],'PMU_SDA');signal(s,p['6'],'PMU_SCL')
    for n in ['10','11']:s.label(None,p[n])
    rail(s,[p['9'],p['21']],'GND',40.64,up=2.54)
    for i,n in enumerate([15,12,7,8]):
        shunt(s,f'C{549+i}','1uF' if n==8 else '2.2uF',p[str(n)],129.54)
    s.text('I2C: 0x36 (7-bit)\nPWRON factory mode: EN\nPWROK joins the reset net.\nIRQ and spare LDO loads unused.',177.8,109.22,1.016)
    s.text('Both CPU feedback inputs return from A523 M19. DNR feedback returns from W10.\nUse matched L505/L506. Place C540 directly at VIN1.\nBLDO2 enables AXP323; AXP717C DCDCEN is unused in this reference configuration.',25.4,165.1,1.016)
    s.save()
    save_power_library()
    overview()


def overview():
    s=Sheet('a523_power.kicad_sch','A523 - power management',sheet_id=PMIC_ID,path=f'/{ROOT}/{HW}/{PMIC_ID}',paper='A4')
    definitions=[('a523_charger.kicad_sch','Charger / control',55.88,25.4),
                 ('a523_bucks.kicad_sch','Main buck rails',187.96,25.4),
                 ('a523_ldos.kicad_sch','LDO rails',55.88,96.52),
                 ('a523_axp323.kicad_sch','CPU big / DNR',187.96,96.52)]
    ports=set()
    for i,(file,title,x,y) in enumerate(definitions):
        parsed=parse((BASE/file).read_text())
        names=list(dict.fromkeys(p[1] for p in children(parsed,'hierarchical_label')))
        ports.update(names)
        h=max(15.24,5.08+2.54*len(names))
        pid=uid(file)
        fragment=[f'(sheet (at {x} {y}) (size 66.04 {h}) (stroke (width 0.254) (type solid)) (fill (color 0 0 0 0)) (uuid "{pid}")',
          f'(property "Sheetname" {q(title)} (at {x} {y-1.27} 0) {effects(1.27,"left bottom")})',
          f'(property "Sheetfile" {q(file)} (at {x} {y+h+1.27} 0) {effects(1.016,"left top")})']
        for j,n in enumerate(names):
            py=y+2.54*(j+1)
            fragment.append(f'(pin {q(n)} bidirectional (at {x} {py} 180) {effects(1.016,"left")} (uuid "{uid(file+"/port/"+n)}"))')
            s.wire((x,py),(x-7.62,py));s.label(n,(x-7.62,py),180,global_=False)
        fragment.append(f'(instances (project "blackpants" (path "/{ROOT}/{HW}/{PMIC_ID}" (page "{14+i}")))))')
        s.items.append('\n'.join(fragment))
    s.text('AXP717C + AXP323 / Allwinner STD V2.4\nA523 factory configuration: voltages, sequence and parallel mode.',25.4,142.24,1.016)
    # External signal interface, compact rows on the left side of the overview.
    for i,n in enumerate(sorted(ports)):
        x=40.64+(i%2)*76.2;y=157.48+(i//2)*5.08
        s.port(n,(x,y),-1)
        s.wire((x,y),(x+12.7,y));s.label(n,(x+12.7,y),0,global_=False)
    s.save()


if __name__=='__main__':main()
