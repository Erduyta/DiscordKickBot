import asyncio
import json
import time
import threading
import os
import typing
from collections import defaultdict

import discord
import requests
from discord.ext import commands

from UserContainer import UserContainer

import grpc

import yandex.cloud.ai.stt.v2.stt_service_pb2 as stt_service_pb2
import yandex.cloud.ai.stt.v2.stt_service_pb2_grpc as stt_service_pb2_grpc

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



@bot.command()
async def start(ctx):
    await ctx.author.voice.channel.connect()
    await serve(ctx)


async def serve(ctx):
    ctx.voice_client.start_recording(discord.sinks.PCMSink(), finished_callback, ctx)
    await asyncio.sleep(0.2)
    ctx.voice_client.stop_recording()


async def finished_callback(sink, ctx):
    global user_containers
    for user_id, audio in sink.audio_data.items():
        if not user_containers.get(user_id):
            user_containers[user_id] = UserContainer(user_id, ctx)
        user_containers[user_id].put_bytes(audio.file.read())
    await serve(ctx)

@bot.command()
async def stop(ctx):
    await ctx.voice_client.disconnect()
    print("Stopped!")

if __name__ == "__main__":
    token = os.environ['BOT_TOKEN']
    bot.run(token)
