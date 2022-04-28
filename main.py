import asyncio
import json
import time
import threading
import os

import discord
import requests
from discord.ext import commands

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
URL = 'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize'
IAM_TOKEN = os.environ["IAM_TOKEN"]
ID_FOLDER = "b1g5pq4lh1ktoijrb9u1"
kostil = True

cred = grpc.ssl_channel_credentials()
channel = grpc.aio.secure_channel('stt.api.cloud.yandex.net:443', cred)
stub = stt_service_pb2_grpc.SttServiceStub(channel)
user_queue = []

specification = stt_service_pb2.RecognitionSpec(
    language_code='ru-RU',
    profanity_filter=False,
    model='general',
    partial_results=True,
    audio_encoding='LINEAR16_PCM',
    sample_rate_hertz=48000
)
streaming_config = stt_service_pb2.RecognitionConfig(specification=specification, folder_id=ID_FOLDER)
config_msg = stt_service_pb2.StreamingRecognitionRequest(config=streaming_config)
speaking_queue = asyncio.queues.Queue()


async def generate_from_queue(queue):
    yield config_msg
    while True:
        yield await queue.get()


async def communicate_queue(gen):
    global stub

    it = stub.StreamingRecognize(
        gen,
        metadata=(('authorization', 'Bearer %s' % IAM_TOKEN),)
    )
    # Process server responses and output the result to the console.
    try:
        while True:
            r = await it.read()
            #print(r)
            try:
                print('Start chunk: ')
                for alternative in r.chunks[0].alternatives:
                    print('alternative: ', alternative.text)
                print('Is final: ', r.chunks[0].final)
                #print('')
            except LookupError:
                print('Not available chunks')
    except Exception as err:
        print(err)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")



@bot.command()
async def start(ctx):
    await ctx.author.voice.channel.connect()
    asyncio.ensure_future(
        communicate_queue(generate_from_queue(speaking_queue))
    )
    await serve(ctx)
    # Connect to the voice channel of the author


async def serve(ctx):
    ctx.voice_client.start_recording(discord.sinks.PCMSink(), finished_callback, ctx) # Start the recording
    #print("Recording...")
    await asyncio.sleep(0.2)
    ctx.voice_client.stop_recording()
    #print("Stopped!")



async def finished_callback(sink, ctx):
    #print(sink.audio_data)
    # print(dir(sink.audio_data))
    # Here you can access the recorded files:
    recorded_users = [
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]
    for user_id, audio in sink.audio_data.items():
        #speaking_queue.put_nowait(audio.file)
        msg = stt_service_pb2.StreamingRecognitionRequest(audio_content=audio.file.read())
        speaking_queue.put_nowait(msg)
        # file = discord.File(audio.file, f"{user_id}.{sink.encoding}")
        # print(dir(audio.file))
        # text = recognize(audio.file).get('result', '').lower()
        # if 'тимыч' in text:
        #     member_to_kick = ctx.voice_client.channel.guild.get_member(user_id)
        #     await member_to_kick.edit(voice_channel=None)
    await serve(ctx)

@bot.command()
async def stop(ctx):
    await ctx.voice_client.disconnect()
    print("Stopped!")

if __name__ == "__main__":
    token = os.environ['BOT_TOKEN']
    bot.run(token)
