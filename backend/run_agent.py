import argparse
import asyncio
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.service import run_analysis


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MEIA orchestrator agent")
    parser.add_argument("--audio-path", default="sample.wav")
    parser.add_argument("--slides-path", default="sample.pdf")
    parser.add_argument("--ticker", default="AMD")
    args = parser.parse_args()
    result = asyncio.run(run_analysis(args.audio_path, args.slides_path, args.ticker))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
