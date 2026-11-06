import os
import sys
import tempfile
import unittest

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.preprocessing.audio_processor import (
    PREPROCESS_CHUNK_SECONDS,
    preprocess_audio,
    split_audio_into_chunks,
)


class TestAudioProcessing(unittest.TestCase):
    def test_preprocess_audio_normalizes_and_preserves_duration(self):
        sample_rate = 16000
        samples = 0.2 * np.sin(
            2 * np.pi * 440 * np.arange(sample_rate * (PREPROCESS_CHUNK_SECONDS + 1)) / sample_rate
        ).astype(np.float32)

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "meeting.wav")
            sf.write(input_path, samples, sample_rate)

            output_path = preprocess_audio(input_path, temp_dir)

            with sf.SoundFile(output_path) as processed:
                self.assertEqual(processed.samplerate, sample_rate)
                self.assertEqual(len(processed), len(samples))
                self.assertAlmostEqual(float(np.max(np.abs(processed.read(dtype="float32")))), 0.9, places=2)
            self.assertFalse(os.path.exists(f"{output_path}.tmp.wav"))

    def test_split_audio_reads_and_writes_chunks_incrementally(self):
        sample_rate = 16000
        samples = np.zeros(sample_rate * 2, dtype=np.float32)

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "meeting.wav")
            sf.write(input_path, samples, sample_rate)

            chunks = split_audio_into_chunks(input_path, chunk_duration_ms=1000)

            self.assertEqual(len(chunks), 2)
            self.assertEqual([len(sf.SoundFile(path)) for path in chunks], [sample_rate, sample_rate])


if __name__ == "__main__":
    unittest.main()
