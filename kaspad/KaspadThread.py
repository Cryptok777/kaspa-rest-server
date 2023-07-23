# encoding: utf-8
import asyncio
from queue import Queue

import grpc
from google.protobuf import json_format
from grpc._channel import _MultiThreadedRendezvous

from . import messages_pb2_grpc
from .messages_pb2 import KaspadMessage


MAX_MESSAGE_LENGTH = 1024 * 1024 * 1024  # 1GB


class KaspadCommunicationError(Exception):
    pass


# pipenv run python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/rpc.proto ./protos/messages.proto ./protos/p2p.proto


class KaspadThread(object):
    def __init__(self, kaspad_host, kaspad_port):

        self.kaspad_host = kaspad_host
        self.kaspad_port = kaspad_port

        self.channel = grpc.aio.insecure_channel(
            f"{kaspad_host}:{kaspad_port}",
            compression=grpc.Compression.Gzip,
            options=[
                ("grpc.max_send_message_length", MAX_MESSAGE_LENGTH),
                ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
            ],
        )

        self.stub = messages_pb2_grpc.RPCStub(self.channel)
        self.__queue = asyncio.queues.Queue()

    async def __aenter__(self, *args):
        return self

    async def __aexit__(self, *args):
        await self.channel.close()

    async def request(self, command, params=None, timeout=120):
        try:
            async for resp in self.stub.MessageStream(
                self.yield_cmd(command, params), timeout=timeout
            ):
                self.__queue.put_nowait("done")
                return json_format.MessageToDict(resp)
        except grpc.aio._call.AioRpcError as e:
            raise KaspadCommunicationError(str(e))

    async def notify(self, command, params=None, callback_func=None):
        try:
            async for resp in self.stub.MessageStream(self.yield_cmd(command, params)):
                if callback_func:
                    await callback_func(json_format.MessageToDict(resp))

        except (grpc.aio._call.AioRpcError, _MultiThreadedRendezvous) as e:
            raise KaspadCommunicationError(str(e))

    async def yield_cmd(self, cmd, params=None):
        msg = KaspadMessage()
        msg2 = getattr(msg, cmd)
        payload = params

        if payload:
            if isinstance(payload, dict):
                json_format.ParseDict(payload, msg2)
            if isinstance(payload, str):
                json_format.Parse(payload, msg2)

        msg2.SetInParent()
        yield msg
        await self.__queue.get()
