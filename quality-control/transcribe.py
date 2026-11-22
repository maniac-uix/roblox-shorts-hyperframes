#!/usr/bin/env python3
"""transcribe.py — transcribe an audio file with local faster-whisper (tiny).

Uses the venv at .cache-tmp/venv-transcribe (faster-whisper + ctranslate2).
The model ("tiny", int8, CPU) is downloaded from Hugging Face on first use
into the default faster-whisper cache. No paid service, no audio leaves the VM.

Usage:
  .cache-tmp/venv-transcribe/bin/python quality-control/transcribe.py \
      --input voiceover/narration.mp3 --output <transcript.json> [--language en]

Output JSON: {"language": "en", "words": [{"word", "start", "end", "prob"}]}
Decoding goes through ffmpeg (16 kHz mono WAV) so no PyAV version is needed.
"""
import argparse
import json
import struct
import subprocess
import sys
import wave
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = PROJECT_DIR / ".cache-tmp" / "tmp"


def decode_to_pcm(audio_path: Path) -> "np.ndarray":
    import numpy as np

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    wav_path = TMP_DIR / "transcribe-input.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(audio_path),
         "-ac", "1", "-ar", "16000", str(wav_path)],
        check=True,
    )
    with wave.open(str(wav_path)) as w:
        n = w.getnframes()
        samples = struct.unpack("<%dh" % n, w.readframes(n))
    return np.array(samples, dtype=np.float32) / 32768.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--language", default="en")
    args = ap.parse_args()

    from faster_whisper import WhisperModel

    pcm = decode_to_pcm(Path(args.input))
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        pcm, language=args.language, word_timestamps=True, vad_filter=False
    )
    words = []
    for seg in segments:
        for wd in (seg.words or []):
            words.append({
                "word": wd.word.strip(),
                "start": round(wd.start, 2),
                "end": round(wd.end, 2),
                "prob": round(wd.probability, 2),
            })
        print(f"[{seg.start:.2f}-{seg.end:.2f}] {seg.text.strip()}")
    result = {"language": info.language, "words": words}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(args.output, "w"), indent=1)
    print("WORDS:", " ".join(w["word"] for w in words))
    print("saved", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
