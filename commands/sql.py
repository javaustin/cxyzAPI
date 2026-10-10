import re

import aiosqlite
from rich import print

import app_instance
from utils.commands import command
from utils.deliveries import deliver

@command("sql", aliases = ["query"])
async def sql(args : list[str]) -> None:
    """
    Execute SQL queries and push the modified rows to game servers.

    Usage: sql <query> -p={bool}
    """

    if len(args) == 0:
        print("[red]Usage: sql <query> -p={bool}[/red]")
        return None

    push_flag : bool = False

    for arg in args:
        if arg.startswith("-p"):
            push_flag = arg[2:].lower() in ["true"]
            args.remove(arg)
            break

    query = " ".join(args)

    try:
        db = app_instance.db

        async with app_instance.db_lock:
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            await cursor.close()
            await db.commit()

            match = re.search(
                r"(?:FROM|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                query,
                re.IGNORECASE
            )
            table = match.group(1) if match else None

            is_write: bool = query.lstrip().split(maxsplit=1)[0].upper() in {"INSERT", "UPDATE", "DELETE", "REPLACE"}

            res = [dict(row) for row in rows]

            if not table and not push_flag:
                print("[green]Operation successful![/green]")
                return None

            elif not table: # push_flag == True
                print("[yellow]Nothing to push![/yellow]")
                return None

            if is_write and not push_flag:
                print("[yellow]Push disabled by flag![/yellow]")

            if is_write and push_flag:
                await deliver(table, [dict(row) for row in rows], [dict(row) for row in rows])
                print(f"[magenta]Pushed updated rows to all available game servers.[/magenta]")
                print(res)

            if not is_write and push_flag:
                print("[yellow]Nothing to push![/yellow]")
                return None

            else: # View the rows
                print("[white]res[/white]")

    except aiosqlite.OperationalError as ex:
        print(f"[red]Could not fulfill the SQL query because of the error:[/red] {ex}")
        return None

    except Exception as ex:
        print(f"[red]{ex}[/red]")