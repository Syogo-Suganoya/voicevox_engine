"""/multi_synthesis API のテスト。"""

import io
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from syrupy.assertion import SnapshotAssertion

from test.e2e.single_api.utils import gen_mora
from test.utility import hash_wave_floats_from_wav_bytes


def test_post_multi_synthesis_200(
    client: TestClient, snapshot: SnapshotAssertion
) -> None:
    queries = [
        {
            "accent_phrases": [
                {
                    "moras": [
                        gen_mora("テ", "t", 2.3, "e", 0.8, 3.3),
                        gen_mora("ス", "s", 2.1, "U", 0.3, 0.0),
                        gen_mora("ト", "t", 2.3, "o", 1.8, 4.1),
                    ],
                    "accent": 1,
                    "pause_mora": None,
                    "is_interrogative": False,
                }
            ],
            "speedScale": 1.0,
            "pitchScale": 1.0,
            "intonationScale": 1.0,
            "volumeScale": 1.0,
            "prePhonemeLength": 0.1,
            "postPhonemeLength": 0.1,
            "pauseLength": None,
            "pauseLengthScale": 1.0,
            "outputSamplingRate": 24000,
            "outputStereo": False,
            "kana": "テ'_スト",
        },
        {
            "accent_phrases": [
                {
                    "moras": [
                        gen_mora("テ", "t", 2.3, "e", 0.8, 3.3),
                        gen_mora("ス", "s", 2.1, "U", 0.3, 0.0),
                        gen_mora("ト", "t", 2.3, "o", 1.8, 4.1),
                        gen_mora("ト", "t", 2.3, "o", 1.8, 4.1),
                    ],
                    "accent": 1,
                    "pause_mora": None,
                    "is_interrogative": False,
                }
            ],
            "speedScale": 1.0,
            "pitchScale": 1.0,
            "intonationScale": 1.0,
            "volumeScale": 1.0,
            "prePhonemeLength": 0.2,
            "postPhonemeLength": 0.1,
            "pauseLength": None,
            "pauseLengthScale": 1.0,
            "outputSamplingRate": 24000,
            "outputStereo": False,
            "kana": "テ'_ストト",
        },
    ]
    response = client.post("/multi_synthesis", params={"speaker": 0}, json=queries)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # zip 内の全ての wav の波形がスナップショットと一致する
    zip_bytes = io.BytesIO(response.read())
    with zipfile.ZipFile(zip_bytes, "r") as zip_file:
        wav_files = (zip_file.read(name) for name in zip_file.namelist())
        for wav in wav_files:
            assert snapshot == hash_wave_floats_from_wav_bytes(wav)


def _gen_query(output_sampling_rate: int) -> dict[str, Any]:
    """指定したサンプリングレートの AudioQuery を生成する。"""
    return {
        "accent_phrases": [
            {
                "moras": [
                    gen_mora("テ", "t", 2.3, "e", 0.8, 3.3),
                    gen_mora("ス", "s", 2.1, "U", 0.3, 0.0),
                    gen_mora("ト", "t", 2.3, "o", 1.8, 4.1),
                ],
                "accent": 1,
                "pause_mora": None,
                "is_interrogative": False,
            }
        ],
        "speedScale": 1.0,
        "pitchScale": 1.0,
        "intonationScale": 1.0,
        "volumeScale": 1.0,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1,
        "pauseLength": None,
        "pauseLengthScale": 1.0,
        "outputSamplingRate": output_sampling_rate,
        "outputStereo": False,
        "kana": "テ'_スト",
    }


@pytest.fixture
def temp_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """一時ファイルの作成先を、テスト用に隔離されたディレクトリへ差し替える。"""
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp_dir))
    return temp_dir


def test_post_multi_synthesis_200_一時ファイルが残らない(
    client: TestClient, temp_dir: Path
) -> None:
    queries = [_gen_query(24000), _gen_query(24000)]
    response = client.post("/multi_synthesis", params={"speaker": 0}, json=queries)
    assert response.status_code == 200
    assert list(temp_dir.iterdir()) == []


def test_post_multi_synthesis_サンプリングレートが異なると422で一時ファイルが残らない(
    client: TestClient, temp_dir: Path
) -> None:
    queries = [_gen_query(24000), _gen_query(48000)]
    response = client.post("/multi_synthesis", params={"speaker": 0}, json=queries)
    assert response.status_code == 422
    assert list(temp_dir.iterdir()) == []


def test_post_multi_synthesis_合成に失敗しても一時ファイルが残らない(
    client: TestClient, temp_dir: Path
) -> None:
    # 存在しないスタイル ID を指定し、合成の途中で失敗させる
    queries = [_gen_query(24000), _gen_query(24000)]
    response = client.post("/multi_synthesis", params={"speaker": -1024}, json=queries)
    assert response.status_code == 422
    assert list(temp_dir.iterdir()) == []
