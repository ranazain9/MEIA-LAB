import asyncio
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock

from backend.agents.asr.processors import transcribe_audio


class FakeASRModel:
    def __call__(self, audio_input, return_timestamps=True, generate_kwargs=None):
        return {
            "text": "Revenue grew 12 percent.",
            "chunks": [
                {"text": "Revenue grew 12 percent.", "timestamp": (0.0, 2.5)}
            ],
        }


class ASRProcessorsTests(unittest.TestCase):
    def test_transcribe_audio_parses_transformers_pipeline_output(self):
        audio_input = {"array": [0.0, 0.1, 0.0], "sampling_rate": 16000}
        segments = asyncio.run(transcribe_audio(audio_input, FakeASRModel()))

        self.assertEqual(len(segments), 1)
        self.assertIn("Revenue", segments[0].text)
        self.assertEqual(segments[0].start, 0.0)
        self.assertEqual(segments[0].end, 2.5)

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    @patch("os.path.getsize", return_value=1024)   # well below 25 MB limit
    @patch("os.path.exists", return_value=True)
    def test_transcribe_audio_uses_groq_client(self, mock_exists, mock_size, mock_file):
        """transcribe_audio should route small files through groq_client.transcription."""

        # Build a mock segment
        mock_segment = MagicMock()
        mock_segment.text = "Gross margin expanded."
        mock_segment.start = 1.0
        mock_segment.end = 3.5
        mock_segment.avg_logprob = -0.05

        mock_response = MagicMock()
        mock_response.segments = [mock_segment]

        # Patch the global groq_client used inside processors.py
        with patch("backend.agents.asr.processors.groq_client") as mock_gc:
            mock_gc.transcription = AsyncMock(return_value=mock_response)
            segments = asyncio.run(transcribe_audio("fake_audio.wav", MagicMock()))

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "Gross margin expanded.")
        self.assertEqual(segments[0].start, 1.0)
        self.assertEqual(segments[0].end, 3.5)
        self.assertEqual(segments[0].confidence, -0.05)


if __name__ == "__main__":
    unittest.main()
