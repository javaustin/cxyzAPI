from shlex import split
from rich import print

COMMANDS : dict = {}

def command(name : str, aliases : list[str]):
    def register(function):

        if name.lower() in COMMANDS:
            raise RuntimeError(f"Duplicate command registration: {name.lower()}")

        COMMANDS[name.lower()] = function

        for alias in aliases:
            if alias.lower() in COMMANDS:
                raise RuntimeError(f"Duplicate command registration: {alias.lower()}")
            else:
                COMMANDS[alias.lower()] = function

        return function

    return register

async def execute_command(line):
    if not line:
        return

    parts : list[str] = split(line)

    command_name = parts[0].lower()

    function : function = COMMANDS.get(command_name)

    if function is None:
        print(f"[red]Unknown command[/red]: '{command_name}'")
        return

    await function(parts[1:])