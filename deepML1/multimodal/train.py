from pathlib import Path
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import Dataset, DataLoader
import torchaudio
import torchaudio.transforms as T
import torchvision.io

from model_audio import AudioEncoder
from model_video import VideoEncoder
from fusion import FusionClassifier

N_MELS = 64
N_FRAMES = 8
IMG_SIZE = 64


class RAVDESSMultimodalDataset(Dataset):
    def __init__(self, root: Path):
        wavs = {p.stem: p for p in root.rglob("*.wav")}
        mp4s = {p.stem: p for p in root.rglob("*.mp4")}
        common = sorted(set(wavs) & set(mp4s))
        self.pairs = [(wavs[s], mp4s[s]) for s in common]

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        wav_path, mp4_path = self.pairs[idx]

        # Label: RAVDESS filename field[2] = emotion (1-8) → 0-7
        emotion_id = int(wav_path.stem.split('-')[2])
        label = emotion_id - 1

        # Audio → mel spectrogram (1, N_MELS, IMG_SIZE)
        waveform, sr = torchaudio.load(wav_path)
        mel_transform = T.MelSpectrogram(sample_rate=sr, n_fft=1024, n_mels=N_MELS, hop_length=512)
        mel = mel_transform(waveform).mean(0, keepdim=True)  # (1, N_MELS, time)
        mel = F.interpolate(mel.unsqueeze(0), size=(N_MELS, IMG_SIZE), mode='bilinear', align_corners=False).squeeze(0)

        # Video → sampled frames (3, N_FRAMES, IMG_SIZE, IMG_SIZE)
        frames, _, _ = torchvision.io.read_video(str(mp4_path), pts_unit='sec', output_format='TCHW')
        frames = frames.float() / 255.0  # (T, C, H, W)
        T_total = frames.shape[0]
        indices = torch.linspace(0, T_total - 1, N_FRAMES).long()
        frames = frames[indices]  # (N_FRAMES, C, H, W)
        frames = frames.permute(1, 0, 2, 3)  # (C, N_FRAMES, H, W)
        C, Tf, H, W = frames.shape
        frames_2d = frames.reshape(C * Tf, 1, H, W)
        frames_2d = F.interpolate(frames_2d, size=(IMG_SIZE, IMG_SIZE), mode='bilinear', align_corners=False)
        frames = frames_2d.reshape(C, Tf, IMG_SIZE, IMG_SIZE)[:3]

        return mel, frames, torch.tensor(label, dtype=torch.long)


def main():
    data_dir = Path(__file__).parent / "data" / "RAVDESS"
    if not data_dir.exists():
        raise FileNotFoundError("Place RAVDESS dataset in multimodal/data/")

    dataset = DummyMultimodalDataset(data_dir)
    loader = DataLoader(dataset, batch_size=4, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    audio_enc = AudioEncoder().to(device)
    video_enc = VideoEncoder().to(device)
    fusion = FusionClassifier().to(device)

    params = list(audio_enc.parameters()) + list(video_enc.parameters()) + list(fusion.parameters())
    optimizer = torch.optim.Adam(params, lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(1):
        for audio, video, label in loader:
            audio, video, label = audio.to(device), video.to(device), label.to(device)
            optimizer.zero_grad()
            a_emb = audio_enc(audio)
            v_emb = video_enc(video)
            logits = fusion(a_emb, v_emb)
            loss = criterion(logits, label)
            loss.backward()
            optimizer.step()
        print("Epoch", epoch + 1, "done")


if __name__ == "__main__":
    main()
