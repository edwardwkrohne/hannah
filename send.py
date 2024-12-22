#!/usr/bin/env python3
"""
send a discord mesg
"""

import argparse
import asyncio
import discord
from hannah_credentials import peeps, bot_token


async def _send(userid, message):
    intents = discord.Intents.default()
    intents.members = True
    client = discord.Client(intents=intents)

    await client.login(bot_token)
    user = await client.fetch_user(userid)
    await user.send(message)
    await client.close()


def _main():
    fc = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=fc)
    parser.add_argument('user')
    parser.add_argument('message', nargs='*')
    args = parser.parse_args()

    userid = peeps.get(args.user, None)
    if userid is None:
        print(f"unknown user: {args.user}")
        return 1
    return asyncio.run(_send(userid, ' '.join(args.message)))


if __name__ == '__main__':
    exit(_main())
