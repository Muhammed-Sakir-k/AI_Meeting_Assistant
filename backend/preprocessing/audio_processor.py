import os
import logging
import numpy as np
import librosa
import soundfile as sf
from scipy.signal import butter, lfilter

logger = logging.getLogger(__name__)
PREPROCESS_CHUNK_SECONDS = 30

def butter_highpass(cutoff, fs, order=5):
    """Generates highpass filter coefficients."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def highpass_filter(data, cutoff, fs, order=5):
    """Applies a highpass filter to remove low-frequency hum/noise."""
    b, a = butter_highpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def spectral_noise_reduction(y, sr, noise_threshold=0.02):
    """
    Performs spectral subtraction for noise reduction.
    Estimates the noise spectrum from low-energy frames and subtracts it.
    """
    try:
        # Compute Short-Time Fourier Transform (STFT)
        stft = librosa.stft(y, n_fft=2048, hop_length=512)
        stft_magnitude, stft_phase = librosa.magphase(stft)
        
        # Estimate noise spectrum: find frames with low energy
        frame_energies = np.sum(stft_magnitude, axis=0)
        low_energy_indices = np.where(frame_energies < np.percentile(frame_energies, 20))[0]
        
        if len(low_energy_indices) > 0:
            noise_spectrum = np.mean(stft_magnitude[:, low_energy_indices], axis=1, keepdims=True)
        else:
            noise_spectrum = np.mean(stft_magnitude[:, :10], axis=1, keepdims=True)  # fallback
            
        # Subtract noise spectrum (spectral subtraction)
        alpha = 1.5
        subtracted_magnitude = stft_magnitude - alpha * noise_spectrum
        subtracted_magnitude = np.maximum(subtracted_magnitude, 0.0)
        
        # Reconstruct and inverse STFT
        stft_cleaned = subtracted_magnitude * stft_phase
        y_cleaned = librosa.istft(stft_cleaned, hop_length=512, length=len(y))
        return y_cleaned
    except Exception as e:
        logger.warning(f"Spectral noise reduction failed: {e}. Returning original audio.")
        return y

def preprocess_audio(input_path: str, output_dir: str) -> str:
    """
    Main preprocessing pipeline:
    1. Loads audio (any format) and downsamples to 16kHz mono.
    2. Highpass filter to remove low-frequency hums (< 80Hz).
    3. Spectral subtraction noise reduction.
    4. Level normalization.
    5. Saves as a Whisper-friendly 16kHz mono 16-bit WAV.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input audio file not found: {input_path}")
        
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_preprocessed.wav")
    
    logger.info(f"Starting preprocessing for {input_path}")
    
    # 1. Read the duration without loading the complete recording into memory.
    duration = librosa.get_duration(path=input_path)
    if duration <= 0:
        raise ValueError("Loaded audio file is empty.")

    working_path = f"{output_path}.tmp.wav"
    peak = 0.0
    try:
        # Stage processed audio as float so normalization can preserve the original
        # whole-recording peak without retaining the audio in memory.
        with sf.SoundFile(
            working_path,
            mode="w",
            samplerate=16000,
            channels=1,
            subtype="FLOAT",
        ) as working_file:
            offset = 0.0
            while offset < duration:
                segment_duration = min(PREPROCESS_CHUNK_SECONDS, duration - offset)
                y, sr = librosa.load(
                    input_path,
                    sr=16000,
                    mono=True,
                    offset=offset,
                    duration=segment_duration,
                )
                if len(y) == 0:
                    break

                y_hp = highpass_filter(y, cutoff=80.0, fs=sr, order=4)
                y_clean = spectral_noise_reduction(y_hp, sr)
                if len(y_clean):
                    peak = max(peak, float(np.max(np.abs(y_clean))))
                    working_file.write(y_clean)
                offset += segment_duration

        if peak == 0.0:
            raise ValueError("Audio contains no usable signal.")

        scale = 0.9 / peak
        with sf.SoundFile(working_path) as working_file, sf.SoundFile(
            output_path,
            mode="w",
            samplerate=16000,
            channels=1,
            subtype="PCM_16",
        ) as output_file:
            while True:
                samples = working_file.read(16000 * PREPROCESS_CHUNK_SECONDS, dtype="float32")
                if len(samples) == 0:
                    break
                output_file.write(samples * scale)
    finally:
        if os.path.exists(working_path):
            os.remove(working_path)

    logger.info(f"Audio preprocessed and saved to {output_path}")
    
    return output_path

def split_audio_into_chunks(audio_path: str, chunk_duration_ms=600000) -> list:
    """
    Splits long audio into chunks (default 10 minutes) for Whisper processing.
    Returns list of paths of chunk files.
    """
    logger.info(f"Checking if audio {audio_path} needs chunking...")
    try:
        with sf.SoundFile(audio_path) as audio:
            chunk_frames = int(chunk_duration_ms * audio.samplerate / 1000)
            if len(audio) <= chunk_frames:
                logger.info("Audio duration is less than chunk size, no chunking needed.")
                return [audio_path]

            chunks = []
            base_dir = os.path.dirname(audio_path)
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            subtype = audio.subtype

            for idx, start_frame in enumerate(range(0, len(audio), chunk_frames)):
                audio.seek(start_frame)
                chunk_data = audio.read(chunk_frames, dtype="float32", always_2d=True)
                chunk_path = os.path.join(base_dir, f"{base_name}_chunk_{idx}.wav")
                sf.write(chunk_path, chunk_data, audio.samplerate, subtype=subtype)
                chunks.append(chunk_path)
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Unable to read preprocessed WAV audio '{audio_path}': {e}") from e

    logger.info(f"Split audio into {len(chunks)} chunks.")
    return chunks
