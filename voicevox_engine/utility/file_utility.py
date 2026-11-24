"""ファイル操作に関するユーティリティ"""

import os
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import IO


def try_delete_file(file_path: str) -> None:
    """指定されたファイルの削除を試み、失敗したらログを残したうえでエラーを握り潰す。"""
    try:
        os.remove(file_path)
    except OSError:
        traceback.print_exc()


@contextmanager
def create_temp_file() -> Iterator[IO[bytes]]:
    """
    書き込み用の一時ファイルを作成する。

    ブロックを抜けるとファイルは閉じられるが、削除はされないため、呼び出し側で削除する必要がある。
    ブロック内で例外が発生した場合は、ファイルを削除してから例外を送出する。
    """
    file = NamedTemporaryFile(delete=False)
    try:
        with file:
            yield file
    except BaseException:
        # NOTE: Windows では開いているファイルを削除できないため、閉じてから削除する
        try_delete_file(file.name)
        raise
