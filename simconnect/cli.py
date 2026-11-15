import typer
import json
from typing import List, Optional
from simconnect import SimConnect
import os
import webbrowser


app = typer.Typer()
DOCS_URL = "https://patricksurry.github.io/pysimconnect/"

thisdir = os.path.dirname(__file__)
with open(os.path.join(thisdir, 'scvars.json')) as f:
    scvars = json.load(f)
for k in ['EVENTS', 'VARIABLES', 'UNITS']:
    for d in scvars[k].values():
        d['name_'] = d['name' if k != 'UNITS' else 'name_std'].replace(' ', '_')



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


@app.command()
def search(name: Optional[List[str]] = typer.Argument(None)):
    """Open the interactive SimConnect SDK Explorer in your web browser."""
    q = '+'.join(name) if name else ''
    url = f"{DOCS_URL}#search={q}" if q else DOCS_URL
    typer.echo(f"Opening {url}")
    webbrowser.open(url)


if __name__ == "__main__":
    app()
