import datetime
import math
import random
import asyncio
import logging
import importlib
import dataclasses
import discord
import queue
from discord import app_commands
import concurrent.futures
from requirement_pool import requirements_strings
import contextlib
import pyaudio
import wave

for name in "gretchen", "hannah", "ingrid":
    if __file__.endswith(f"{name}.py"):
        credentials = importlib.import_module(f"{name}_credentials")
        print(name)
        logging.basicConfig(
            filename=f"{name}.log",
            filemode="w",
            format='%(asctime)s %(levelname)s:%(message)s',
            level=logging.INFO)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)


second = datetime.timedelta(seconds=1)
minute = datetime.timedelta(minutes=1)
hour = datetime.timedelta(hours=1)
day = datetime.timedelta(days=1)

drk_warning_time = 70*minute

class WarningSounds:
    def __init__(self):
        logger.debug("Initializing WarningSounds")
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def __enter__(self):
        logger.debug("Entering WarningSounds context")
        with contextlib.ExitStack() as stack:
            self._pyaudio = pyaudio.PyAudio()
            stack.callback(self._pyaudio.terminate)

            info = self._pyaudio.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')

            devices = {i: self._pyaudio.get_device_info_by_index(i) for i in range(0, numdevices)}
            self._device, = [device for i, device in devices.items() if 'LG' in device['name']]
            device_index = self._device['index']

            self._wave_file = stack.enter_context(wave.open("iwould.wav"))

            self._stream = self._pyaudio.open(
                format=self._pyaudio.get_format_from_width(self._wave_file.getsampwidth()),
                channels=self._wave_file.getnchannels(),
                rate=self._wave_file.getframerate(),
                output=True,
                output_device_index=device_index
            )
            stack.callback(self._stream.close)
            stack.callback(self._stream.stop_stream)

            self._executor = stack.enter_context(concurrent.futures.ThreadPoolExecutor(max_workers=1))

            self._context_stack = stack.pop_all()

        self._context_stack.__enter__()
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            logger.debug("Exiting context")
            return self._context_stack.__exit__(exc_type, exc_val, exc_tb)
        finally:
            self._pyaudio.terminate()

    def play(self, num):
        logger.debug("Playing")
        for i in range(num):
            self._executor.submit(self._play_task)

    def _play_task(self):
        CHUNK = 8192

        # play stream (3)
        try:
            data = self._wave_file.readframes(CHUNK)
            while len(data) > 0:
                self._stream.write(data)
                data = self._wave_file.readframes(CHUNK)
        finally:
            self._wave_file.rewind()


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

class RescheduleExceptionBase(Exception):
    def __init__(self, schedule, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schedule = schedule
        self.interaction = interaction

class RescheduleException(RescheduleExceptionBase):
    pass

class ImmediateRescheduleException(RescheduleExceptionBase):
    pass

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def main(self):

        me_requirements_str, drk_requirements_str = requirements_strings()

        async with self:
            with WarningSounds() as warning_sounds:
                self._client_task = asyncio.create_task(client.start(credentials.bot_token))
                await self.wait_until_ready()

                self.queue = asyncio.Queue()

                self.me = await self.fetch_user(credentials.peeps['me'])
                self.drk = await self.fetch_user(credentials.peeps['drk'])

                logger.info(f'Beginning daily run')

                now = datetime.datetime.now()
                today = datetime.datetime(now.year, now.month, now.day)
                midnight = today + 1 * day
                noon = today + 12 * hour
                sched = Rescheduling(earliest=max(now, noon) + drk_warning_time, latest=midnight)
                start_time = sched.when
                day_of_week = now.strftime("%A")

                await self.drk.send(f"Notifying Master Emily of today's training start time.")
                await self.me.send(
                    f"Master Emily, today, {day_of_week}, Ed will be required to begin training at {bold_time(start_time)}."
                    f"\n\nEd will not know when he will be training today until his {str_timedelta(drk_warning_time, plural=False)} advance notice at {bold_time(start_time - drk_warning_time)}."
                    " He will also be given thirty minute, five minute, and one minute warnings."
                    f"\n{me_requirements_str}"
                )

                try:
                    while True:
                        try:
                            await self.at(start_time - drk_warning_time)

                        except RescheduleException as ex:
                            logger.debug(f"Requested {ex.schedule.schedule_string}")
                            start_time = ex.schedule.when

                            await ex.interaction.response.send_message(
                                f"Requested {ex.schedule.schedule_string}.\n"
                                f"The new start time will be {bold_time(start_time)} with an advance notice at {bold_time(start_time - drk_warning_time)}."
                            )
                            continue

                        try:
                            logger.info(f'Sending warning to Dr. Krohne')
                            await self.drk.send(
                                f"This is your notification that you will be training in {str_timedelta(drk_warning_time)}. You must begin at {bold_time(start_time)}."
                                f"\n{drk_requirements_str}"
                            )
                            warning_sounds.play(3)

                            if drk_warning_time > 30 * minute:
                                await self.at(start_time - 30 * minute)
                                logger.info(f'Sending thirty minute warning to Dr. Krohne')
                                await self.drk.send(
                                    f"This is your thirty minute warning to begin training. You must begin at {bold_time(start_time)}.")
                                warning_sounds.play(1)

                            await self.at(start_time - 10 * minute)
                            logger.info(f'Sending ten minute warning to Master Emily')
                            await self.me.send(
                                f"This is your ten minute reminder that Ed will start training. He will start at {bold_time(start_time)}.")

                            if drk_warning_time >= 5 * minute:
                                await self.at(start_time - 5 * minute)
                                logger.info(f'Sending five minute warning to Dr. Krohne')
                                await self.drk.send(
                                    f"This is your five minute warning to begin training. You must begin at {bold_time(start_time)}.")
                                warning_sounds.play(1)

                            await self.at(start_time - 1 * minute)
                            logger.info(f'Sending one minute warning to Dr. Krohne')
                            await self.drk.send(
                                f"This is your one minute warning to begin training. You must begin at {bold_time(start_time)}.")
                            warning_sounds.play(1)

                            await self.at(start_time)
                            logger.info(f'Sending timeout to Dr. Krohne')
                            await self.drk.send(f"You must now be actively training.")
                            warning_sounds.play(2)

                        except RescheduleException as ex:
                            old_start_time = start_time
                            start_time = ex.schedule.when

                            await ex.interaction.response.send_message(
                                f"Reschedule for {ex.schedule.schedule_string}\n"
                                f"Because Ed had already been notified of today's training start time of {bold_time(old_start_time)}, he has been told that you requested a manual reschedule, though not when.\n"
                                f"The new start time will be {bold_time(start_time)} with an advance notice at {bold_time(start_time - drk_warning_time)}."
                            )

                            await self.drk.send(
                                f"Master Emily has manually rescheduled today's training start time. It will no longer be at {bold_time(old_start_time)}.")
                            continue

                        break

                except ImmediateRescheduleException as ex:
                    start_time = ex.schedule.when
                    await ex.interaction.response.send_message(
                        "Immediate reschedule!\n"
                        "Ed is being given no advance notice that his training is beginning absolutely immediately."
                    )
                    await self.drk.send(
                        f"Master Emily has rescheduled your training starting immediately."
                        f"\n{drk_requirements_str}"
                    )
                    warning_sounds.play(5)

                for s in range(0, 90, 15):
                    await self.at_noreschedule(start_time + s * second)
                    await self.drk.send(f"You have {90 - s} seconds to be close to orgasm.")

                await self.at_noreschedule(start_time + 90 * second)
                await self.drk.send(f"You must be close to orgasm.")

                await self.at_noreschedule(start_time + 10 * minute)
                await self.drk.send(f"You may stop or continue.  If you stop, remember your back exercises.")

                await self.at_noreschedule(start_time + 30 * minute)
                await self.drk.send(f"You must stop if you have not.")

    async def at(self, timeout):
        now = datetime.datetime.now()
        try:
            message = await asyncio.wait_for(self.queue.get(), (timeout - now).total_seconds())
        except asyncio.TimeoutError:
            return
        else:
            if isinstance(message, Exception):
                raise message
        logger.error("Unrecognized message from the queue.")

    async def at_noreschedule(self, timeout):
        while True:
            try:
                await self.at(timeout)
                break
            except RescheduleException as ex:
                logger.debug(f"Session already begun. Cannot reschedule.")
                await ex.interaction.response.send_message(f"Ed's training has already begun. Cannot reschedule.")
                continue

    async def setup_hook(self):
        #commands = await self.tree.sync()
        pass

def bold_time(dt: datetime.datetime):
    return dt.strftime("**%H:%M**")

def str_timedelta(td: datetime.timedelta, plural=True):
    num_minutes = int(td.total_seconds()) // 60

    return f"{num_minutes} minute" if not plural or num_minutes == 1 else f"**{num_minutes} minutes**"

client = MyClient(intents=discord.Intents.default())

@client.tree.command()
@app_commands.choices(choice=[
    app_commands.Choice(name="immediately", value=-1),
    app_commands.Choice(name="soon", value=0),
    *(
        app_commands.Choice(name=f"{n}:00 to {n+1}:59", value=n)
        for n in range(12, 24, 2)
    )
])
async def reschedule(interaction: discord.Interaction, choice: app_commands.Choice[int]):
    if interaction.user != client.me:
        await interaction.response.send_message(f"Only Master Emily can reschedule.")
        await client.me.send(f"{interaction.user} requested a manual reschedule, which is not allowed.")
        return

    if choice.value == -1:
        now = datetime.datetime.now()
        latest = earliest = now
        RescheduleExceptionType = ImmediateRescheduleException

    elif choice.value == 0:
        now = datetime.datetime.now()
        today = datetime.datetime(now.year, now.month, now.day)
        earliest = today + drk_warning_time + math.ceil((now-today).total_seconds()/60)*minute
        latest = earliest
        RescheduleExceptionType = RescheduleException

    else:
        now = datetime.datetime.now()
        today = datetime.datetime(now.year, now.month, now.day)
        earliest = today + choice.value*hour
        latest = earliest + 119*minute

        earliest = max(earliest, now+drk_warning_time)

        if earliest > latest:
            await interaction.response.send_message(f"Impossible reschedule: this time slot will be over before Ed can be given a {str_timedelta(drk_warning_time, plural=False)} notification.")
            return

        RescheduleExceptionType = RescheduleException

    client.queue.put_nowait(
        RescheduleExceptionType(
            schedule=Rescheduling(
                earliest=earliest,
                latest=latest
            ),
            interaction=interaction
        )
    )


if __name__ == "__main__":
    asyncio.run(client.main())

