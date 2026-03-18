from pathlib import Path
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
import torchaudio

from features import mel_spectrogram
from model import AudioCNN


class RAVDESSDataset(Dataset):
    def __init__(self, root: Path):
        self.files = sorted([p for p in root.rglob("*.wav")])

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        path = self.files[idx]
        waveform, sr = torchaudio.load(path)
        mel = mel_spectrogram(waveform, sample_rate=sr)
        # Placeholder label: parse from filename if needed
        label = 0
        x = mel.unsqueeze(0)  # [1, n_mels, time]
        y = torch.tensor(label, dtype=torch.long)
        return x, y


def main():
    data_dir = Path(__file__).parent / "data" / "Audio_Speech_Actors_01-24_16k"
    if not data_dir.exists():
        raise FileNotFoundError("Place RAVDESS 16k folder in audio/data/")

    dataset = RAVDESSDataset(data_dir)
    loader = DataLoader(dataset, batch_size=8, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AudioCNN(num_classes=8).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    for epoch in range(1):
        model.train()
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
        print("Epoch", epoch + 1, "done")


if __name__ == "__main__":
    main()
