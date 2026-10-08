from command import command

from rich import print

@command("hello")
def hello(args : list[str]) -> None:
    print("[green]Hello Console[/green]")