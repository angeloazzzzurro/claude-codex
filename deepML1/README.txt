deepML1 — Emotion Classification (PyTorch)
===========================================

Tre sub-progetti indipendenti per classificare emozioni da sorgenti diverse.

STRUTTURA
---------
  images/      → classificazione emozioni da immagini (FER2013, 7 classi)  — COMPLETO
  audio/       → classificazione emozioni da audio   (RAVDESS 16k, 8 classi) — BUG: label hardcoded
  multimodal/  → fusione audio+video                 (RAVDESS full, 8 classi) — STUB: dataset dummy
  docs/        → dataset_links.txt, setup_pytorch.txt

AMBIENTE
--------
  Python 3.9 in ~/projects/claude-codex/deepML1/.venv
  source ~/projects/claude-codex/deepML1/.venv/bin/activate
  pip install torch torchvision torchaudio pandas numpy scikit-learn matplotlib

ESECUZIONE (import relativi: eseguire SEMPRE dalla sottocartella)
---------
  cd ~/projects/claude-codex/deepML1/images    && python train.py
  cd ~/projects/claude-codex/deepML1/audio     && python train.py
  cd ~/projects/claude-codex/deepML1/multimodal && python train.py

BUG CRITICI
-----------
  audio/train.py:23      → label = 0 hardcoded (serve parsing filename RAVDESS)
  multimodal/train.py:11 → DummyMultimodalDataset con tensori random (serve loader reale)

RAVDESS FILENAME FORMAT: 03-01-05-02-01-01-01.wav
  campo[2] (0-based) = emotion (1-8): neutral calm happy sad angry fearful disgusted surprised
  label = int(stem.split('-')[2]) - 1  → range 0-7

DATASET PATHS
-------------
  images/data/fer2013.csv
  audio/data/Audio_Speech_Actors_01-24_16k/
  multimodal/data/RAVDESS/

  Sorgenti: docs/dataset_links.txt
