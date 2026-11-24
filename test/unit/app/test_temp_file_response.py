"""一時ファイルを返すレスポンスのテスト"""

from pathlib import Path

import anyio
import pytest
from starlette.types import Message

from voicevox_engine.app.temp_file_response import TempFileResponse


def _create_file(tmp_path: Path) -> Path:
    path = tmp_path / "temp.wav"
    path.write_bytes(b"x" * 200_000)
    return path


def _scope() -> dict[str, object]:
    # NOTE: ASGI 2.4 では、切断後の send は OSError を送出する
    return {
        "type": "http",
        "method": "POST",
        "headers": [],
        "asgi": {"spec_version": "2.4"},
    }


async def _receive() -> Message:
    return {"type": "http.request", "body": b"", "more_body": False}


def test_送信が終わったら一時ファイルを削除する(tmp_path: Path) -> None:
    path = _create_file(tmp_path)
    received: list[Message] = []

    async def send(message: Message) -> None:
        received.append(message)

    anyio.run(TempFileResponse(path), _scope(), _receive, send)

    assert received[-1]["more_body"] is False
    assert not path.exists()


def test_送信に失敗しても一時ファイルを削除する(tmp_path: Path) -> None:
    path = _create_file(tmp_path)

    async def send(message: Message) -> None:
        if message["type"] == "http.response.body":
            raise OSError("クライアントが切断した")

    with pytest.raises(OSError, match="クライアントが切断した"):
        anyio.run(TempFileResponse(path), _scope(), _receive, send)

    assert not path.exists()
