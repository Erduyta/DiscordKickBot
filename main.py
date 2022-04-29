import asyncio
import os

import discord
from discord.ext import commands

from UserContainer import UserContainer

description = """An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here."""

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="?", description=description, intents=intents)
user_containers: dict[str, UserContainer] = {}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


looper = None


@bot.command()
async def start(ctx):
    global looper
    await ctx.author.voice.channel.connect()
    await serve(ctx)
    looper = asyncio.get_event_loop()


class CustomSink(discord.sinks.PCMSink):
    def __init__(self, callback, ctx):
        super().__init__()
        self.callback = callback
        self.ctx = ctx

    def write(self, data, user):
        self.callback(data, user, self.ctx)


async def serve(ctx):
    ctx.voice_client.start_recording(CustomSink(finished_callback, ctx), finished_callback, ctx)


def finished_callback(data, user_id, ctx):
    global looper
    if looper is not None:
        asyncio.set_event_loop(looper)

    global user_containers
    if not user_containers.get(user_id):
        user_containers[user_id] = UserContainer(user_id, ctx)
    user_containers[user_id].put_bytes(data)

@bot.command()
async def stop(ctx):
    await ctx.voice_client.disconnect()
    print("Stopped!")

if __name__ == "__main__":
    token = os.environ['BOT_TOKEN']
    bot.run(token)
