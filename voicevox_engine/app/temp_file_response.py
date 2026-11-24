"""一時ファイルを返すレスポンス"""

from starlette.responses import FileResponse
from starlette.types import Receive, Scope, Send

from voicevox_engine.utility.file_utility import try_delete_file


class TempFileResponse(FileResponse):
    """
    一時ファイルを返し、送信が終わったらファイルを削除するレスポンス。

    送信に失敗した場合（クライアントの切断など）も削除する。
    """

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """レスポンスを送信し、成否にかかわらず一時ファイルを削除する。"""
        try:
            await super().__call__(scope, receive, send)
        finally:
            try_delete_file(str(self.path))
