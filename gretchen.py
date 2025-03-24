import datetime
import math
import random
import asyncio
import logging
import importlib
import dataclasses
import discord
from discord import app_commands

second = datetime.timedelta(seconds=1)
minute = datetime.timedelta(minutes=1)
hour = datetime.timedelta(hours=1)
day = datetime.timedelta(days=1)

for name in "gretchen", "hannah":
    if __file__.endswith(f"{name}.py"):
        credentials = importlib.import_module(f"{name}_credentials")
        print(name)
        logging.basicConfig(filename=f"{name}.log", filemode="w", level=logging.INFO)
        logger = logging.getLogger(name)

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

me = None
drk = None
queue = asyncio.Queue()
start_time = None

def bold_time(dt: datetime.datetime):
    return dt.strftime("**%H:%M**")

@dataclasses.dataclass
class Rescheduling:
    earliest: datetime.datetime
    latest: datetime.datetime

    def __post_init__(self):
        self.when = self._random_minute_between(self.earliest, self.latest)

        logger.debug(f"Scheduling for {self.schedule_string}, which will be at {self.when_str}")

    @property
    def schedule_string(self) -> str:
        return (
            self.earliest_str if (self.earliest == self.latest)
            else  f"{self.earliest_str} to {self.latest_str}"
        )

    @property
    def earliest_str(self) -> str:
        return bold_time(self.earliest)

    @property
    def latest_str(self) -> str:
        return bold_time(self.latest)

    @property
    def when_str(self) -> str:
        return bold_time(self.when)

    @staticmethod
    def _random_minute_between(earliest: datetime.datetime, latest: datetime.datetime) -> datetime.datetime:
        seconds_between = int((latest-earliest).total_seconds())
        if seconds_between < 60:
            return earliest

        while True:
            random_time = earliest + random.randint(0, int((latest-earliest).total_seconds()))*second

            random_minute = datetime.datetime(random_time.year, random_time.month, random_time.day, random_time.hour, random_time.minute)
            if random_minute < earliest or random_minute > latest:
                continue

            return random_minute

async def at(timeout):
    global queue

    now = datetime.datetime.now()
    try:
        message = await asyncio.wait_for(queue.get(), (timeout-now).total_seconds())
    except asyncio.TimeoutError:
        return
    else:
        if isinstance(message, Exception):
            raise message
    logger.error("Unrecognized message from the queue.")

async def at_noreschedule(timeout):
    while True:
        try:
            await at(timeout)
            break
        except RescheduleException as ex:
            logger.debug(f"Session already begun. Cannot reschedule.")
            await ex.interaction.response.send_message(f"Ed's edging has already begun. Cannot reschedule.")
            continue

class RescheduleExceptionBase(Exception):
    def __init__(self, schedule, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schedule = schedule
        self.interaction = interaction

class RescheduleException(RescheduleExceptionBase):
    pass

class ImmediateRescheduleException(RescheduleExceptionBase):
    pass

@client.event
async def on_ready():
    global client, me, drk, queue, start_time
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

    try:
        await client.change_presence(status=discord.Status.online)

        me = await client.fetch_user(credentials.peeps['me'])
        drk = await client.fetch_user(credentials.peeps['drk'])

        now = datetime.datetime.now()
        today = datetime.datetime(now.year, now.month, now.day)
        start_time = math.ceil((now - today).total_seconds()/60)*60*second + today

        logger.info(f'Beginning daily run')
        now = datetime.datetime.now()
        midnight = datetime.datetime(now.year, now.month, now.day) + 1*day
        noon = datetime.datetime(now.year, now.month, now.day) + 12*hour
        sched = Rescheduling(earliest=max(now, noon)+30*minute, latest=midnight)
        start_time = sched.when
        day_of_week = now.strftime("%A")

        await drk.send(f"Notifying Master Emily of today's edging start time.")
        await me.send(
            f"Master Emily, today, {day_of_week}, Ed will be required to begin edging at {bold_time(start_time)}."
            f"\n\nEd will not know when he will be edging today until his thirty minute advance notice at {bold_time(start_time-30*minute)}. He will also be given five minute and one minute warnings."
        )

        try:
            while True:
                try:
                    await at(start_time - 30*minute)

                except RescheduleException as ex:
                    logger.debug(f"Requested {ex.schedule.schedule_string}")
                    start_time = ex.schedule.when

                    await ex.interaction.response.send_message(
                        f"Requested {ex.schedule.schedule_string}.\n"
                        f"The new start time will be {bold_time(start_time)} with an advance notice at {bold_time(start_time - 30*minute)}."
                    )
                    continue

                try:
                    logger.info(f'Sending thirty minute warning to Dr. Krohne')
                    await drk.send(f"This is your notification that you will be edging in 30 minutes. You must begin at {bold_time(start_time)}.")

                    await at(start_time - 10*minute)
                    logger.info(f'Sending ten minute warning to Master Emily')
                    await me.send(f"This is your ten minute reminder that Ed will start edging. He will start at {bold_time(start_time)}.")

                    await at(start_time - 5*minute)
                    logger.info(f'Sending five minute warning to Dr. Krohne')
                    await drk.send(f"This is your five minute warning to begin edging. You must begin at {bold_time(start_time)}.")

                    await at(start_time - 1*minute)
                    logger.info(f'Sending one minute warning to Dr. Krohne')
                    await drk.send(f"This is your one minute warning to begin edging. You must begin at {bold_time(start_time)}.")

                    await at(start_time)
                    logger.info(f'Sending timeout to Dr. Krohne')
                    await drk.send(f"You must now be actively edging.")

                except RescheduleException as ex:
                    old_start_time = start_time
                    start_time = ex.schedule.when

                    await ex.interaction.response.send_message(
                        f"Reschedule for {ex.schedule.schedule_string}\n"
                        f"Because Ed had already been notified of today's edging start time of {bold_time(old_start_time)}, he has been told that you requested a manual reschedule, though not when.\n"
                        f"The new start time will be {bold_time(start_time)} with an advance notice at {bold_time(start_time - 30 * minute)}."
                    )

                    await drk.send(f"Master Emily has manually rescheduled today's edging start time. It will no longer be at {bold_time(old_start_time)}.")
                    continue

                break

        except ImmediateRescheduleException as ex:
            start_time = ex.schedule.when
            await ex.interaction.response.send_message(
                "Immediate reschedule!\n"
                "Ed is being given no advance notice that his edging is beginning absolutely immediately."
            )
            await drk.send(f"Master Emily has rescheduled your edging practice starting immediately.")


        for s in range(0,90,15):
            await at_noreschedule(start_time + s*second)
            await drk.send(f"You have {90-s} seconds to be close to orgasm.")

        await at_noreschedule(start_time + 90*second)
        await drk.send(f"You must be close to orgasm.")

        await at_noreschedule(start_time + 10*minute)
        await drk.send(f"You may stop or continue.  If you stop, remember your back exercises.")

        await at_noreschedule(start_time + 30*minute)
        await drk.send(f"You must stop if you have not.")

    finally:
        await client.close()

@client.tree.command()
@app_commands.choices(choice=[
    app_commands.Choice(name="immediately", value=-1),
    app_commands.Choice(name="in thirty minutes", value=0),
    *(
        app_commands.Choice(name=f"{n}:00 to {n+1}:59", value=n)
        for n in range(12, 24, 2)
    )
])
async def reschedule(interaction: discord.Interaction, choice: app_commands.Choice[int]):
    if interaction.user != me:
        await interaction.response.send_message(f"Only Master Emily can reschedule.")
        await me.send(f"{interaction.user} requested a manual reschedule, which is not allowed.")
        return



    if choice.value == -1:
        now = datetime.datetime.now()
        latest = earliest = now
        RescheduleExceptionType = ImmediateRescheduleException

    elif choice.value == 0:
        now = datetime.datetime.now()
        today = datetime.datetime(now.year, now.month, now.day)
        earliest = today + 30*minute + math.ceil((now-today).total_seconds()/60)*minute
        latest = earliest
        RescheduleExceptionType = RescheduleException

    else:
        now = datetime.datetime.now()
        today = datetime.datetime(now.year, now.month, now.day)
        earliest = today + choice.value*hour
        latest = earliest + 119*minute

        earliest = max(earliest, now+30*minute)

        if earliest > latest:
            await interaction.response.send_message(f"Impossible reschedule: this time slot will be over before Ed can be given a 30 minute notification.")
            return

        RescheduleExceptionType = RescheduleException

    queue.put_nowait(
        RescheduleExceptionType(
            schedule=Rescheduling(
                earliest=earliest,
                latest=latest
            ),
            interaction=interaction
        )
    )

client.run(credentials.bot_token)