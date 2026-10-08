from shlex import split
from rich import print

COMMANDS : dict = {}

def command(name : str):
    def register(function):
        COMMANDS[name.lower()] = function
        return function
    return register

async def execute(line):
    if not line:
        return

    parts : list[str] = split(line)

    command_name = parts[0].lower()

    function : function = COMMANDS.get(command_name)

    if function is None:
        print(f"[red]Unknown command: {command_name}[/red]")
        return

    function(parts[1:])