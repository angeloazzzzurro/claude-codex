import torch
from model import SimpleCNN

model = SimpleCNN()
x = torch.randn(1, 1, 48, 48)  # finta immagine
y = model(x)

print(y)
print(y.shape)
