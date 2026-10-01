import asyncio
from pathlib import Path

from audio_separator.separator import Separator, InvalidAudioDataError, AudioExportError, BatchSeparationError

import config.config as _config
from pipeline.separate_vocals.base import SeparateVocalsBase
from utils import const
from utils.exception import VPTException
from utils.file_utils import get_separate_vocals_path


class SeparateVocals(SeparateVocalsBase):
    def __init__(
            self,
            src_mp3_path: str,
            dst_mp3_dir: str
    ):
        self.__src_mp3_path = src_mp3_path
        self.__dst_mp3_dir = dst_mp3_dir

    def convert(self) -> tuple[str, str]:
        src_mp3_real_path = Path(self.__src_mp3_path).resolve()
        if not src_mp3_real_path.is_file():
            raise VPTException(const.PIPELINE_ERR_FILE_NOT_FOUND, "the src mp3 file is not exists!")
        if not self.__dst_mp3_dir:
            raise VPTException(const.PIPELINE_ERR_VALUE, "when separate vocals, the target mp3 path is empty!")
        dst_mp3_dir_path = Path(self.__dst_mp3_dir)
        dst_mp3_dir_path.mkdir(parents=True, exist_ok=True)
        separator = Separator(
            output_dir=str(dst_mp3_dir_path),
            output_format="mp3"
        )
        try:
            separator.load_model()
            separator.separate(
                self.__src_mp3_path,
                custom_output_names={
                    "Vocals": f"{src_mp3_real_path.stem}_voice",
                    "Instrumental": f"{src_mp3_real_path.stem}_bgm",
                },
            )
            return (str(dst_mp3_dir_path.joinpath(f"{src_mp3_real_path.stem}_voice.mp3")),
                    str(dst_mp3_dir_path.joinpath(f"{src_mp3_real_path.stem}_bgm.mp3")))
        except InvalidAudioDataError as ex:
            raise VPTException(const.PIPELINE_ERR_ASR_AUDIO_SEPARATOR_INVALID_DATA,
                               "Decoded or generated audio data was empty, non-finite, or structurally invalid.",
                               tr=ex) from ex
        except AudioExportError as ex:
            raise VPTException(const.PIPELINE_ERR_ASR_AUDIO_SEPARATOR_AUDIO_EXPORT,
                               "An audio backend or filesystem failed to publish an output file.",
                               tr=ex) from ex
        except BatchSeparationError as ex:
            raise VPTException(const.PIPELINE_ERR_ASR_AUDIO_SEPARATOR_BATCH_SEPARATION,
                               "A list or directory input had one or more failures. All discoverable inputs are attempted first",
                               tr=ex) from ex


if __name__ == "__main__":
    _config.init_config()
    audio_separator_path = asyncio.run(get_separate_vocals_path())
    separate_vocals = SeparateVocals(
        src_mp3_path="/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/downloads/20260930174849775386.mp3",
        dst_mp3_dir=audio_separator_path if audio_separator_path else ""
    )
    files = separate_vocals.convert()
    print(files)
