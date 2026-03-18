import torch
from torch import nn


class FusionClassifier(nn.Module):
    def __init__(self, in_dim: int = 256, num_classes: int = 8):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, audio_emb: torch.Tensor, video_emb: torch.Tensor) -> torch.Tensor:
        x = torch.cat([audio_emb, video_emb], dim=1)
        return self.fc(x)
