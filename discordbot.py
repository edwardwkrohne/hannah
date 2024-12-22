#!/usr/bin/env python3
# This example requires the 'message_content' intent.

import logging

import arrow
import discord
import hannah_credentials


handler = logging.FileHandler(filename='discord.log',
                              encoding='utf-8', mode='w')


intents = discord.Intents.default()
intents.message_content = True
# intents.members = True
# intents.presences = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if '🔔' in message.content:
        guild = message.guild
        sbg = guild.get_member_named('slaveboygene')
        send = (":bell::bell::bell:\n"
                f"from: {message.author.display_name}@{message.channel.name}\n"
                f"message:\n{message.content}\n"
                ":bell::bell::bell:")
        await sbg.send(send)

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if 'infinity' in message.content:
        await message.channel.send(f'`{message.content=}`, `{type(message.content)=}`, Time has little to do with'
                                   ' infinity and jelly donuts.')

        await message.channel.send(embed={
            "content": "This is a message with components",
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "label": "Click me!",
                            "style": 1,
                            "custom_id": "click_one"
                        }
                    ]

                }
            ]
        })
    if message.content.startswith('watcher, goodnight'):
        await client.close()


@client.event
async def on_presence_update(before, after):
    if before.name in ['stvgld', 'slaveboygene']:
        return
    now = arrow.now()
    guild = before.guild
    sbg = guild.get_member_named('slaveboygene')
    upd = None
    now_str = now.isoformat(timespec='seconds')

    send = None
    if before.status != after.status:
        upd = (f"{now_str} {before.name}: status '{before.status}'"
               f" -> '{after.status}'")
        if after.status.value not in ['idle', 'offline']:
            send = upd
        print(upd)
    if before.activity != after.activity:
        upd = (f"{now_str} {before.name}: activity {before.activity}"
               f" -> {after.activity}")
        send = upd
        print(upd)
    if sbg and send:
        await sbg.send(send)

client.run(hannah_credentials.bot_token, log_handler=handler, log_level=logging.DEBUG)
