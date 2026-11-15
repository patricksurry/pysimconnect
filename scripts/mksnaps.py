"""Generate terminal SVG snapshots in doc/*.svg from the actual simconnect CLI."""
import os
import sys
from unittest.mock import MagicMock, patch
from rich.console import Console
from rich.text import Text
from typer.testing import CliRunner

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from simconnect.cli import app, floatfmt, labelfmt, scoped_autocomplete

DOC_DIR = os.path.join(ROOT_DIR, "doc")
runner = CliRunner()


def save_terminal_svg(filename: str, command: str, output_lines: list, title: str = "simconnect"):
    console = Console(record=True, width=88)
    prompt = Text("PS > ", style="bold green")
    prompt.append(command, style="bold bright_white")
    console.print(prompt)
    for line in output_lines:
        if isinstance(line, Text):
            console.print(line)
        else:
            console.print(Text.from_ansi(line))
    out_path = os.path.join(DOC_DIR, filename)
    console.save_svg(out_path, title=title)
    return out_path


def generate_all():
    os.makedirs(DOC_DIR, exist_ok=True)

    # 1. sc-install-completion.svg
    save_terminal_svg(
        "sc-install-completion.svg",
        "simconnect --install-completion powershell",
        ["powershell completion installed in ~\\Documents\\PowerShell\\Microsoft.PowerShell_profile.ps1", "Completion will take effect once you restart the terminal"],
        title="simconnect --install-completion",
    )

    # 2. sc-search.svg
    with patch("simconnect.cli.webbrowser.open"):
        res = runner.invoke(app, ["search", "altitude"])
        save_terminal_svg(
            "sc-search.svg",
            "simconnect search altitude",
            res.stdout.strip().splitlines(),
            title="simconnect search",
        )

    # 3. sc-tab-completion.svg
    matches = scoped_autocomplete("VARIABLES")("PLA")
    row1 = "    ".join(f"{m:26s}" for m in matches[:3])
    row2 = "    ".join(f"{m:26s}" for m in matches[3:6])
    t_row1 = Text()
    t_row1.append(f"{matches[0]:26s}", style="black on bright_cyan")
    t_row1.append("    " + "    ".join(f"{m:26s}" for m in matches[1:3]))
    save_terminal_svg(
        "sc-tab-completion.svg",
        "simconnect get PLA<TAB>",
        [t_row1, Text(row2)],
        title="simconnect tab completion",
    )

    # 4. sc-get.svg, 5. sc-set.svg, 6. sc-send.svg
    with patch("simconnect.cli.SimConnect") as mock_sc_cls:
        mock_sc = MagicMock()
        mock_sc.__enter__.return_value = mock_sc
        mock_sc.get_simdatum.return_value = 5000.002311
        mock_sc_cls.return_value = mock_sc

        res_get = runner.invoke(app, ["get", "PLANE_ALTITUDE"])
        save_terminal_svg(
            "sc-get.svg",
            "simconnect get PLANE_ALTITUDE",
            res_get.stdout.strip().splitlines(),
            title="simconnect get",
        )

        res_set = runner.invoke(app, ["set", "PLANE_ALTITUDE", "1500", "--units", "meters"])
        save_terminal_svg(
            "sc-set.svg",
            "simconnect set PLANE_ALTITUDE 1500 --units meters",
            res_set.stdout.strip().splitlines(),
            title="simconnect set",
        )

        res_send = runner.invoke(app, ["send", "KOHLSMAN_INC"])
        save_terminal_svg(
            "sc-send.svg",
            "simconnect send KOHLSMAN_INC",
            res_send.stdout.strip().splitlines(),
            title="simconnect send",
        )

    # 7. sc-watch.svg
    headings = ["PLANE ALTITUDE", "INDICATED ALTITUDE", "AIRSPEED INDICATED"]
    hdr_even = "".join(labelfmt(headings[i]) for i in range(0, len(headings), 2))
    hdr_odd = " " * 12 + "".join(labelfmt(headings[i]) for i in range(1, len(headings), 2))
    watch_lines = [
        "Watching PLANE ALTITUDE, INDICATED ALTITUDE, AIRSPEED INDICATED every 1 seconds",
        hdr_even,
        hdr_odd,
    ]
    samples = [
        ([4912.4, 4910.1, 118.5], {0, 1, 2}),
        ([4914.2, 4912.0, 118.5], {0, 1}),
        ([4916.8, 4914.6, 118.9], {0, 1, 2}),
    ]
    for vals, changed_idxs in samples:
        row = Text()
        for idx, val in enumerate(vals):
            row.append(floatfmt(val), style="bold dodger_blue1" if idx in changed_idxs else "white")
        watch_lines.append(row)

    save_terminal_svg(
        "sc-watch.svg",
        "simconnect watch PLANE_ALTITUDE INDICATED_ALTITUDE AIRSPEED_INDICATED",
        watch_lines,
        title="simconnect watch",
    )


if __name__ == "__main__":
    generate_all()
