# ============================================================================
# FILE: aprocess.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import asyncio
import typing


class Process(asyncio.SubprocessProtocol):

    def __init__(self, plugin: typing.Any) -> None:
        self._plugin = plugin
        self._vim = plugin._vim

    def connection_made(self, transport: typing.Any) -> None:
        self._unpacker = self._plugin._connect_stdin(
            transport.get_pipe_transport(0))

    def pipe_data_received(self, fd: int, data: typing.Any) -> None:
        unpacker = self._unpacker
        unpacker.feed(data)
        for child_out in unpacker:
            self._plugin._queue_out.put(child_out)

    def process_exited(self) -> None:
        pass
