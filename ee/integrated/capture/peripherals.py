#!/usr/bin/env python3
"""Product interfaces for the A523 replacement. Regenerates the named sheets."""
from kicad import Sheet, BASE, parse, children, one, dump
from power import cap, bank, raw_cap, shunt, signal, rail

RFP='Resistor_SMD:R_0402_1005Metric'
HEADER='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical'


def resistor(s,ref,value,x,y,horizontal=False):
    return s.symbol('Device:R_Small',ref,value,x,y,angle=90 if horizontal else 0,footprint=RFP)


def pull(s,ref,value,net,supply,x,y):
    p=resistor(s,ref,value,x,y)
    s.wire(p['1'],(x,y-5.08));s.power(supply,(x,y-5.08))
    s.wire(p['2'],(x,y+5.08));s.junction((x,y+5.08))


def usb_connector(s,ref,esd,x,y,recovery=False):
    """USB-C USB2 sink. DP/DM joined at the connector, then through ESD."""
    p=s.symbol('Connector:USB_C_Receptacle_USB2.0_16P',ref,'USB-C / recovery' if recovery else 'USB-C / charge + keyboard',x,y,
        footprint='Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal' if recovery else 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12')
    vbus='USB0_VBUS' if recovery else 'VBUS'
    rail(s,[p['A4']],vbus,x+22.86,up=7.62)
    s.power('GND',p['A1']);s.power('GND',p['SH'])
    for n in ['A8','B8']:s.label(None,p[n])
    for n in ['A6','A7']:
        b='B'+n[1:];bx=x+22.86
        s.wire(p[n],(bx,p[n][1]));s.wire(p[b],(bx,p[b][1]));s.wire((bx,p[n][1]),(bx,p[b][1]))
        s.junction((bx,p[n][1]))
    ep=s.symbol('Power_Protection:USBLC6-2SC6',esd,'USBLC6-2SC6',x+53.34,y-2.54)
    # ESD channel 1 = D-, channel 2 = D+.
    for n,ip in [('A7','1'),('A6','3')]:
        a=(x+22.86,p[n][1]);b=ep[ip]
        s.wire(a,(x+35.56,a[1]));s.wire((x+35.56,a[1]),(x+35.56,b[1]));s.wire((x+35.56,b[1]),b)
    s.power('GND',ep['2'])
    vp=(ep['5'][0]+12.7,ep['5'][1]);s.wire(ep['5'],vp);s.power(vbus,vp)
    signal(s,ep['6'],'USB0_DM' if recovery else 'MCU_USB_DM',1)
    signal(s,ep['4'],'USB0_DP' if recovery else 'MCU_USB_DP',1)
    # Local CC labels keep the protection and termination networks together below.
    for n,net in [('A5','CC1'),('B5','CC2')]:s.tag(net,p[n],1,local=True)
    cap(s,'C121' if recovery else 'C901','100nF',vbus,x+106.68,y-10.16)
    return p,vbus


def power_input():
    s=Sheet('power.kicad_sch','Battery, USB-C charging and keyboard USB',sheet_id='05158df8-c1e6-40b8-af8c-4aba99cbc568')
    p,vbus=usb_connector(s,'J8','U12',35.56,50.8)
    s.symbol('power:PWR_FLAG','#FLG901','PWR_FLAG',58.42,27.94)
    # USB cable is an external power source; no connection to the peripheral +5V.
    s.wire((58.42,27.94),(58.42,27.94))
    s.power('VBUS',(58.42,27.94))
    for i,net in enumerate(['CC1','CC2']):
        x=35.56+i*76.2;y=104.14
        r=resistor(s,f'R{901+i}','1k',x,y,True)
        s.tag(net,min(r.values()),-1,local=True);signal(s,max(r.values()),'PMIC_'+net,1)
    # Allwinner's battery design uses PMIC CC termination behind 1k series resistors.
    for i,(n,net) in enumerate([('A6','PMIC_USB_DP'),('A7','PMIC_USB_DM')]):
        x=35.56+i*76.2;y=137.16
        r=resistor(s,f'R{903+i}','470',x,y,True)
        s.label('SENSE_DP' if n=='A6' else 'SENSE_DM',(58.42,p[n][1]));s.junction((58.42,p[n][1]))
        s.tag('SENSE_DP' if n=='A6' else 'SENSE_DM',min(r.values()),-1,local=True);signal(s,max(r.values()),net,1)
    # Cell, fuse and remote temperature sensor.
    b=s.symbol('BH-18650-B1BA002:BH-18650-B1BA002','BT1','Protected 18650 / 1S Li-ion',233.68,48.26)
    f=s.symbol('Device:Polyfuse','F1','4A hold',233.68,30.48,footprint='Fuse:Fuse_1812_4532Metric')
    s.wire(b['1'],f['2']);s.tag('VBAT',f['1'],-1,17.78);s.power('GND',b['2'])
    s.symbol('power:PWR_FLAG','#FLG902','PWR_FLAG',233.68,26.67)
    s.symbol('power:PWR_FLAG','#FLG903','PWR_FLAG',246.38,55.88);s.power('GND',(246.38,55.88))
    t=s.symbol('Device:Thermistor_NTC','TH901','10k @25C / cell-attached NTC',233.68,104.14,
        footprint='Connector_Wire:SolderWire-0.5sqmm_1x02_P4.6mm_D0.9mm_OD2.1mm',fields={'Assembly':'Insulated NTC leads; bond bead to cell. Select curve and program TS thresholds together.'})
    signal(s,t['1'],'BAT_TS',-1);s.power('GND',t['2'])
    cap(s,'C902','10nF','BAT_TS',187.96,106.68)
    key=s.symbol('PTS847MM160LSMTR2_LFS:PTS847MM160LSMTR2_LFS','PWR_BUTTON1','Power',228.6,147.32)
    signal(s,key['1'],'PWRON',-1)
    for n in ['2','S1','S2']:s.power('GND',key[n])
    # Cable present indication to the 3.3V STM32, after the input protection.
    pull(s,'R905','100k','VBUS_PRESENT','VBUS',157.48,45.72)
    r=resistor(s,'R906','150k',157.48,66.04)
    s.wire(r['1'],(157.48,50.8));s.junction((157.48,50.8));signal(s,(157.48,50.8),'VBUS_PRESENT',1)
    s.power('GND',r['2'])
    led=s.symbol('Device:LED','D902','Charge status',162.56,142.24,angle=90,footprint='LED_SMD:LED_0603_1608Metric')
    r=resistor(s,'R907','2.2k',162.56,124.46)
    s.power('VSYS',r['1']);s.wire(r['2'],led['2']);signal(s,led['1'],'CHGLED_N',-1)
    s.text('AXP717C is the only battery charger. The IP5306 path has been removed.\nJ8 supplies VBUS only; peripheral +5V is a separate boost output.\nSet USB input/charge limits from the source capability and selected cell.\nTS: 50uA bias, 10k NTC; program temperature limits for the fitted curve.',25.4,170.18,1.016)
    s.save()


def peripheral_supplies():
    s=Sheet('peripheral_power.kicad_sch','Peripheral 5V boost and 3.3V regulator')
    p=s.symbol('Regulator_Switching:TPS61230DRC','U901','TPS61230DRCR',81.28,50.8,
        footprint='Package_SON:Texas_S-PVSON-N10')
    s.wire(p['10'],(45.72,45.72));s.power('VSYS',(45.72,45.72))
    cap(s,'C910','22uF','VSYS',30.48,48.26)
    l=s.symbol('Device:L_Small','L901','1uH / Isat >= 7A',81.28,25.4,angle=90,
        footprint='Inductor_SMD:L_Coilcraft_XAL4020-XXX',fields={'MPN':'XAL4020-102MEB'})
    s.wire(min(l.values()),(55.88,25.4));s.wire((55.88,25.4),(55.88,45.72));s.junction((55.88,45.72))
    s.wire(max(l.values()),(104.14,25.4));s.wire((104.14,25.4),(104.14,45.72));s.wire((104.14,45.72),p['1'])
    s.tag('VCC_3V3',p['9'],-1);s.label(None,p['8']);s.label(None,p['5']);s.power('GND',p['11'])
    c=raw_cap(s,'C911','10nF',53.34,76.2);s.wire(p['6'],(53.34,p['6'][1]));s.wire((53.34,p['6'][1]),c['1']);s.power('GND',c['2'])
    out=(121.92,p['3'][1]);s.wire(p['3'],out);s.power('+5V',out)
    rt=resistor(s,'R910','402k / 1%',121.92,58.42);rb=resistor(s,'R911','100k / 1%',121.92,81.28)
    s.wire(out,rt['1']);s.wire(rt['2'],rb['1']);s.wire(p['7'],(111.76,p['7'][1]));s.wire((111.76,p['7'][1]),(111.76,68.58));s.wire((111.76,68.58),(121.92,68.58));s.junction((121.92,68.58));s.power('GND',rb['2'])
    bank(s,912,'+5V',['22uF','22uF','22uF'],162.56,45.72)
    # Use the vendor's 0805, 10V output capacitors: effective capacitance >=20uF.
    for i in range(len(s.items)):
        if any(f'"C{n}"' in s.items[i] for n in [910,912,913,914]):
            s.items[i]=s.items[i].replace('Capacitor_SMD:C_0603_1608Metric','Capacitor_SMD:C_0805_2012Metric')
    s.text('5.02V nominal; load disconnect when disabled.\nEnabled by the main 3.3V SoC rail.\nBudget: USB-A 2 x 0.5A, logic/radio 0.4A equivalent,\nbacklights 0.2A: 1.6A total at 5V.\nDo not enable USB loads until the boost has started.',152.4,73.66,1.016)
    # Existing AOZ1280 function, corrected bootstrap capacitor and explicit feedback.
    p=s.symbol('Regulator_Switching:AOZ1280CI','U7','AOZ1280CI',81.28,137.16)
    s.tag('+5V',p['5'],-1);s.tag('+5V',p['4'],-1);s.power('GND',p['2'])
    cap(s,'C920','10uF','+5V',35.56,137.16)
    c=raw_cap(s,'C921','10nF',111.76,127)
    s.wire(p['1'],(101.6,p['1'][1]));s.wire((101.6,p['1'][1]),(101.6,c['1'][1]));s.wire((101.6,c['1'][1]),c['1'])
    s.wire(c['2'],(111.76,137.16));s.wire(p['6'],(124.46,137.16));s.junction((111.76,137.16))
    l=s.symbol('Device:L_Small','L902','2.2uH / Isat >= 2A',134.62,137.16,angle=90,footprint='Inductor_SMD:L_Coilcraft_XAL4020-XXX')
    s.wire((124.46,137.16),min(l.values()));s.wire(max(l.values()),(162.56,137.16));s.power('+3V3',(162.56,137.16))
    d=s.symbol('Device:D_Schottky','D901','MSS2P3',119.38,152.4,angle=270,footprint='Diode_SMD:D_MicroSMP_LargeCathode')
    s.wire(d['1'],(119.38,137.16));s.junction((119.38,137.16));s.power('GND',d['2'])
    rt=resistor(s,'R920','49.9k / 1%',162.56,147.32);rb=resistor(s,'R921','15.8k / 1%',162.56,172.72)
    s.wire((162.56,137.16),rt['1']);s.wire(rt['2'],rb['1']);s.power('GND',rb['2'])
    s.wire(p['3'],(101.6,p['3'][1]));s.wire((101.6,p['3'][1]),(101.6,160.02));s.wire((101.6,160.02),(162.56,160.02));s.junction((162.56,160.02))
    bank(s,922,'+3V3',['22uF','100nF'],200.66,147.32)
    s.text('3.33V nominal / 1.2A converter.\nSeparate from PMIC VCC_3V3.\nLogic/radio allocation: 0.6A.\nValidate startup and load steps.',193.04,110.49,1.016)
    s.save()


def card():
    s=Sheet('sdcard.kicad_sch','MicroSD boot socket')
    p=s.symbol('Connector:Micro_SD_Card_Det_Hirose_DM3AT','J105','microSD / boot',190.5,63.5,
        footprint='Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5')
    mapping={'1':'SD0_D2','2':'SD0_D3','3':'SD0_CMD','5':'SD0_CLK','7':'SD0_D0','8':'SD0_D1','9':'SD0_DET'}
    for n,net in mapping.items():signal(s,p[n],net,-1,43.18)
    for n in ['6','10','SH']:s.tag('GND',p[n],-1 if n!='SH' else 1)
    s.tag('VCC_3V3',p['4'],-1,20.32)
    bank(s,102,'VCC_3V3',['100nF','22uF'],218.44,48.26)
    for i,net in enumerate(['SD0_CMD','SD0_D0','SD0_D1','SD0_D2','SD0_D3','SD0_DET']):
        x=38.1+i*38.1;y=124.46
        pull(s,f'R{103+i}','10k' if i==0 else '100k',net,'VCC_3V3',x,y)
        signal(s,(x,y+5.08),net,1,7.62)
    s.text('PF0..PF5 SDC0, 3.3V removable card. PF6 detect is active low.\nClock series resistor R203 is at the SoC. No clock pull-up.\nC102/C103 at the socket. Configure card-detect pull-up before use.',25.4,162.56,1.016)
    s.save()


def wifi():
    s=Sheet('wifi.kicad_sch','RTL8723DS Wi-Fi and Bluetooth')
    mapping={n:None for n in range(1,45)}
    mapping.update({1:'GND',3:'GND',20:'GND',31:'GND',33:'GND',36:'GND',2:'RF_ANT',9:'VCC_WIFI',22:'VCC_PG',
        12:'WL_REG_ON',13:'WL_HOST_WAKE',14:'SD1_D2',15:'SD1_D3',16:'SD1_CMD',17:'SD1_CLK',18:'SD1_D0',19:'SD1_D1',
        41:'BT_RTS_N',42:'BT_TXD',43:'BT_RXD',44:'BT_CTS_N',6:'BT_WAKE',7:'BT_HOST_WAKE',34:'BT_RESET_N',24:'CLK32K'})
    p=s.ic('rtl8723ds:RTL8723DS','U701','RTL8723DS',96.52,73.66,mapping,local_nets={'RF_ANT'})
    # The legacy symbol has no library footprint property; retain the installed module.
    s.items=[v.replace('(property "Footprint" ""','(property "Footprint" "KiLib:RTL8723"') if '"U701"' in v else v for v in s.items]
    l=s.symbol('Device:L_Ferrite_Small','L701','120R @100MHz / >=0.6A',193.04,30.48,angle=90,footprint='Inductor_SMD:L_0603_1608Metric')
    s.tag('+3V3',min(l.values()),-1);s.tag('VCC_WIFI',max(l.values()),1)
    s.symbol('power:PWR_FLAG','#FLG904','PWR_FLAG',223.52,30.48);s.power('VCC_WIFI',(223.52,30.48))
    bank(s,703,'VCC_WIFI',['10uF','100nF'],177.8,55.88)
    cap(s,'C705','100nF','VCC_PG',238.76,55.88)
    for i,(net,val) in enumerate([('SD1_CMD','10k'),('SD1_D0','10k'),('SD1_D1','10k'),('SD1_D2','10k'),('SD1_D3','10k'),('CLK32K','10k')]):
        x=160.02+(i%3)*40.64;y=91.44+(i//3)*33.02
        pull(s,f'R{710+i}',val,net,'VCC_PG',x,y);signal(s,(x,y+5.08),net,1,5.08)
    for i,net in enumerate(['WL_REG_ON','BT_RESET_N','BT_WAKE']):
        s.passive('R',f'R{716+i}','100k',35.56+i*55.88,149.86,net)
    # Preserve the antenna connector and the original pi-matching provision.
    r=resistor(s,'R703','0',213.36,144.78,True)
    s.tag('RF_ANT',min(r.values()),-1,local=True)
    j=s.symbol('Connector:Conn_Coaxial','J701','Antenna',256.54,144.78,
        footprint='Connector_Coaxial:SMA_Amphenol_901-143_Horizontal')
    s.wire(max(r.values()),j['1']);s.power('GND',j['2'])
    for ref,x in [('C701',198.12),('C702',231.14)]:
        c=raw_cap(s,ref,'DNP',x,157.48,True);s.wire((x,144.78),c['1']);s.junction((x,144.78));s.power('GND',c['2'])
    # C701 attaches to the RF stub ahead of R703.
    s.wire((198.12,144.78),min(r.values()))
    s.text('Program BLDO1 = 3.3V before enabling PG / PH outputs.\nVBAT is filtered +3V3; VDD_IO is the separately sequenced VCC_PG.\nModule TX/RTS -> SoC RX/CTS; module RX/CTS <- SoC TX/RTS.\nX32KFOUT is open drain; R715 pulls it up to VCC_PG.',25.4,182.88,1.016)
    s.save()


def recovery_console():
    s=Sheet('console.kicad_sch','USB recovery, serial console and expansion')
    p,vbus=usb_connector(s,'J101','U101',35.56,50.8,True)
    s.symbol('power:PWR_FLAG','#FLG905','PWR_FLAG',58.42,27.94)
    for i,net in enumerate(['CC1','CC2']):s.passive('R',f'R{121+i}','5.1k',35.56+i*45.72,91.44,net,local_nets={net})
    pull(s,'R123','100k','USB0_VBUS_DET',vbus,157.48,38.1)
    r=resistor(s,'R124','150k',157.48,60.96)
    s.wire(r['1'],(157.48,43.18));signal(s,(157.48,43.18),'USB0_VBUS_DET',1);s.power('GND',r['2'])
    key=s.symbol('Switch:SW_Push','SW101','FEL / recovery',223.52,40.64,footprint='Button_Switch_SMD:SW_SPST_TL3342')
    signal(s,key['1'],'FEL_N',-1);s.tag('GND',key['2'],1)
    # UART bridge uses the fourth internal hub port, leaving both USB-A ports intact.
    p=s.symbol('Interface_USB:CH340C','U402','CH340C',83.82,139.7)
    inst=parse(s.items[-1])
    for prop in children(inst,'property'):
        if prop[1] in ['Reference','Value']:
            from kicad import Atom
            one(prop,'at')[1:3]=[Atom('104.14'),Atom('111.76' if prop[1]=='Reference' else '114.3')]
    s.items[-1]=dump(inst)
    rail(s,[p['4'],p['16']],'+3V3',78.74,up=7.62)
    s.junction(p['16'])  # VCC lies between V3 and the rail's horizontal endpoint.
    s.power('GND',p['1'])
    signal(s,p['5'],'HUB_CONSOLE_DP',-1);signal(s,p['6'],'HUB_CONSOLE_DM',-1)
    s.tag('GND',p['15'],-1)
    for n in ['7','8','9','10','11','12','13','14']:s.label(None,p[n])
    signal(s,p['3'],'UART0_TX',1,7.62)
    j=s.symbol('Jumper:SolderJumper_2_Bridged','JP101','Open for external UART RX',132.08,p['2'][1],
        footprint='Jumper:SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm')
    s.wire(p['2'],j['1']);signal(s,j['2'],'UART0_RX',1)
    cap(s,'C401','100nF','+3V3',40.64,149.86)
    j=s.symbol('Connector_Generic:Conn_01x03','J102','3.3V UART0: TX / RX / GND',228.6,104.14,footprint=HEADER)
    signal(s,j['1'],'UART0_TX',-1);signal(s,j['2'],'UART0_RX',-1);s.tag('GND',j['3'],-1)
    j=s.symbol('Connector_Generic:Conn_01x04','J103','I2C1: 3V3 / SCL / SDA / GND',228.6,149.86,
        footprint='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical')
    s.tag('VCC_3V3',j['1'],-1,40.64);signal(s,j['2'],'A523_I2C1_SCL',-1);signal(s,j['3'],'A523_I2C1_SDA',-1);s.tag('GND',j['4'],-1)
    for i,net in enumerate(['A523_I2C1_SCL','A523_I2C1_SDA']):
        x=187.96+i*50.8;y=124.46
        pull(s,f'R{125+i}','4.7k',net,'VCC_3V3',x,y);signal(s,(x,y+5.08),net,1,5.08)
    s.text('J101 is the A523 USB0 device / FEL connector; its VBUS is sense-only.\nJ8 remains charge + keyboard USB. The supplies do not join.\nJ102 provides console before the USB host starts. Open JP101 when\nan external adapter drives RX. CH340C V3 and VCC are tied for 3.3V.',25.4,172.72,1.016)
    s.save()


def main():
    power_input();peripheral_supplies();card();wifi();recovery_console()


if __name__=='__main__':main()
