images/ — Image Emotion Classification (FER2013)
=================================================

STATUS: COMPLETO (bug minore: np.fromstring → np.frombuffer)

FILE
----
  prepare_data.py  → FER2013Dataset (torch.utils.data.Dataset)
                     Legge data/fer2013.csv, reshape 48×48, normalizza [0,1]
  model.py         → SimpleCNN: Conv2d(1→32) → MaxPool → Conv2d(32→64) → MaxPool → FC(7)
  train.py         → Training: 90/10 split, batch=64, lr=1e-3, epochs=3, Adam, CrossEntropyLoss
  test_model.py    → Sanity check: dummy tensor (1,1,48,48) → verifica output shape

PIPELINE
--------
  prepare_data.py → FER2013Dataset → DataLoader
  model.py        → SimpleCNN
  train.py        → importa entrambi, esegue training + eval

INPUT/OUTPUT MODELLO
--------------------
  Input : (batch, 1, 48, 48)  — immagine grayscale 48×48 normalizzata
  Output: (batch, 7)           — logits per 7 emozioni

EMOZIONI (indici 0-6)
---------------------
  0=Angry 1=Disgust 2=Fear 3=Happy 4=Sad 5=Surprise 6=Neutral

DATASET
-------
  data/fer2013.csv
  Colonne: emotion (int 0-6), pixels (stringa spazio-separata), Usage (Training/PublicTest/PrivateTest)
  Download: https://zenodo.org/records/11063852

ESECUZIONE
----------
  source ~/projects/claude-codex/deepML1/.venv/bin/activate
  cd ~/projects/claude-codex/deepML1/images
  python train.py
