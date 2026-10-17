"""Conservative sentence grouping; subtitle IDs remain traceable in reports."""
import re

import srt

MAX_SEGMENT_MS = 10000
MAX_SUBTITLES = 6
# Do not move speech across a visible pause; only join nearly continuous cues.
MAX_JOIN_GAP_MS = 150
SENTENCE_END = re.compile(r'''[.!?。！？]["'”’）)]*$''')
SPEAKER_START = re.compile(r"^\s*(?:[-–—]\s+|\[[^]]+\]|[^:：\n]{1,24}[:：]\s)")


def group_subtitles(subs):
    """Return grouped source subtitles and their original IDs, without mutating inputs.

    Punctuation is a conservative semantic boundary, not speaker recognition.
    No reliable speaker metadata is currently available from the ASR pipeline.
    """
    groups, mappings, current = [], [], []

    def flush():
        if not current:
            return
        groups.append(srt.Subtitle(len(groups) + 1, current[0].start, current[-1].end,
                                   " ".join(s.content.strip() for s in current)))
        mappings.append([s.index for s in current])
        current.clear()

    for sub in subs:
        if sub.start.total_seconds() < 0 or sub.end <= sub.start:
            raise ValueError(f"Subtitle {sub.index}: invalid time window")
        if current:
            previous = current[-1]
            gap = (sub.start - previous.end).total_seconds() * 1000
            span = (sub.end - current[0].start).total_seconds() * 1000
            if gap < 0:
                raise ValueError(f"Subtitle {sub.index}: overlapping time window")
            if (gap > MAX_JOIN_GAP_MS or span > MAX_SEGMENT_MS or len(current) >= MAX_SUBTITLES
                    or SENTENCE_END.search(previous.content.strip())
                    or SPEAKER_START.match(sub.content)
                    or not previous.content.strip() or not sub.content.strip()):
                flush()
        # Check ordering even when a preceding sentence was already flushed.
        if groups and not current and sub.start < groups[-1].end:
            raise ValueError(f"Subtitle {sub.index}: overlapping time window")
        current.append(sub)
    flush()
    return groups, mappings


def timestamp(value):
    milliseconds = round(value.total_seconds() * 1000)
    seconds, ms = divmod(milliseconds, 1000)
    minutes, second = divmod(seconds, 60)
    hour, minute = divmod(minutes, 60)
    return f"{hour:02}:{minute:02}:{second:02},{ms:03}"


def as_rewrite_subtitles(subs):
    return [{"index": str(s.index), "start": timestamp(s.start), "end": timestamp(s.end),
             "text": s.content} for s in subs]
