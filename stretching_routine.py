import asyncio

import discord
import gretchen_credentials as credentials
from discord import app_commands

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        #commands = await self.tree.sync()
        pass

intents = discord.Intents.default()
# intents.members = True
client = MyClient(intents=intents)

@client.event
async def on_ready():
    drk = await client.fetch_user(credentials.peeps['drk'])

    await drk.send("stretching routine")

    for i in range(3):
        await asyncio.sleep(5)
        await drk.send("hands up")
        await asyncio.sleep(20)
        await drk.send("hands down")

    for i in range(3):
        await asyncio.sleep(5)
        await drk.send("left hand up")
        await asyncio.sleep(20)
        await drk.send("left hand down")
        await asyncio.sleep(5)
        await drk.send("right hand up")
        await asyncio.sleep(20)
        await drk.send("right hand down")

    await drk.send("on the floor")
    for i in range(3):
        await asyncio.sleep(5)
        await drk.send("arch")
        await asyncio.sleep(20)
        await drk.send("relax")

    await asyncio.sleep(5)
    await drk.send("roll; knees on the footrest")
    await asyncio.sleep(400)

    await drk.send("done")

client.run(credentials.bot_token)