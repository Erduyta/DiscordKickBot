import os
import random
import time
import asyncio
import discord
from discord.ext import commands
import json
import requests


description = """An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here."""

intents = discord.Intents.default()
intents.members = True
#intents.message_content = True

bot = commands.Bot(command_prefix="?", description=description, intents=intents)
URL = 'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize'
IAM_TOKEN = "token"
ID_FOLDER = "id_folder"
kostil = True


def recognize(data_sound):
    """ Функция распознавания русской речи

    :param IAM_TOKEN: (str)
    :param outh_guest: ответ гостя (bytes)
    :param ID_FOLDER: (str)
    :return text: (str)

    """
    # в поле заголовка передаем IAM_TOKEN:
    headers = {'Authorization': f'Bearer {IAM_TOKEN}'}

    # остальные параметры:
    params = {
        'lang': 'ru-RU',
        'folderId': ID_FOLDER,
        'sampleRateHertz': 48000,
    }

    response = requests.post(URL, params=params, headers=headers,
                             data=data_sound)

    # бинарные ответ доступен через response.content, декодируем его:
    decode_resp = response.content.decode('UTF-8')

    # и загрузим в json, чтобы получить текст из аудио:

    text = json.loads(decode_resp)
    print(text)
    return text


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

    ctx.voice_client.start_recording(discord.sinks.OGGSink(), finished_callback, ctx) # Start the recording
    print("Recording...")
    await asyncio.sleep(5)
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
        file = discord.File(audio.file, f"{user_id}.{sink.encoding}")
        print(dir(audio.file))
        text = recognize(audio.file).get('result', '').lower()
        if 'тимыч' in text:
            member_to_kick = ctx.voice_client.channel.guild.get_member(user_id)
            await member_to_kick.edit(voice_channel=None)
    await start(ctx)


@bot.command()
async def stop(ctx):
    await ctx.voice_client.disconnect()
    print("Stopped!")


if __name__ == "__main__":
    token = os.environ['BOT_TOKEN']
    bot.run(token)