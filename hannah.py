from typing import Optional
import datetime
import random
import asyncio
import logging

import discord
from discord import app_commands
import hannah_credentials

logging.basicConfig(filename="hannah.log", level=logging.INFO)
logger = logging.getLogger('hannah')

MY_GUILD = discord.Object(id=hannah_credentials.peeps['greystone'])  # replace with your guild id

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

@client.tree.command()
async def hello(interaction: discord.Interaction):
    global client, me, drk

    # We create the view and assign it to a variable so we can wait for it later.
    # me = await client.fetch_user(hannah_credentials.peeps['drk'])
    # drk = await client.fetch_user(hannah_credentials.peeps['drk'])
    channel = interaction.channel
    view = Engage("Button from command text")
    await interaction.response.send_message("Asking Master Emily", ephemeral=True)
    await me.send('Master Emily, would you please hit "confirm" to confirm to Ed that he can write scripts that send messages asking questions?', view=view)

    # Wait for the View to stop listening for input...
    await view.wait()
    if view.value is None:
        print('Timed out...')
    elif view.value:
        await drk.send("Master Emily Confirmed")
        print('Confirmed...')
    else:
        await drk.send("Master Emily Cancelled")
        print('Cancelled...')

class Engage(discord.ui.View):
    def __init__(self, button_text: str):
        super().__init__()
        self.button_text = button_text
        self.value = None
        self.confirm.label = button_text

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True

me = None
drk = None

@client.event
async def on_ready():
    global client, me, drk
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

    me = await client.fetch_user(hannah_credentials.peeps['me'])
    drk = await client.fetch_user(hannah_credentials.peeps['drk'])

    try:
        logger.info(f'Beginning daily run')
        intents = discord.Intents.default()
        intents.members = True
        client = discord.Client(intents=intents)

        now = datetime.datetime.now()
        end_of_day = datetime.datetime(now.year, now.month, now.day) + 1*day
        seconds_to_wait = random.randint(0, (end_of_day - now).seconds)
        logger.debug(f"Will send message in {seconds_to_wait} seconds")

        drk_notification_time = as_string(now + seconds_to_wait*second)
        drk_start_time = as_string(now + seconds_to_wait*second + 30*minute)
        day_of_week = now.strftime("%A")

        view = Engage("Button text")
        await drk.send("Notifying Master Emily of today's edging start time.", view=view)
        await me.send(
            f"Master Emily, today, {day_of_week}, Ed will be required to begin edging at {drk_start_time}."
            f"\n\nEd will not know when he will be edging today until his thirty minute advance notice at {drk_notification_time}. He will also be given a five minute and one minute warnings."
        )
        await sleep_timedelta(seconds_to_wait*second)

        logger.info(f'Sending five minute warning to Dr. Krohne')
        await drk.send(f"This is your notification that you will be edging in 30 minutes. You must begin at {drk_start_time}.")

        await sleep_timedelta(20*minute)
        logger.info(f'Sending ten minute warning to Master Emily')
        await me.send(f"This is your ten minute reminder that Ed will start edging. He will start at {drk_start_time}.")

        await sleep_timedelta(5*minute)
        logger.info(f'Sending message to Dr. Krohne')
        await drk.send(f"This is your five minute warning to begin edging. You must begin at {drk_start_time}.")

        await sleep_timedelta(4*minute)
        logger.info(f'Sending message to Dr. Krohne')
        await drk.send(f"This is your one minute warning to begin edging. You must begin at {drk_start_time}.")

        await sleep_timedelta(1*minute)
        await drk.send(f"You must now be actively edging.")

        for t in range(90,0,-15):
            await drk.send(f"You have {t} seconds to be close to orgasm.")
            await sleep_timedelta(15*second)

        await drk.send(f"You must be close to orgasm.")
        await sleep_timedelta(10*minute-90*second)
        await drk.send(f"You may stop, or continue.")
        await sleep_timedelta(20*minute)
        await drk.send(f"You must stop, if you have not.")

    except Exception as e:
        logger.exception(e)
        raise
    finally:
        await client.close()

def as_string(dt):
    return dt.strftime("**%H:%M**")

second = datetime.timedelta(seconds=1)
minute = datetime.timedelta(minutes=1)
hour=datetime.timedelta(hours=1)
day=datetime.timedelta(days=1)

async def sleep_timedelta(td):
    await asyncio.sleep(td.seconds)

client.run(hannah_credentials.bot_token)

import sys
sys.exit()
