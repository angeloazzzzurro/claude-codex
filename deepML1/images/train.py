from pathlib import Path
import torch
from torch import nn
from torch.utils.data import DataLoader, random_split

from prepare_data import FER2013Dataset
from model import SimpleCNN


def main():
    data_dir = Path(__file__).parent / "data"
    csv_path = data_dir / "fer2013.csv"
    dataset = FER2013Dataset(str(csv_path))

    n_total = len(dataset)
    n_train = int(n_total * 0.9)
    n_val = n_total - n_train
    train_ds, val_ds = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=64)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SimpleCNN(num_classes=7).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    for epoch in range(3):
        model.train()
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                logits = model(x)
                preds = logits.argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.numel()
        acc = correct / max(total, 1)
        print(f"Epoch {epoch+1}: val acc {acc:.3f}")


if __name__ == "__main__":
    main()
