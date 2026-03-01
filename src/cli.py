import asyncio
import os
import click
import aiosqlite
from dotenv import load_dotenv

load_dotenv()

async def create_db_user(username: str):
    db_path = os.getenv("DATABASE_URL", "app.sqlite")
    async with aiosqlite.connect(db_path) as conn:
        try:
            await conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
            await conn.commit()
            click.secho(f"Successfully created user: {username}", fg="green")
        except Exception as e:
            click.secho(f"Error creating user: {e}", fg="red")

@click.group()
def cli():
    pass

@cli.command()
@click.argument('username')
def create_user(username):
    asyncio.run(create_db_user(username))

if __name__ == '__main__':
    cli()
