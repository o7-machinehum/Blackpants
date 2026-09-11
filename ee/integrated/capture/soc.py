#!/usr/bin/env python3
"""A523 load-side power, clocks and IO capture, based on STD sheets 9-12."""
import csv
import re
from kicad import Sheet, BASE
from power import cap, bank, raw_cap, shunt, signal

PINS=list(csv.DictReader((BASE/'A523/pinout.csv').open()))
RAM=list(csv.DictReader((BASE/'LPDDR4/pinout.csv').open()))


def soc(s,unit,x,y,nets,local_nets=()):
    ps=[p for p in PINS if p['unit']==chr(64+unit)]
    assert set(nets)<=set(p['name'] for p in ps),set(nets)-set(p['name'] for p in ps)
    return s.ic('A523:A523','U201','A523',x,y,{p['ball']:nets.get(p['name']) for p in ps},unit,local_nets)


def main():
    s=Sheet('a523_core.kicad_sch','A523 - core supplies and sense')
    s.text('A523 core power and remote sense',20.32,15.24,2.032)
    nets={'VCC-IO':'VCC_3V3','VDD-CPUS':'VDD_CPUS','VDD-CPUB':'VDD_CPUB','VDD-CPUL':'VDD_CPUL',
          'VDD-SYS':'VDD_SYS','VDD-GPU':'VDD_SYS','VDD-VE':'VDD_SYS','VDD-DE':'VDD_SYS','VDD-DNR':'VDD_DNR',
          'VDD-CPUBFB':'VDD_CPUB_FB','VDD-CPULFB':'VDD_CPUL_FB','VDD-SYSFB':'VDD_SYS_FB','VDD-DNRFB':'VDD_DNR_FB'}
    soc(s,11,83.82,38.1,nets)
    bank(s,201,'VDD_CPUS',['2.2uF','100nF'],162.56,40.64)
    bank(s,203,'VCC_3V3',['1uF','100nF'],162.56,66.04)
    bank(s,205,'VDD_SYS',['22uF','2.2uF','2.2uF'],162.56,91.44)
    bank(s,208,'VDD_SYS',['22uF','100nF'],162.56,116.84)
    s.text('At VE balls K10/L10',203.2,116.84)
    bank(s,210,'VDD_SYS',['2.2uF'],162.56,142.24)
    s.text('At DE balls K19/L18/L19',182.88,142.24)
    bank(s,211,'VDD_SYS',['2.2uF','2.2uF'],45.72,121.92)
    s.text('At GPU balls\nN8/N10/P9/P10',83.82,120.65)
    s.text('Sense pins are dedicated internal supply taps.\nRoute directly to PMIC feedback.\nCPU / DNR bypass is on the next page.',25.4,152.4)
    s.save()

    s=Sheet('a523_cpu_bypass.kicad_sch','A523 - CPU and DNR bypass capacitors')
    s.text('CPU / DNR decoupling: place at the SoC balls',20.32,15.24,2.032)
    for i,(net,vals) in enumerate([
        ('VDD_CPUB',['22uF','22uF','2.2uF','2.2uF','1uF','2.2uF','100nF']),
        ('VDD_CPUL',['22uF','22uF','2.2uF','2.2uF','1uF','2.2uF']),
        ('VDD_DNR',['22uF','2.2uF','2.2uF','2.2uF','2.2uF','100nF'])]):
        bank(s,220+i*10,net,vals,35.56,40.64+i*40.64)
    s.text('Populated capacitances follow Allwinner STD / hardware guide p39.\nKeep the individual capacitors at the corresponding ball clusters; bulk PMIC output capacitors are additional.\nUse X5R/X7R parts with adequate effective capacitance at the operating voltage.\nFeedback routing: M19 CPUB, V16 CPUL, L15 SYS, W10 DNR.',25.4,152.4)
    s.save()

    s=Sheet('a523_ground.kicad_sch','A523 - digital and analog ground balls')
    s.text('All A523 ground balls',20.32,15.24,2.032)
    for unit,x in [(12,76.2),(13,208.28),(14,76.2)]:
        p=s.symbol('A523:A523','U201','A523',x,40.64 if unit!=14 else 142.24,unit)
        for side in [-1,1]:
            ps=sorted([v for v in p.values() if (v[0]<x)==(side<0)],key=lambda v:v[1])
            bx=ps[0][0]+side*5.08
            for point in ps:
                s.wire(point,(bx,point[1]))
                s.junction((bx,point[1]))
            s.wire((bx,ps[0][1]),(bx,ps[-1][1]+5.08))
            s.tag('GND',(bx,ps[-1][1]+5.08),side)
    s.text('124 digital GND balls and 17 AVSS balls.\nAudio AGND is on the analog page.\nUse a continuous ground reference and nearby vias.\nKeep high-speed return paths continuous.',147.32,137.16)
    s.save()

    s=Sheet('a523_system.kicad_sch','A523 - clocks, reset and boot controls')
    s.text('System clocks / reset / FEL',20.32,15.24,2.032)
    soc(s,3,76.2,38.1,{'FEL':'FEL_N','VCC-EFUSE':'VCC_1V8','VCC-RTC':'VCC_RTC','VCC-DCXO':'VCC_AVCC',
        'VCC-PLL':'VCC_AVCC','RESET':'AP_RESET_N','NMI':'AP_NMI','WREQIN':'GND',
        'X32KFOUT':'CLK32K','X32KIN':'X32KIN','X32KOUT':'X32KOUT','DXIN':'DXIN','DXOUT':'DXOUT'},
        local_nets={'X32KIN','X32KOUT','DXIN','DXOUT'})
    p=s.symbol('Device:Crystal_GND24','Y201','24MHz / CL20pF / 20ppm',195.58,45.72,
               footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')
    s.wire(p['1'],(167.64,45.72));s.label('DXIN',(167.64,45.72),180)
    s.wire(p['3'],(220.98,45.72))
    for n in ['2','4']:
        gx=190.5 if n=='2' else 200.66
        s.wire(p[n],(gx,p[n][1]));s.wire((gx,p[n][1]),(gx,63.5));s.power('GND',(gx,63.5))
    rp=s.symbol('Device:R_Small','R201','0',236.22,45.72,angle=90,footprint='Resistor_SMD:R_0402_1005Metric')
    s.wire((220.98,45.72),min(rp.values()));s.tag('DXOUT',max(rp.values()),local=True)
    for ref,x in [('C250',172.72),('C251',220.98)]:
        cp=raw_cap(s,ref,'18pF',x,66.04)
        s.wire((x,45.72),cp['1']);s.junction((x,45.72))
        s.wire(cp['2'],(x,71.12));s.power('GND',(x,71.12))
    p=s.symbol('Device:Crystal','Y202','32.768kHz / CL12.5pF / 20ppm',195.58,111.76,
               footprint='Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm')
    rp=s.symbol('Device:R_Small','R202','10M',195.58,88.9,angle=90,footprint='Resistor_SMD:R_0402_1005Metric')
    for ref,x,net,yp,rpt in [('C252',172.72,'X32KIN',p['1'],min(rp.values())),('C253',220.98,'X32KOUT',p['2'],max(rp.values()))]:
        s.wire(yp,(x,111.76));s.label(net,(x,111.76),180 if x<195 else 0)
        s.wire(rpt,(x,88.9));s.wire((x,88.9),(x,111.76));s.junction((x,111.76))
        cp=raw_cap(s,ref,'22pF',x,129.54)
        s.wire((x,111.76),cp['1']);s.wire(cp['2'],(x,134.62));s.power('GND',(x,134.62))
    for i,(net,value) in enumerate([('VCC_1V8','100nF'),('VCC_RTC','100nF'),('VCC_AVCC','2.2uF'),('VCC_AVCC','100nF'),('AP_NMI','1nF'),('AP_RESET_N','1nF'),('FEL_N','1nF')]):
        cap(s,f'C{254+i}',value,net,30.48+(i%2)*58.42,99.06+(i//2)*20.32)
    s.text('TEST / JTAG-SEL / PLLTEST / REFCLK-OUT: unconnected.\nWREQIN grounded; no Allwinner Wi-Fi clock fanout.\nC258/C259: 1nF NMI / reset filters.\nTune crystal capacitors for CL and PCB stray capacitance.',20.32,177.8,1.016)
    s.save()

    s=Sheet('a523_gpio.kicad_sch','A523 - SD card, console and unused storage IO')
    s.text('Boot SD / UART0 console / GPIO',20.32,15.24,2.032)
    soc(s,4,83.82,40.64,{'PB9':'UART0_TX','PB10':'UART0_RX','PB4':'A523_I2C1_SCL','PB5':'A523_I2C1_SDA','PB11':'USB0_VBUS_DET',
        'PB7':'LCD_RST','PB8':'LCD_PWM','PB6':'LCD_TE','PF0':'SD0_D1','PF1':'SD0_D0','PF2':'SD0_CLK_SOC',
        'PF3':'SD0_CMD','PF4':'SD0_D3','PF5':'SD0_D2','PF6':'SD0_DET','VCC-PC':'VCC_3V3'},local_nets={'SD0_CLK_SOC'})
    cap(s,'C261','100nF','VCC_3V3',182.88,45.72)
    s.passive('R','R203','33',182.88,83.82,'SD0_CLK','SD0_CLK_SOC',True,local_nets={'SD0_CLK_SOC'})
    s.text('UART0: PB9 / PB10, mux 2.\nSDC0: PF0..PF5, mux 2; PF6 detect.\nLCD PWM: PB8 mux 6. Reset / TE: GPIO.\nPB11: divided USB0 VBUS detect.\nI2C1: expansion header with 3.3V pull-ups.',152.4,116.84)
    s.save()

    s=Sheet('a523_display_io.kicad_sch','A523 - DSI display IO')
    s.text('Two-lane DSI0 to the existing display connector',20.32,15.24,2.032)
    soc(s,5,83.82,40.64,{'PD0':'DSI_D0P','PD1':'DSI_D0N','PD2':'DSI_D1P','PD3':'DSI_D1N',
        'PD4':'DSI_CKP','PD5':'DSI_CKN','VCC-PD':'VCC_3V3','VCC-LVDS0':'VCC_1V8','VCC-PE':'VCC_PE'})
    bank(s,262,'VCC_3V3',['10uF','100nF'],172.72,45.72)
    cap(s,'C264','100nF','VCC_1V8',177.8,83.82)
    cap(s,'C265','100nF','VCC_PE',228.6,83.82)
    s.text('PD0..PD5: DSI0 mux 4. Clock = PD4/PD5.\nPD6..PD9 unused with the two-lane panel.\nFollow panel and A523 routing constraints.\nPE camera bank remains disabled.',152.4,116.84)
    s.save()

    s=Sheet('a523_wifi_io.kicad_sch','A523 - Wi-Fi, Bluetooth and DDR strap GPIO')
    s.text('SDIO1 / UART1 / DDR parameter straps',20.32,15.24,2.032)
    soc(s,6,83.82,40.64,{'PG0':'SD1_CLK_SOC','PG1':'SD1_CMD','PG2':'SD1_D0','PG3':'SD1_D1',
        'PG4':'SD1_D2','PG5':'SD1_D3','PG6':'BT_RXD','PG7':'BT_TXD','PG8':'BT_CTS_N','PG9':'BT_RTS_N',
        'VCC-PG':'VCC_PG','PH16':'DDR_ID0','PH17':'DDR_ID1',
        'PH0':'WL_REG_ON','PH1':'WL_HOST_WAKE','PH2':'BT_RESET_N','PH3':'BT_WAKE','PH4':'BT_HOST_WAKE'},local_nets={'SD1_CLK_SOC','DDR_ID0','DDR_ID1'})
    cap(s,'C266','100nF','VCC_PG',182.88,40.64)
    for i,net in enumerate(['DDR_ID0','DDR_ID1']):
        x=165.1+i*63.5
        lo=s.symbol('Device:R_Small',f'R{204+i}','1k',x,96.52,footprint='Resistor_SMD:R_0402_1005Metric')
        hi=s.symbol('Device:R_Small',f'R{206+i}','47k',x,68.58,footprint='Resistor_SMD:R_0402_1005Metric',dnp=True)
        s.wire(hi['2'],lo['1']);s.label(net,(x,83.82));s.junction((x,83.82))
        s.wire(hi['1'],(x,62.23));s.power('VCC_3V3',(x,62.23))
        s.wire(lo['2'],(x,102.87));s.power('GND',(x,102.87))
    s.passive('R','R208','33',182.88,129.54,'SD1_CLK','SD1_CLK_SOC',True,local_nets={'SD1_CLK_SOC'})
    s.text('SDIO and UART use PG mux 2. PG voltage must match the module VDD_IO.\nWi-Fi/BT control pins use PH (3.3V VCC_IO); the 1.8V PM bank is not used for these controls.\nPH16/PH17 = 0/0, GPADC1 selects DDR parameter set 1 (see analog page).\nFirmware must populate that parameter set for NT6AN512T32AV-J2.',20.32,160.02)
    s.save()

    s=Sheet('a523_always_on_io.kicad_sch','A523 - always-on IO and PMIC bus')
    s.text('PMIC control bus and standby IO',20.32,15.24,2.032)
    soc(s,7,83.82,40.64,{'PL0':'PMU_SCL','PL1':'PMU_SDA','VCC-PL':'VCC_PL',
        'VCC-PM':'VDD18_LPDDR','VCC-PK':'VCC_1V8','VCC-MCSI':'VCC_1V8'})
    for i,net in enumerate(['VCC_PL','VDD18_LPDDR','VCC_1V8','VCC_1V8']):cap(s,f'C{267+i}','100nF',net,177.8+(i%2)*50.8,50.8+(i//2)*35.56)
    s.text('PL0 / PL1: S-TWI0 mux 2, 3.3V.\nPMIC addresses: 0x34 and 0x36.\nMCSI must be supplied for SD voltage switching.\nPK: unused, supplied at 1.8V.\nPM: 1.8V standby; GPIOs unused.',152.4,127)
    s.save()

    s=Sheet('a523_usb.kicad_sch','A523 - USB PHY and unused PCIe / eDP')
    s.text('USB0 device/recovery / USB1 host',20.32,15.24,2.032)
    soc(s,8,76.2,40.64,{'USB0-DP':'USB0_DP','USB0-DM':'USB0_DM','USB1-DP':'USB_HOST_DP','USB1-DM':'USB_HOST_DM',
        'USB0-REXT':'USB0_REXT','USB1-REXT':'USB1_REXT','VDD09-USB':'VDD_CPUS',
        'VCC33-USB':'VCC_PL','VCC33-18-USB':'VCC_PL','PCIE-REF-CLKP':'GND','PCIE-REF-CLKN':'GND'},local_nets={'USB0_REXT','USB1_REXT'})
    # Entire unused PHY domains may float, per STD sheet 12 notes.
    soc(s,9,220.98,40.64,{})
    for i in range(2):s.passive('R',f'R{209+i}','200 / 1%',45.72+i*71.12,111.76,f'USB{i}_REXT',local_nets={f'USB{i}_REXT'})
    cap(s,'C271','100nF','VCC_PL',45.72,142.24)
    cap(s,'C272','100nF','VDD_CPUS',116.84,142.24)
    s.text('USB0/1 standby supplies: ALDO3 + CPUSLDO.\nUSB1 host is intended for USB2514B upstream.\nUnused USB2/3, PCIe and eDP domains float.\nPCIe reference-clock inputs grounded per STD.\nUSB 2.0: 90 ohm pairs; match within 50 mil.\n200-ohm REXT: 1%, beside the SoC.',20.32,165.1,1.016)
    s.save()

    s=Sheet('a523_analog.kicad_sch','A523 - analog rails and boot selection')
    s.text('Analog support / boot and DRAM ID straps',20.32,15.24,2.032)
    soc(s,10,83.82,40.64,{'AVCC':'VCC_AVCC','VDD33':'VCC_3V3','AGND':'GND','CPVIN':'VCC_1V8',
        'VRA1':'VRA1','VRA2':'VRA2','VRP':'VRP','VCM-ADC':'VCM_ADC','VREFP-ADC':'VCC_AVCC','VREFN-ADC':'GND',
        'GPADC0':'BOOT_ADC','GPADC1':'DDR_ADC','ALDO-OUT':'ALDO_OUT','CPVEE':'CPVEE','VEE':'CPVEE','CPVDD':'CPVDD'},
        local_nets={'BOOT_ADC','DDR_ADC','ALDO_OUT','CPVEE','CPVDD','VRA1','VRA2','VRP','VCM_ADC'})
    for i,(net,val) in enumerate([('VRA1','470nF'),('VRA2','470nF'),('VRP','470nF'),('VCM_ADC','470nF'),
                                 ('ALDO_OUT','2.2uF'),('CPVEE','2.2uF'),('CPVDD','2.2uF'),('VCC_AVCC','2.2uF'),('VCC_1V8','2.2uF')]):
        cap(s,f'C{273+i}',val,net,167.64+(i%3)*35.56,45.72+(i//3)*30.48)
    cap(s,'C282','10uF','VCC_1V8',167.64,137.16)
    cap(s,'C283','100nF','VCC_3V3',203.2,137.16)
    cap(s,'C284','2.2uF','VCC_AVCC',238.76,137.16)
    for i,(net,down) in enumerate([('BOOT_ADC','3.9k / 1%'),('DDR_ADC','2.7k / 1%')]):
        x=38.1+i*60.96
        hi=s.symbol('Device:R_Small',f'R{211+i*2}','10k / 1%',x,127,footprint='Resistor_SMD:R_0402_1005Metric')
        lo=s.symbol('Device:R_Small',f'R{212+i*2}',down,x,149.86,footprint='Resistor_SMD:R_0402_1005Metric')
        s.wire(hi['2'],lo['1']);s.label(net,(x,137.16));s.junction((x,137.16))
        s.wire(hi['1'],(x,120.65));s.power('VCC_AVCC',(x,120.65))
        s.wire(lo['2'],(x,156.21));s.power('GND',(x,156.21))
    s.text('BOOT_ADC: STD 10k / 3.9k, SD boot available.\nDDR_ADC: 0.383V; PH16/PH17 = 0/0 selects set 1.\nBuild set 1 for Nanya 16Gb LPDDR4.\nUnused audio / ADC IO is unconnected.\nKeep audio and headphone blocks disabled.',20.32,175.26,1.016)
    s.save()


if __name__=='__main__':main()
