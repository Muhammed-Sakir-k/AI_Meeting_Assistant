import os
import logging
import numpy as np
import librosa
import soundfile as sf
from scipy.signal import butter, lfilter
from pydub import AudioSegment

logger = logging.getLogger(__name__)

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
        y_cleaned = librosa.istft(stft_cleaned, hop_length=512)
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
    
    # 1. Load and downsample to 16kHz mono
    y, sr = librosa.load(input_path, sr=16000, mono=True)
    
    if len(y) == 0:
        raise ValueError("Loaded audio file is empty.")
        
    # 2. Highpass filter (> 80 Hz)
    y_hp = highpass_filter(y, cutoff=80.0, fs=sr, order=4)
    
    # 3. Spectral Noise Reduction
    y_clean = spectral_noise_reduction(y_hp, sr)
    
    # 4. Normalization (scale to peak at 0.9 to prevent clipping)
    peak = np.max(np.abs(y_clean))
    if peak > 0:
        y_normalized = y_clean * (0.9 / peak)
    else:
        y_normalized = y_clean
        
    # 5. Write to 16kHz Mono 16-bit WAV
    sf.write(output_path, y_normalized, sr, subtype='PCM_16')
    logger.info(f"Audio preprocessed and saved to {output_path}")
    
    return output_path

def split_audio_into_chunks(audio_path: str, chunk_duration_ms=600000) -> list:
    """
    Splits long audio into chunks (default 10 minutes) for Whisper processing.
    Returns list of paths of chunk files.
    """
    logger.info(f"Checking if audio {audio_path} needs chunking...")
    try:
        audio = AudioSegment.from_file(audio_path)
    except Exception as e:
        logger.warning(f"pydub failed to load audio. Trying librosa: {e}")
        # fallback to soundfile load
        data, sr = sf.read(audio_path)
        # convert to millisecond length
        duration_ms = int(len(data) / sr * 1000)
        audio = None
        
    # If using pydub loaded successfully
    if audio is not None:
        duration_ms = len(audio)
        if duration_ms <= chunk_duration_ms:
            logger.info("Audio duration is less than chunk size, no chunking needed.")
            return [audio_path]
            
        chunks = []
        base_dir = os.path.dirname(audio_path)
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        
        for i in range(0, duration_ms, chunk_duration_ms):
            chunk = audio[i:i+chunk_duration_ms]
            chunk_path = os.path.join(base_dir, f"{base_name}_chunk_{i//chunk_duration_ms}.wav")
            chunk.export(chunk_path, format="wav")
            chunks.append(chunk_path)
            
        logger.info(f"Split audio into {len(chunks)} chunks.")
        return chunks
    else:
        # manual array slice fallback
        # Let's read full info
        y, sr = librosa.load(audio_path, sr=None)
        chunk_samples = int((chunk_duration_ms / 1000) * sr)
        if len(y) <= chunk_samples:
            return [audio_path]
            
        chunks = []
        base_dir = os.path.dirname(audio_path)
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        
        for idx, i in enumerate(range(0, len(y), chunk_samples)):
            chunk_data = y[i:i+chunk_samples]
            chunk_path = os.path.join(base_dir, f"{base_name}_chunk_{idx}.wav")
            sf.write(chunk_path, chunk_data, sr)
            chunks.append(chunk_path)
            
        logger.info(f"Split audio into {len(chunks)} chunks via array slicing.")
        return chunks
