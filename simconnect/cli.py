import typer
import json
from typing import List, Optional, Dict, Any
from textwrap import fill
from enum import Enum
from difflib import SequenceMatcher
from simconnect import SimConnect
import os
import re
import webbrowser


app = typer.Typer()

thisdir = os.path.dirname(__file__)
with open(os.path.join(thisdir, 'scvars.json')) as f:
    scvars = json.load(f)
for k in ['EVENTS', 'VARIABLES', 'UNITS']:
    for d in scvars[k].values():
        d['name_'] = d['name' if k != 'UNITS' else 'name_std'].replace(' ', '_')


class MetadataKind(str, Enum):
    variable = 'variable'
    event = 'event'
    unit = 'unit'


def floatfmt(v, width=12, precision=3):
    s = f"{v:{width}.{precision}f}".rstrip('0').rstrip('.') 
    s += ' ' * (width - len(s))
    return s


def labelfmt(s, width=2*12):
    label = s if len(s) < width else s[:width-4] + '...'
    return f"{label:{width}s}"


def matchcase(s: str, prefix: str) -> Optional[str]:
    if not prefix:
        return s
    elif not s.upper().startswith(prefix.upper()):
        return None
    elif len(prefix) == len(s):
        return prefix
    else:
        tail = s[len(prefix):]
        return prefix + (tail.upper() if prefix[-1].isupper() else tail.lower())


def scoped_autocomplete(kind: str, max_results=10):
    def _complete(incomplete: str):
        return sorted(
            list(filter(None, (matchcase(d['name_'], incomplete) for d in scvars[kind].values()))),
            key=lambda s: (len(s), s)
        )[:max_results]
    return _complete


simvardef = typer.Argument(..., autocompletion=scoped_autocomplete('VARIABLES'))
eventdef = typer.Argument(..., autocompletion=scoped_autocomplete('EVENTS'))
unitsdef = typer.Option(None, autocompletion=scoped_autocomplete('UNITS'))


def canonicalvars(simvars: List[str]) -> List[str]:
    # appear to be case insenstive but ' ' vs '_' is important
    return [s.upper().replace('_', ' ') for s in simvars]


@app.command()
def get(simvars: List[str] = simvardef, units: Optional[str] = unitsdef):
    simvars = canonicalvars(simvars)
    unitdesc = f" ({units})" if units else ''
    with SimConnect(name='cli') as sc:
        for s in simvars:
            v = sc.get_simdatum(s, units)
            typer.echo(f"{s}{unitdesc} = {v}")


@app.command()
def watch(simvars: List[str] = simvardef, units: Optional[str] = unitsdef, interval: Optional[int] = 1):
    simvars = canonicalvars(simvars)
    typer.echo(f"Watching {', '.join(simvars)} every {interval} seconds")
    with SimConnect(name='cli') as sc:
        dd = sc.subscribe_simdata(
            [dict(name=sv, units=units) for sv in simvars],
            interval=interval
        )
        latest = 0
        headings = None
        while True:
            # consume incoming messages, waiting up to a second
            sc.receive(timeout_seconds=1)
            if not headings:
                # show staggered header across two lines
                headings = list(dd.simdata.keys())
                # even cols
                typer.echo(''.join(labelfmt(headings[i]) for i in range(0, len(headings), 2)))
                # odd cols
                typer.echo(' '*12 + ''.join(labelfmt(headings[i]) for i in range(1, len(headings), 2)))
            changed = list(dd.simdata.changedsince(latest).keys())
            latest = dd.simdata.latest()
            values = [
                typer.style(
                    floatfmt(dd.simdata[k]),
                    fg=typer.colors.BLUE if k in changed else typer.colors.WHITE
                )
                for k in headings
            ]
            typer.echo(''.join(values))


@app.command()
def set(simvar: str = simvardef, value: float = typer.Argument(...), units: Optional[str] = unitsdef):
    simvar = canonicalvars([simvar])[0]
    typer.echo(f"Setting {simvar} = {value}" + (f" ({units})" if units else ''))
    with SimConnect(name='cli') as sc:
        sc.set_simdatum(simvar, value, units)


@app.command()
def send(event: str = eventdef, value: Optional[int] = None):
    event = event.upper()
    typer.echo(f"Sending {event}({value})")
    with SimConnect(name='cli') as sc:
        sc.send_event(event, value or 0)


def _search_scvars(queries: List[str], kind: Optional[MetadataKind] = None) -> List[Dict[str, Any]]:
    kinds = [f"{kind.name.upper()}S"] if kind else ['VARIABLES', 'EVENTS', 'UNITS']
    raw_q = ' '.join(queries).strip()
    if not raw_q:
        return []
    tokens = [t.rstrip('*').lower() for t in re.split(r'[\s_]+', raw_q) if t.rstrip('*')]
    fuzzy = '~' in raw_q
    if fuzzy:
        tokens = [t.split('~')[0] for t in tokens if t.split('~')[0]]

    scored = []
    for k in kinds:
        for key, d in scvars[k].items():
            name_low = d['name'].lower().replace('_', ' ')
            desc_low = d.get('description', '').lower()
            cat_low = f"{d.get('page', '')} {d.get('section', '')}".lower()
            haystack = f"{name_low} {desc_low} {cat_low}"

            score = 0.0
            matched = True
            for tok in tokens:
                if tok in name_low:
                    score += 10.0 if name_low.startswith(tok) else 5.0
                    if name_low == tok:
                        score += 10.0
                elif tok in haystack:
                    score += 2.0
                elif fuzzy:
                    words = name_low.split()
                    best = max((SequenceMatcher(None, tok, w).ratio() for w in words), default=0.0)
                    if best >= 0.65:
                        score += best * 3.0
                    else:
                        matched = False
                        break
                else:
                    matched = False
                    break
            if matched and score > 0:
                scored.append((score, -len(d['name']), d['name'], dict(d, kind=k)))

    scored.sort(reverse=True)
    return [item[3] for item in scored]


DOCS_URL = "https://patricksurry.github.io/pysimconnect/"


@app.command()
def search(
    name: List[str],
    kind: Optional[MetadataKind] = None,
    max_results: int = 10,
    brief: bool = False,
    web: bool = False,
):
    if web:
        q = '+'.join(name)
        webbrowser.open(f"{DOCS_URL}#search={q}")
        return

    styles = dict(
        # in mac terminal some double-width emoji need a trailing space to display correctly
        # but this seems fine on windows terminal
        VARIABLES=dict(color=typer.colors.BLUE, symbol="🧭"),
        EVENTS=dict(color=typer.colors.GREEN, symbol="⚙️"),  # or maybe? 🔔
        UNITS=dict(color=typer.colors.RED, symbol="📐"),
        DIMENSIONS=dict(color=typer.colors.MAGENTA, symbol="📏"),
    )
    indent = ' ' * 4

    all_docs = _search_scvars(name, kind=kind)
    docs = all_docs[:max_results]

    typer.echo(
        'Showing '
        + typer.style(f"{len(docs)}/{len(all_docs)}", fg=typer.colors.BLUE)
        + ' results'
    )
    if not docs:
        typer.echo(fill("""
Perhaps try a shorter prefix like 'alti' or fuzzy match 'alti~'
        """.strip()))
    else:
        if len(docs) < len(all_docs):
            typer.echo('Increase --max-results for more')
        typer.echo('')
        for d in docs:
            name = d['name_std'] if ',' in d['name'] else d['name']
            style = styles[d['kind']]
            label = typer.style(f"{name}", fg=style['color'], bold=True)
            typer.echo(style['symbol'] + ' ' + label + f"{' ✏️' if d.get('settable') else ''}")
            if brief:
                continue
            desc = d.get('description')
            if desc:
                s = re.sub(r'\s*\n\s*', ' ', desc).strip()
                typer.echo(fill(s, initial_indent=indent, subsequent_indent=indent))
            loc = '; '.join(filter(None, [d['page'], d['section'] or None])).lower()
            typer.echo(f"{indent}Category: {loc}")
            if d.get('units'):
                lines = [s for s in d['units'].split('\n') if s.rstrip()]
                lines[0] = f"{indent}Default units: {lines[0]} [{d['dimensions']}]"
                typer.echo('\n'.join(lines))


if __name__ == "__main__":
    app()
