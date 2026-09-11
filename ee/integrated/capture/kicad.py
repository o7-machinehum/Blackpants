"""Small schematic writer for the A523 capture; KiCad remains the file validator."""
import copy
import json
import math
import re
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = "d0a98fce-b133-4503-8f8a-83b2a1eed591"
HW = "8df227e7-e4f0-4624-83cb-7ffc2dd20696"
q = json.dumps


def is_supply(net):
    return bool(net) and not net.endswith('_FB') and (net=='GND' or net.startswith(('VCC','VDD','VBAT','VSYS','VBUS','+')))


class Atom(str):
    pass


def parse(text):
    stack = []
    root = None
    for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if t == '(':
            n = []
            if stack:
                stack[-1].append(n)
            else:
                assert root is None
                root = n
            stack.append(n)
        elif t == ')':
            stack.pop()
        else:
            stack[-1].append(json.loads(t) if t.startswith('"') else Atom(t))
    assert not stack
    return root


def children(n, key):
    return [x for x in n if isinstance(x,list) and x[0] == key]


def one(n, key):
    return children(n,key)[0]


def dump(n, depth=0):
    if isinstance(n,list):
        if all(not isinstance(x,list) for x in n):
            return '('+' '.join(dump(x) for x in n)+')'
        return '('+'\n'.join(('  '*(depth+1) if i and isinstance(x,list) else '')+dump(x,depth+1) for i,x in enumerate(n))+')'
    return str(n) if isinstance(n,Atom) else q(n)


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'blackpants-a523/'+name))


def effects(size=1.016, justify='', hide=False):
    return f'(effects (font (size {size} {size}))'+(f' (justify {justify})' if justify else '')+(' hide' if hide else '')+')'


LIBRARIES = {}


def library(libid):
    lib, name = libid.split(':')
    if lib not in LIBRARIES:
        path = {'A523':BASE/'A523/A523.kicad_sym', 'AXP':BASE/'AXP/AXP.kicad_sym',
                'LPDDR4':BASE/'LPDDR4/LPDDR4.kicad_sym'}.get(lib, Path('/usr/share/kicad/symbols')/(lib+'.kicad_sym'))
        if not path.exists():
            table = parse((BASE/'sym-lib-table').read_text())
            entry = next(e for e in children(table,'lib') if one(e,'name')[1] == lib)
            assert one(entry,'type')[1] == 'KiCad', lib
            path = Path(one(entry,'uri')[1].replace('${KIPRJMOD}',str(BASE)))
        LIBRARIES[lib] = {s[1]:s for s in children(parse(path.read_text()),'symbol')}
    original = LIBRARIES[lib][name]
    s = copy.deepcopy(original)
    ext = children(s,'extends')
    if ext:
        base = library(lib+':'+ext[0][1])
        oldname = base[1].split(':')[1]
        props = {p[1]:p for p in children(s,'property')}
        for i,p in enumerate(base):
            if isinstance(p,list) and p[0]=='property' and p[1] in props:
                base[i] = copy.deepcopy(props[p[1]])
        for u in children(base,'symbol'):
            u[1] = name+u[1][len(oldname):]
        s = base
    s[1] = libid
    return s


class Sheet:
    def __init__(self, filename, title, sheet_id=None, path=None, paper='A4'):
        self.filename, self.title = filename, title
        self.id = sheet_id or uid(filename)
        self.path = path or f'/{ROOT}/{HW}/{self.id}'
        self.paper = paper
        self.items, self.libs = [], {}
        self.refs, self.sequence = {}, 0

    def id_for(self, kind):
        self.sequence += 1
        return uid(f'{self.filename}/{kind}/{self.sequence}')

    def text(self, text, x, y, size=1.27):
        self.items.append(f'(text {q(text)} (at {x} {y} 0) {effects(size,"left top")} (uuid "{self.id_for("text")}"))')

    def wire(self, a, b):
        if a != b:
            self.items.append(f'(wire (pts (xy {a[0]:.4f} {a[1]:.4f}) (xy {b[0]:.4f} {b[1]:.4f})) (stroke (width 0) (type default)) (uuid "{self.id_for("wire")}"))')

    def junction(self, p):
        self.items.append(f'(junction (at {p[0]} {p[1]}) (diameter 0) (color 0 0 0 0) (uuid "{self.id_for("junction")}"))')

    def label(self, net, p, angle=0, global_=False):
        if net is None:
            self.items.append(f'(no_connect (at {p[0]} {p[1]}) (uuid "{self.id_for("nc")}"))')
            return
        kind = 'global_label' if global_ else 'label'
        extra = '(shape passive)' if global_ else ''
        self.items.append(f'({kind} {q(net)} (at {p[0]:.4f} {p[1]:.4f} {angle}) {extra} {effects(0.889,"left" if angle==0 else "right")} (uuid "{self.id_for("label")}"))')

    def port(self, net, p, side=-1, shape='bidirectional'):
        self.items.append(f'(hierarchical_label {q(net)} (at {p[0]} {p[1]} {180 if side<0 else 0}) (shape {shape}) {effects(1.016,"right" if side<0 else "left")} (uuid "{self.id_for("port")}"))')

    def power(self, net, p, side=0):
        libid='power:GND' if net=='GND' else 'A523Power:'+net
        if libid.startswith('A523Power:'):
            if 'A523Power' not in LIBRARIES: LIBRARIES['A523Power']={}
            if net not in LIBRARIES['A523Power']:
                LIBRARIES['A523Power'][net]=parse(f'''(symbol {q(net)} (power) (pin_names (offset 0) hide) (in_bom no) (on_board yes)
                  (property "Reference" "#PWR" (at 0 0 0) {effects(hide=True)})
                  (property "Value" {q(net)} (at 0 3.81 0) {effects()})
                  (symbol {q(net+"_0_1")} (polyline (pts (xy -1.27 1.27) (xy 0 2.54) (xy 1.27 1.27)) (stroke (width 0) (type default)) (fill (type none)))
                    (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none))))
                  (symbol {q(net+"_1_1")} (pin power_in line (at 0 0 90) (length 0) hide (name {q(net)} {effects()}) (number "1" {effects()}))))''')
        self.libs[libid]=library(libid)
        key=self.id_for('power')
        ref='#PWR'+str(uuid.UUID(key).int%1000000000)
        x,y=p
        angle=((90 if side>0 else 270) if net=='GND' else (270 if side>0 else 90)) if side else 0
        px,py=(x+side*(4.445+0.4*len(net)),y) if side and net!='GND' else (x,y+(3.81 if net=='GND' else -3.81))
        justify=''
        self.items.append(f'''(symbol (lib_id {q(libid)}) (at {x} {y} {angle}) (unit 1) (in_bom no) (on_board yes) (uuid "{key}")
          (property "Reference" "{ref}" (at {x} {y} 0) {effects(hide=True)})
          (property "Value" {q(net)} (at {px} {py} {angle}) {effects(1.016,justify,hide=net=='GND')})
          (pin "1" (uuid "{uid(key+'/pin')}"))
          (instances (project "blackpants" (path "{self.path}" (reference "{ref}") (unit 1)))))''')

    def connect_power(self, net, p, side=1, length=5.08):
        end=(p[0]+side*length,p[1])
        self.wire(p,end)
        self.power(net,end)

    def tag(self, net, p, side=1, length=5.08, local=False):
        if net == '__wired__':
            return
        if net is None:
            self.label(net,p)
            return
        if net.endswith('_FB'):length=max(length,20.32)
        end = (round(p[0]+side*length,4),p[1])
        self.wire(p,end)
        if is_supply(net):
            self.power(net,end)
        elif local:
            self.label(net,end,0 if side>0 else 180)
        else:
            self.port(net,end,side)

    def symbol(self, libid, ref, value, x, y, unit=1, angle=0, footprint=None, fields=None, dnp=False):
        lib = library(libid)
        self.libs[libid] = lib
        symid = uid(f'{self.filename}/{ref}/{unit}')
        items = [f'(symbol (lib_id {q(libid)}) (at {x} {y} {angle}) (unit {unit}) (in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"}) (uuid "{symid}")']
        props = {p[1]:p[2] for p in children(lib,'property')}
        props.update(Reference=ref, Value=value)
        if footprint is not None:
            props['Footprint'] = footprint
        props.update(fields or {})
        small = libid in ['Device:R_Small','Device:C_Small','Device:L_Small']
        top=5.08
        for sub in children(lib,'symbol'):
            if int(sub[1].rsplit('_',2)[1]) in [0,unit]:
                for box in children(sub,'rectangle'):
                    top=max(top,float(one(box,'start')[2]),float(one(box,'end')[2]))
        for name, val in props.items():
            hidden = name not in ['Reference','Value'] or (name=='Reference' and ref.startswith('#')) or (libid=='power:PWR_FLAG' and name=='Value')
            if small:
                px, py = (x+3.81,y+(-1.27 if name=='Reference' else 1.27)) if angle==0 else (x,y+(-3.81 if name=='Reference' else 3.81))
                justify='left' if angle==0 else ''
            else:
                px, py, justify = x, y-top-(5.08 if name=='Reference' else 2.54), ''
            items.append(f'(property {q(name)} {q(val)} (at {px} {py} {angle}) {effects(1.016,justify,hidden)})')
        pins = {}
        rad = math.radians(angle)
        for u in children(lib,'symbol'):
            if int(u[1].rsplit('_',2)[1]) not in [0,unit]:
                continue
            for p in children(u,'pin'):
                number = one(p,'number')[1]
                dx,dy = map(float,one(p,'at')[1:3])
                pins[number] = (round(x+dx*math.cos(rad)-dy*math.sin(rad),4), round(y-dy*math.cos(rad)-dx*math.sin(rad),4))
                items.append(f'(pin {q(number)} (uuid "{uid(symid+"/"+number)}"))')
        items.append(f'(instances (project "blackpants" (path "{self.path}" (reference {q(ref)}) (unit {unit}))))')
        items.append(')')
        self.items.append('\n'.join(items))
        self.refs[ref] = (libid,pins)
        return pins

    def passive(self, kind, ref, value, x, y, a, b='GND', horizontal=False, fields=None, footprint=None, dnp=False, local_nets=()):
        fp = footprint or {'R':'Resistor_SMD:R_0402_1005Metric','C':'Capacitor_SMD:C_0402_1005Metric','L':'Inductor_SMD:L_4.0x4.0_H2.0'}[kind]
        p = self.symbol('Device:'+kind+'_Small',ref,value,x,y,angle=90 if horizontal else 0,footprint=fp,fields=fields,dnp=dnp)
        if horizontal:
            self.tag(a,max(p.values()),1,local=a in local_nets)
            self.tag(b,min(p.values()),-1,local=b in local_nets)
        else:
            # Vertical passive: labels connect through a short horizontal stub.
            self.tag(a,p['1'],-1,local=a in local_nets)
            self.tag(b,p['2'],-1,local=b in local_nets)
        return p

    def ic(self, libid, ref, value, x, y, mapping, unit=1, local_nets=()):
        pins = self.symbol(libid,ref,value,x,y,unit)
        assert set(pins)==set(map(str,mapping)), (ref,unit,set(pins)^set(map(str,mapping)))
        # Common power pins form a physical bus at each edge of the symbol.
        for side in [-1,1]:
            entries=sorted([(n,p) for n,p in pins.items() if (p[0]<x)==(side<0)],key=lambda v:v[1][1])
            groups=[]
            previous_power=False
            for n,p in entries:
                net=mapping[int(n) if n.isdigit() else n]
                power=is_supply(net)
                if power and previous_power and groups and groups[-1][0]==net and p[1]-groups[-1][1][-1][1]<=5.081:
                    groups[-1][1].append(p)
                elif power:groups.append((net,[p]))
                else:self.tag(net,p,side,local=net in local_nets)
                previous_power=power
            for net,ps in groups:
                bx=ps[0][0]+side*5.08
                for p in ps:self.wire(p,(bx,p[1]))
                if len(ps)>1:
                    self.wire((bx,ps[0][1]),(bx,ps[-1][1]))
                    for p in ps[1:-1]:self.junction((bx,p[1]))
                self.power(net,(bx,ps[-1][1] if net=='GND' else ps[0][1]),side=side)
        return pins

    def child(self, filename, name, x, y, page, sheetid=None):
        sheetid = sheetid or uid(filename)
        self.items.append(f'''(sheet (at {x} {y}) (size 66.04 15.24) (fields_autoplaced yes)
          (stroke (width 0.254) (type solid)) (fill (color 0 0 0 0)) (uuid "{sheetid}")
          (property "Sheetname" {q(name)} (at {x} {y-1.27} 0) {effects(1.27,"left bottom")})
          (property "Sheetfile" {q(filename)} (at {x} {y+16.51} 0) {effects(1.016,"left top")})
          (instances (project "blackpants" (path "/{ROOT}/{HW}" (page "{page}")))))''')

    def save(self):
        content = [f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{self.id}") (paper "{self.paper}")',
                   f'(title_block (title {q(self.title)}) (rev "A523 capture"))',
                   '(lib_symbols\n'+'\n'.join(dump(s) for s in self.libs.values())+')',
                   *self.items, '(embedded_fonts no)', ')']
        text = '\n'.join(content)+'\n'
        parsed = parse(text)
        assert len(children(parsed,'symbol')) == sum(bool(re.match(r'\(symbol\s',x)) for x in self.items)
        (BASE/self.filename).write_text(text)
        if 'A523Power' in LIBRARIES:save_power_library()


def save_power_library():
    path=BASE/'A523Power.kicad_sym'
    if path.exists():
        existing={s[1]:s for s in children(parse(path.read_text()),'symbol')}
    else:existing={}
    existing.update(LIBRARIES.get('A523Power',{}))
    path.write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+'\n'.join(dump(existing[n]) for n in sorted(existing))+')\n')
