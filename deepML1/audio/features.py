import torch
import torchaudio


def mel_spectrogram(waveform: torch.Tensor, sample_rate: int = 16000) -> torch.Tensor:
    transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=sample_rate,
        n_fft=1024,
        hop_length=256,
        n_mels=64,
    )
    mel = transform(waveform)
    return torchaudio.functional.amplitude_to_DB(mel, multiplier=10.0, amin=1e-10, db_multiplier=0.0)
