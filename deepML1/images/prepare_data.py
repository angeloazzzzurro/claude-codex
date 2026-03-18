from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


class FER2013Dataset(Dataset):
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        pixels = np.fromstring(row["pixels"], sep=" ", dtype=np.float32)
        img = pixels.reshape(48, 48) / 255.0
        label = int(row["emotion"])
        x = torch.tensor(img).unsqueeze(0)  # [1, 48, 48]
        y = torch.tensor(label, dtype=torch.long)
        return x, y


def main():
    data_dir = Path(__file__).parent / "data"
    csv_path = data_dir / "fer2013.csv"
    if not csv_path.exists():
        raise FileNotFoundError("Place fer2013.csv in images/data/")
    ds = FER2013Dataset(str(csv_path))
    print("Samples:", len(ds))
    x, y = ds[0]
    print("Sample shape:", x.shape, "label:", y.item())


if __name__ == "__main__":
    main()
