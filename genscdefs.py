# Generate SimConnect_cpp.h via:
#
#   touch float.h
#   cpp -nostdinc -I. -CC SimConnect.h > SimConnect_cpp.h
#
import re
from typing import List


def nopfx(s: str, pfx='SIMCONNECT_') -> str:
    return s.replace(pfx, '')


# typedef DWORD SIMCONNECT_WAYPOINT_FLAGS;
def maybeTypedef(line, lines, output) -> bool:
    m = re.match(r'typedef\s+(\w+)\s+(\w+)\s*;(.*)', line)
    if not m:
        return False

    typ, aka, suffix = m.groups()
    aka = nopfx(aka)
    output.append(f"{aka} = {typ} {suffix}")
    return True


# static const DWORD SIMCONNECT_GROUP_PRIORITY_HIGHEST = 1; // highest priority
def maybeConst(line, lines, output, indent='') -> bool:
    m = re.match(r'\s*static\s+const\s+(\w+)\s+(\w+)\s*=\s*(\S+);(.*)', line)
    if not m:
        return False

    typ, var, val, suffix = m.groups()
    var = nopfx(var)
    val = nopfx(val)
    if typ in ('DWORD'):
        val = f"{typ}({val})"
    line = f"{var}: {typ} = {val} {suffix}"
    output.append(indent + line)
    return True


# enum SIMCONNECT_RECV_ID {
def maybeEnum(line, lines, output) -> bool:
    m = re.match(r'\s*enum\s+(\w+)\s*{(.*)', line)
    if not m:
        return False

    enum, suffix = m.groups()
    enum = nopfx(enum)
    line = f"{enum} = ENUM_T"
    eidx = 0
    output.append(line)

    while True:
        line = lines.pop(0)
        if line.strip().startswith('};'):
            break
        #     SIMCONNECT_TEXT_TYPE_PRINT_BLACK=0x0100,
        m = re.match(r'\s*(\w+)(?:\s*=\s*([0-9x]*))?\s*,?(.*)', line)
        if m:
            var, val, suffix = m.groups()
            var = nopfx(var)
            if val is None:
                eidx += 1
                val = eidx
            else:
                eidx = eval(val)
            line = f"{var} = ENUM_T({val}) {suffix}"
        output.append(line)
    output.append('')
    return True


def _ctyp(typ):
    ctyp = nopfx(typ).strip()
    if ctyp.startswith('const'):
        ctyp = ctyp[5:].strip()
    if ctyp.startswith('BOOL'):
        ctyp = 'bool' + ctyp[4:]
    m = re.match(r'([a-z]+(?:\s+\*)?)(.*)', ctyp)
    if m:
        t, suffix = m.groups()
        ctyp = 'c_' + re.sub(r'\s+', '_', t.replace('*', 'p')) + suffix
    stars = 0
    while True:
        ctyp = ctyp.strip()
        if ctyp[-1] != '*':
            break
        stars += 1
        ctyp = ctyp[:-1]
    for _ in range(stars):
        ctyp = f"POINTER({ctyp})"
    return ctyp


# unsigned long Flags; // ...
def maybeField(line, lines, fields) -> bool:
    m = re.match(r'\s*(?:(\w+)\s+)+(\w+)(\[\w+\])?\s*;(.*)', line)
    if not m:
        return False

    typ, field, size, suffix = m.groups()
    typ = _ctyp(typ)
    if size:
        typ = f"{typ} * {size.strip('[]')}"
    line = f'("{field}", {typ}), {suffix}'
    fields.append(line)
    return True


# struct SIMCONNECT_RECV_EXCEPTION : public SIMCONNECT_RECV // when dwID == SIMCONNECT_RECV_ID_EXCEPTION
def maybeStruct(line, lines, output) -> bool:
    m = re.match(r'\s*struct\s+(\w+)\s*(?::\s*public\s+(\w+))?(.*)', line)
    if not m:
        return False

    struct, base, suffix = m.groups()
    struct = nopfx(struct)
    base = nopfx(base) if base else 'Structure'
    line = f"class {struct}({base}):"
    output.append(line)
    fields: List[str] = []

    while True:
        line = lines.pop(0)
        if line.startswith('{'):
            continue
        elif line.startswith('};'):
            break
        elif maybeConst(line, lines, output, indent):
            continue
        elif maybeField(line, lines, fields):
            continue
        else:
            output.append(line)

    output.append(indent + '_fields_ = [')
    for line in fields:
        output.append(2 * indent + line)
    output.append(indent + ']')
    return True


# extern "C" HRESULT __attribute__((__stdcall__)) SimConnect_MapClientEventToSimEvent(HANDLE hSimConnect, ...
def maybeDecl(line, lines, decls) -> bool:
    m = re.match(r'extern\s+"C"\s+(.*?)\s+__attribute__\(\(__stdcall__\)\)\s+(\w+)\((.*?)\)', line)
    if not m:
        return False

    ret, func, arglist = m.groups()
    args = arglist.split(',')

    decls += [
        f"f = dll.{func}",
        f"f.restype = {ret}",
        "f.argtypes = [",
    ]
    for arg in args:
        m = re.match(r'(.*?)\s+(\w+)(?:\s*=\s*(.*))?$', arg.strip())
        assert m, f"Unrecognized arg {arg}"
        typ, var, dflt = m.groups()
        dflt = "default {dflt}" if dflt else ""
        decls.append(f"{indent}{_ctyp(typ)}, # {typ} {var} {dflt}")
    decls += [
        "]",
        f"_['{func.replace('SimConnect_', '')}'] = f",
    ]
    return True


indent = ' ' * 4

lines = open('SimConnect_cpp.h').read().splitlines()
lines = [line.replace('//', '# ', 1) for line in lines]

output: List[str] = []
aka = None
eidx = None
decls = [
    '\n\ndef _decls(dll):',
    '_ = dict()',
]
while lines:
    line = lines.pop(0)

    if maybeTypedef(line, lines, output):
        continue
    elif maybeConst(line, lines, output):
        continue
    elif maybeEnum(line, lines, output):
        continue
    elif maybeStruct(line, lines, output):
        continue
    elif maybeDecl(line, lines, decls):
        continue
    else:
        if line.startswith('typedef void') and 'DispatchProc' in line:
            # special case:
            # typedef void (CALLBACK *DispatchProc)(SIMCONNECT_RECV* pData, DWORD cbData, void* pContext);
            output.append('# ' + line)
            line = 'DispatchProc = WINFUNCTYPE(None, POINTER(RECV), DWORD, c_void_p)'
        output.append(line)

decls.append('return _\n')

with open('scdefs.py', 'w') as out:
    out.write("""
from types import SimpleNamespace
from ctypes import (
    c_bool, c_char, c_int, c_long, c_float, c_double,
    c_char_p, c_void_p,
    Structure, POINTER, HRESULT, WINFUNCTYPE,
)
from ctypes.wintypes import BYTE, WORD, DWORD, HANDLE, LPCSTR, HWND


ENUM_T = DWORD
FLT_MAX = 3.402823466e+38
MAX_PATH = 260
c_float_p = POINTER(c_float)


class GUID(Structure):
    _fields_ = [
        ("Data1", DWORD),
        ("Data2", WORD),
        ("Data3", WORD),
        ("Data4", BYTE * 8)
    ]


""")
    out.write('\n'.join(output))
    out.write(f"\n{indent}".join(decls))
