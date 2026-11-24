"""ファイル操作用ユーティリティのテスト"""

from pathlib import Path

import pytest

from voicevox_engine.utility.file_utility import create_temp_file


def test_create_temp_file_正常終了ならファイルが残る() -> None:
    with create_temp_file() as f:
        f.write(b"test")
    path = Path(f.name)
    assert path.read_bytes() == b"test"
    path.unlink()


def _write_and_fail() -> str:
    """一時ファイルに書き込んだあと例外を送出する。"""
    with create_temp_file() as f:
        f.write(b"test")
        raise RuntimeError(f.name)


def test_create_temp_file_例外が発生したらファイルを削除する() -> None:
    with pytest.raises(RuntimeError) as e:
        _write_and_fail()
    assert not Path(str(e.value)).exists()
