#!/usr/bin/env python3
"""Assemble A523 sheets inside the actual blackpants project."""
from collections import Counter
from kicad import Sheet, BASE, uid, parse, children, one, effects, q, dump, Atom


def ports(file):
    return list(dict.fromkeys(p[1] for p in children(parse((BASE/file).read_text()),'hierarchical_label')))


def overview(file,title,definitions,paper,port_positions,sheet_id=None):
    s=Sheet(file,title,paper=paper,sheet_id=sheet_id)
    counts=Counter(n for f,_,_,_ in definitions for n in ports(f))
    external=sorted(n for n,count in counts.items() if count==1)
    for f,name,x,y in definitions:
        names=ports(f);h=max(12.7,5.08+2.54*len(names))
        fragment=[f'(sheet (at {x} {y}) (size 71.12 {h}) (stroke (width 0.254) (type solid)) (fill (color 0 0 0 0)) (uuid "{uid(f)}")',
            f'(property "Sheetname" {q(name)} (at {x} {y-1.27} 0) {effects(1.27,"left bottom")})',
            f'(property "Sheetfile" {q(f)} (at {x} {y+h+1.27} 0) {effects(1.016,"left top")})']
        for i,n in enumerate(names):
            py=y+2.54*(i+1)
            fragment.append(f'(pin {q(n)} bidirectional (at {x} {py} 180) {effects(1.016,"left")} (uuid "{uid(file+f+n)}"))')
            s.wire((x,py),(x-7.62,py));s.label(n,(x-7.62,py),180)
        fragment.append(')');s.items.append('\n'.join(fragment))
    for i,n in enumerate(external):
        x,y=port_positions(i)
        s.port(n,(x,y),-1)
        s.wire((x,y),(x+10.16,y));s.label(n,(x+10.16,y))
    s.save()


def main():
    overview('a523_soc.kicad_sch','A523 - SoC support',[
        ('a523_core.kicad_sch','Core supplies',55.88,25.4),
        ('a523_system.kicad_sch','Clocks / reset / boot',187.96,25.4),
        ('a523_cpu_bypass.kicad_sch','CPU bypass',55.88,76.2),
        ('a523_ground.kicad_sch','Ground balls',187.96,76.2),
        ('a523_analog.kicad_sch','Analog / straps',55.88,114.3)],'A4',
        lambda i:(40.64+(i%2)*76.2,152.4+(i//2)*5.08))
    overview('a523_memory.kicad_sch','A523 - 2GB LPDDR4',[
        ('a523_dram_data.kicad_sch','Data channels',55.88,25.4),
        ('a523_dram_control.kicad_sch','Command / DRAM supply',187.96,25.4),
        ('a523_dram_power.kicad_sch','DRAM power / ground',55.88,76.2)],'A4',
        lambda i:(55.88,119.38+i*5.08))
    overview('a523_interfaces.kicad_sch','A523 - peripheral IO assignments',[
        ('a523_gpio.kicad_sch','SD / console / GPIO',55.88,25.4),
        ('a523_wifi_io.kicad_sch','Wi-Fi / Bluetooth',190.5,25.4),
        ('a523_display_io.kicad_sch','Display DSI',55.88,111.76),
        ('a523_usb.kicad_sch','USB PHY',190.5,111.76),
        ('a523_always_on_io.kicad_sch','PMIC bus / standby IO',55.88,185.42)],'A3',
        lambda i:(325.12,25.4+i*3.81))
    overview('a523_peripherals.kicad_sch','A523 - product peripherals',[
        ('sdcard.kicad_sch','MicroSD boot',55.88,25.4),
        ('wifi.kicad_sch','Wi-Fi / Bluetooth',190.5,25.4),
        ('dsi.kicad_sch','Display / backlight',55.88,78.74),
        ('console.kicad_sch','Recovery / UART / I2C',190.5,96.52),
        ('peripheral_power.kicad_sch','5V / 3.3V peripherals',55.88,134.62)],'A3',
        lambda i:(325.12,25.4+i*3.81))
    overview('hardware.kicad_sch','A523 system',[
        ('a523_power.kicad_sch','AXP717C + AXP323',63.5,25.4),
        ('a523_soc.kicad_sch','SoC support',63.5,96.52),
        ('a523_memory.kicad_sch','2GB LPDDR4',63.5,139.7),
        ('a523_interfaces.kicad_sch','Peripheral IO',205.74,25.4),
        ('a523_peripherals.kicad_sch','Product peripherals',335.28,25.4)],'A3',
        lambda i:(60.96+(i%3)*127,190.5+(i//3)*5.08),
        sheet_id='8df227e7-e4f0-4624-83cb-7ffc2dd20696')
    rebase_project()


def rebase_project():
    root=BASE/'blackpants.kicad_sch'
    rootid=one(parse(root.read_text()),'uuid')[1]
    page=0
    def rebase(file,parent_path=None):
        nonlocal page
        if file.name in {'keyboard.kicad_sch','dsi_bridge.kicad_sch'}:
            page+=1
            return  # Original instance paths are unchanged; preserve user edits verbatim.
        tree=parse(file.read_text());sid=one(tree,'uuid')[1]
        path=parent_path or '/'+sid
        page+=1
        tree[:]=[n for n in tree if not isinstance(n,list) or n[0]!='sheet_instances']
        if file==root:
            tree.append(parse('(sheet_instances (path "/" (page "1")))'))
        for symbol in children(tree,'symbol'):
            props={p[1]:p[2] for p in children(symbol,'property')}
            unit=one(symbol,'unit')[1]
            symbol[:]=[n for n in symbol if not isinstance(n,list) or n[0]!='instances']
            symbol.append(parse(f'(instances (project "blackpants" (path {q(path)} (reference {q(props["Reference"])}) (unit {unit}))))'))
        for child in children(tree,'sheet'):
            childid=one(child,'uuid')[1]
            childfile=next(p[2] for p in children(child,'property') if p[1]=='Sheetfile')
            child[:]=[n for n in child if not isinstance(n,list) or n[0]!='instances']
            child.append(parse(f'(instances (project "blackpants" (path {q(path)} (page "{page+1}"))))'))
            rebase(BASE/childfile,path+'/'+childid)
        file.write_text(dump(tree)+'\n')
    rebase(root)
    print(f'Assembled {page} sheets in blackpants.kicad_sch')


if __name__=='__main__':main()
