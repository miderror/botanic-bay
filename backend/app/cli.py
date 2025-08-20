import asyncio

import typer

from app.core.db import async_session
from app.core.init_db import init_roles

app = typer.Typer()


@app.command()
def init():
    """Initialize database with default data"""

    async def run_init():
        async with async_session() as session:
            await init_roles(session)
            typer.echo("✅ Roles created successfully!")

    typer.echo("Creating default roles...")
    asyncio.run(run_init())


def main():
    app()


if __name__ == "__main__":
    main()
