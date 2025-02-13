# This example requires the 'message_content' privileged intent to function.

if __file__.endswith('gretchen.py'):
    import gretchen_credentials as credentials
elif __file__.endswith('hannah.py'):
    import hannah_credentials as credentials
else:
    print("unrecognized file ending")

from discord.ext import commands

import discord

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents)



# Define a simple View that gives us a confirmation menu
class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.value = True
        # self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Cancelling', ephemeral=True)
        self.value = False
        # self.stop()


bot = Bot()
me, drk = None, None
@bot.event
async def on_ready():
    global bot, me, drk

    me = await bot.fetch_user(credentials.peeps['drk'])
    drk = await bot.fetch_user(credentials.peeps['drk'])

    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

    view = Confirm()
    await drk.send('Do you want to continue?', view=view)
    # Wait for the View to stop listening for input...
    await view.wait()

    await drk.send('View is now finished.')
    if view.value is None:
        await drk.send('Timed out.')
    elif view.value:
        await drk.send('Confirmed.')
    else:
        await drk.send('Canceled.')

@bot.command()
async def ask(ctx: commands.Context):
    """Asks the user a question to confirm something."""
    # We create the view and assign it to a variable so we can wait for it later.
    view = Confirm()
    await ctx.send('Do you want to continue?', view=view)
    # Wait for the View to stop listening for input...
    await view.wait()
    if view.value is None:
        print('Timed out...')
    elif view.value:
        print('Confirmed...')
    else:
        print('Cancelled...')


bot.run(credentials.bot_token)