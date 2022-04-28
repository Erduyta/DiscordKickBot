import asyncio
import json
import time
import os

import discord
import grpc
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
channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
stub = stt_service_pb2_grpc.SttServiceStub(channel)
speaking_queue = asyncio.queues.Queue()
user_queue = []

specification = stt_service_pb2.RecognitionSpec(
    language_code='ru-RU',
    profanity_filter=True,
    model='general',
    partial_results=True,
    audio_encoding='LINEAR16_PCM',
    sample_rate_hertz=48000
)
streaming_config = stt_service_pb2.RecognitionConfig(specification=specification, folder_id=ID_FOLDER)
config_msg = stt_service_pb2.StreamingRecognitionRequest(config=streaming_config)

def recognize_grpc(audio_bytes):
    # Establish a connection with the server.

    msg = stt_service_pb2.StreamingRecognitionRequest(audio_content=audio_bytes.read())
    send_msg([config_msg, msg])


def send_msg(msgs):
    global stub

    it = stub.StreamingRecognize(
        iter(msgs),
        metadata=(('authorization', 'Bearer %s' % IAM_TOKEN),)
    )
    # Process server responses and output the result to the console.
    try:
        for r in it:
            print(r)
            try:
                print('Start chunk: ')
                for alternative in r.chunks[0].alternatives:
                    print('alternative: ', alternative.text)
                print('Is final: ', r.chunks[0].final)
                print('')
            except LookupError:
                print('Not available chunks')
    except grpc._channel._Rendezvous as err:
        print('Error code %s, message: %s' % (err._state.code, err._state.details))


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")



@bot.command()
async def start(ctx):
    global kostil
    # print(dir(bot.get_all_channels()))
    # channel = discord.utils.get(server.channels, name="Channel_name_here", type="ChannelType.voice")
    #if not ctx.voice_client.is_connected():
    if kostil:
        await ctx.author.voice.channel.connect()
        kostil = False
    # Connect to the voice channel of the author

    ctx.voice_client.start_recording(discord.sinks.PCMSink(), finished_callback, ctx) # Start the recording
    print("Recording...")
    await asyncio.sleep(0.4)
    ctx.voice_client.stop_recording()
    print("Stopped!")


async def finished_callback(sink, ctx):
    print(sink.audio_data)
    # print(dir(sink.audio_data))
    # Here you can access the recorded files:
    recorded_users = [
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]
    for user_id, audio in sink.audio_data.items():
        #speaking_queue.put_nowait(audio.file)
        recognize_grpc(audio.file)
        # file = discord.File(audio.file, f"{user_id}.{sink.encoding}")
        # print(dir(audio.file))
        # text = recognize(audio.file).get('result', '').lower()
        # if 'тимыч' in text:
        #     member_to_kick = ctx.voice_client.channel.guild.get_member(user_id)
        #     await member_to_kick.edit(voice_channel=None)
    await start(ctx)


@bot.command()
async def stop(ctx):
    await ctx.voice_client.disconnect()
    print("Stopped!")


if __name__ == "__main__":
    token = os.environ['BOT_TOKEN']
    bot.run(token)
