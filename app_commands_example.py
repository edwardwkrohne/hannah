import discord
from discord import app_commands
from asyncio.queues import Queue
import asyncio

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        #commands = await self.tree.sync()
        #print(f"commands: {commands}")
        pass


intents = discord.Intents.default()
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

    timeout = 300

    try:
        while True:
            message = await asyncio.wait_for(queue.get(), timeout)
            timeout = message
            print(f"{timeout=}")
    except asyncio.TimeoutError:
        print('Timed out')

@client.tree.command()
@app_commands.choices(choice=[
    app_commands.Choice(name=f"{n}:00 to {n+1}:59", value=n)
    for n in range(12, 24, 2)
])
async def reschedule(interaction: discord.Interaction, choice: app_commands.Choice[int]):
    await interaction.response.send_message(f"Rescheduled for {choice.name}")
    queue.put_nowait(choice.value)

queue = Queue(maxsize=1)

import gretchen_credentials
client.run(gretchen_credentials.bot_token)