from pathlib import Path
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader

from model_audio import AudioEncoder
from model_video import VideoEncoder
from fusion import FusionClassifier


class DummyMultimodalDataset(Dataset):
    def __init__(self, root: Path):
        self.audio = list(root.rglob("*.wav"))
        self.video = list(root.rglob("*.mp4"))

    def __len__(self):
        return min(len(self.audio), len(self.video))

    def __getitem__(self, idx):
        # Placeholder tensors (replace with real loaders)
        audio = torch.randn(1, 64, 64)
        video = torch.randn(3, 8, 64, 64)
        label = torch.tensor(0, dtype=torch.long)
        return audio, video, label


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
