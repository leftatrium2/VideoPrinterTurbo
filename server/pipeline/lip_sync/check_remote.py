"""Run one real remote job without importing the VideoPrinterTurbo application."""
import argparse
import json
import os
import time
from pathlib import Path

from .remote import RemoteLipSync, _digest, _probe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--video', required=True)
    parser.add_argument('--audio', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--timeline', choices=('strict', 'audio'), default='strict')
    parser.add_argument('--job-timeout', type=float, default=0,
                        help='Total client deadline in seconds; 0 disables it (default)')
    parser.add_argument('--readiness-timeout', type=float, default=600)
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    report = output.with_suffix('.remote-verification.json')
    if report.exists():
        parser.error('Verification report already exists; choose a new output filename')
    client = RemoteLipSync(args.base_url, api_key=os.environ.get('LIPSYNC_API_KEY', ''),
                           timeline=args.timeline, job_timeout=args.job_timeout,
                           readiness_timeout=args.readiness_timeout)
    started = time.monotonic()
    result = Path(client.lip_sync(args.video, args.audio, str(output)))
    data = {'base_url': client.base_url, 'timeline': args.timeline, 'job_id': client.last_job_id,
            'output': str(result), 'seconds': time.monotonic() - started,
            'video_duration': _probe(result, 'video'), 'audio_duration': _probe(result, 'audio'),
            'sha256': _digest(result), 'manual_quality_review': 'pending: play output and check lip sync, face and audio'}
    report.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
