import re


class SubTitleUtils(object):
    # 解析 SRT 文件为结构化列表: [{index, start, end, text}, ...]
    @staticmethod
    def parse_srt(srt_path):
        """解析 SRT 文件为结构化列表: [{index, start, end, text}, ...]"""
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 统一换行符，按空行分割字幕块
        content = content.replace("\r\n", "\n").strip()
        blocks = re.split(r"\n\s*\n", content)

        subtitles = []
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 2:
                continue
            index = lines[0].strip()
            time_line = lines[1].strip()
            text = "\n".join(lines[2:]).strip()

            m = re.match(
                r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
                time_line
            )
            if not m:
                continue

            subtitles.append({
                "index": index,
                "start": m.group(1),
                "end": m.group(2),
                "text": text,
            })
        return subtitles

    # 将结构化字幕列表写回 SRT 文件
    @staticmethod
    def write_srt(subtitles, output_path):
        lines = []
        for i, sub in enumerate(subtitles, start=1):
            lines.append(str(i))  # 重新编号，避免原文件编号有问题
            lines.append(f"{sub['start']} --> {sub['end']}")
            lines.append(sub["text"])
            lines.append("")  # 空行分隔

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
