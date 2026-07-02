import asyncio
import unittest

from backend.agents.asr.processors import transcribe_audio


class FakeASRModel:
    def __call__(self, audio_path, return_timestamps=True, chunk_length_s=30, generate_kwargs=None):
        return {
            "text": "Revenue grew 12 percent.",
            "chunks": [
                {"text": "Revenue grew 12 percent.", "timestamp": (0.0, 2.5)}
            ],
        }


class ASRProcessorsTests(unittest.TestCase):
    def test_transcribe_audio_parses_transformers_pipeline_output(self):
        segments = asyncio.run(transcribe_audio("sample.wav", FakeASRModel()))

        self.assertEqual(len(segments), 1)
        self.assertIn("Revenue", segments[0].text)
        self.assertEqual(segments[0].start, 0.0)
        self.assertEqual(segments[0].end, 2.5)


if __name__ == "__main__":
    unittest.main()
