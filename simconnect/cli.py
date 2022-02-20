import typer
import json
from typing import List, Optional
from textwrap import fill
from enum import Enum
from lunr.index import Index
from simconnect import SimConnect
import os
import re


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
    def _complete(q: str):
        return sorted(
            list(filter(None, (matchcase(d['name_'], q) for d in scvars[kind].values()))),
            key=lambda s: (len(s), s)[:max_results]
        )
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
    for s in simvars:
        with SimConnect(name='cli') as sc:
            v = sc.get_simdatum(s.replace('_,', ' '), units)
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
def send(event: str = eventdef, value: Optional[float] = None):
    event = event.upper()
    typer.echo(f"Sending {event}({value})")
    with SimConnect(name='cli') as sc:
        sc.send_event(event, value or 0)


@app.command()
def search(name: List[str], kind: Optional[MetadataKind] = None, max_results: int = 5, brief: bool = False):
    q = ' '.join(name)
    if kind:
        q += f" +kind:{kind.name.upper()}S"

    with open(os.path.join(thisdir, 'scvars_idx.json')) as f:
        scvarsidx = Index.load(json.load(f))

    styles = dict(
        # in mac terminal some double-width emoji need a trailing space to display correctly
        # but this seems fine on windows terminal
        VARIABLES=dict(color=typer.colors.BLUE, symbol="🧭"),
        EVENTS=dict(color=typer.colors.GREEN, symbol="⚙️"),  # or maybe? 🔔
        UNITS=dict(color=typer.colors.RED, symbol="📐"),
        DIMENSIONS=dict(color=typer.colors.MAGENTA, symbol="📏"),
    )
    indent = ' ' * 4

    refs = scvarsidx.search(q)
    if not refs and not q.endswith('*'):
        # Try implicit wildcard if not results
        refs = scvarsidx.search(q.rstrip() + '*')
    docs = []
    for r in refs[:max_results]:
        k, name = r['ref'].split('_', 1)
        docs.append(dict(scvars[k][name], kind=k))

    typer.echo(
        'Showing '
        + typer.style(f"{len(docs)}/{len(refs)}", fg=typer.colors.BLUE)
        + ' results'
    )
    if not docs:
        typer.echo(fill("""
Perhaps try wildcard 'alti*', fuzzy match 'alti~2'
or advanced options at https://lunr.readthedocs.io/en/latest/usage.html
        """.strip()))
    else:
        if len(docs) < len(refs):
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
