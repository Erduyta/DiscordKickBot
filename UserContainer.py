import asyncio

import grpc
import os

import yandex.cloud.ai.stt.v2.stt_service_pb2 as stt_service_pb2
import yandex.cloud.ai.stt.v2.stt_service_pb2_grpc as stt_service_pb2_grpc

cred = grpc.ssl_channel_credentials()
channel = grpc.aio.secure_channel('stt.api.cloud.yandex.net:443', cred)
stub = stt_service_pb2_grpc.SttServiceStub(channel)
user_queue = []

IAM_TOKEN = os.environ["IAM_TOKEN"]
ID_FOLDER = "b1gj08mqho7r4mv65hh9"

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


class UserContainer:
    def __init__(self, user_id, ctx):
        self.ctx = ctx
        self.user_id = user_id
        self.queue = asyncio.queues.Queue()
        asyncio.ensure_future(self._communicate_queue(ctx))

    def put_bytes(self, audio_content):
        msg = stt_service_pb2.StreamingRecognitionRequest(audio_content=audio_content)
        self.queue.put_nowait(msg)

    @staticmethod
    async def generate_from_queue(queue):
        yield config_msg
        while True:
            yield await queue.get()

    async def _communicate_queue(self, ctx):
        global stub

        it = stub.StreamingRecognize(
            UserContainer.generate_from_queue(self.queue),
            metadata=(('authorization', 'Bearer %s' % IAM_TOKEN),)
        )
        # Process server responses and output the result to the console.
        try:
            while True:
                r = await it.read()
                # print(r)
                try:
                    print('Start chunk: ')
                    for chunk in r.chunks:
                        for alternative in chunk.alternatives:
                            print('alternative: ', alternative.text)
                            if '????????????' in str(alternative.text).lower():
                                member_to_kick = ctx.voice_client.channel.guild.get_member(self.user_id)
                                await member_to_kick.edit(voice_channel=None)
                    print('Is final: ', r.chunks[0].final)

                    # print('')
                except LookupError:
                    print('Not available chunks')
        except Exception as err:
            print('Restarting because of error')
            print(err)
            await self._communicate_queue(ctx)