from dataclasses import dataclass


@dataclass
class Segment:
    """
    统一的句子级识别结果结构，三类引擎的输出最终都会被转换成 List[Segment]，
    再交给 asr.utils.srt_writer.segments_to_srt() 生成最终 SRT 文本。
    """

    start: float  # 相对于整段音频的起始时间，单位：秒
    end: float  # 相对于整段音频的结束时间，单位：秒
    text: str

    def shifted(self, offset_seconds: float) -> "Segment":
        """返回一个整体时间偏移 offset_seconds 之后的新 Segment（用于分片拼接场景）"""
        return Segment(
            start=self.start + offset_seconds,
            end=self.end + offset_seconds,
            text=self.text,
        )
