# Provides powershell fix from https://github.com/tiangolo/typer/pull/360 until new typer release

from typing import List, Tuple
import click
import os
from typer import _completion_shared
from typer.utils import _get_click_major

print('patching typer')

if '_TYPER_CURSOR_POSITION' not in _completion_shared.COMPLETION_SCRIPT_POWER_SHELL:
    _pwsh_script = """
Import-Module PSReadLine
Set-PSReadLineKeyHandler -Chord Tab -Function MenuComplete
$scriptblock = {
    param($wordToComplete, $commandAst, $cursorPosition)
    $Env:%(autocomplete_var)s = "complete_powershell"
    $Env:_TYPER_COMPLETE_ARGS = $commandAst.ToString()
    $Env:_TYPER_COMPLETE_WORD_TO_COMPLETE = $wordToComplete
    $Env:_TYPER_CURSOR_POSITION = $cursorPosition
    %(prog_name)s | ForEach-Object {
        $commandArray = $_ -Split ":::"
        $command = $commandArray[0]
        $helpString = $commandArray[1]
        [System.Management.Automation.CompletionResult]::new(
            $command, $command, 'ParameterValue', $helpString)
    }
    $Env:%(autocomplete_var)s = ""
    $Env:_TYPER_COMPLETE_ARGS = ""
    $Env:_TYPER_COMPLETE_WORD_TO_COMPLETE = ""
    $Env:_TYPER_CURSOR_POSITION = ""
}
Register-ArgumentCompleter -Native -CommandName %(prog_name)s -ScriptBlock $scriptblock
"""

    _completion_shared.COMPLETION_SCRIPT_POWER_SHELL = _pwsh_script
    for k in ('pwsh', 'powershell'):
        _completion_shared._completion_scripts[k] = _pwsh_script

    if _get_click_major() < 8:
        from typer import _completion_click7

        def do_powershell_complete(cli: click.Command, prog_name: str) -> bool:
            completion_args = os.getenv("_TYPER_COMPLETE_ARGS", "")
            incomplete = os.getenv("_TYPER_COMPLETE_WORD_TO_COMPLETE", "")
            cursor = os.getenv("_TYPER_CURSOR_POSITION")
            if cursor:
                completion_args = completion_args[:int(cursor)]
            cwords = click.parser.split_arg_string(completion_args)
            args = cwords[1:-1] if incomplete else cwords[1:]
            for item, help in click._bashcomplete.get_choices(cli, prog_name, args, incomplete):
                click.echo(f"{item}:::{help or ' '}")

            return True

        _completion_click7.do_powershell_complete = do_powershell_complete

    else:
        from typer import _completion_click8

        def get_completion_args(self) -> Tuple[List[str], str]:
            completion_args = os.getenv("_TYPER_COMPLETE_ARGS", "")
            incomplete = os.getenv("_TYPER_COMPLETE_WORD_TO_COMPLETE", "")
            cursor = os.getenv("_TYPER_CURSOR_POSITION")
            if cursor:
                completion_args = completion_args[:int(cursor)]
            cwords = click.parser.split_arg_string(completion_args)
            args = cwords[1:-1] if incomplete else cwords[1:]
            return args, incomplete

        _completion_click8.PowerShellComplete.get_completion_args = get_completion_args
