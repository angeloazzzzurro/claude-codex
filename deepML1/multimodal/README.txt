multimodal/ — Audio+Video Emotion Classification (RAVDESS)
===========================================================

STATUS: STUB — DummyMultimodalDataset con tensori random, nessun dato reale

FILE
----
  prepare_data.py  → Enumera .wav e .mp4 da data/RAVDESS/
                     Restituisce (audio_files[], video_files[])
  model_audio.py   → AudioEncoder
                     Conv2d(1→32)+ReLU+MaxPool → Conv2d(32→64)+ReLU+AdaptiveAvgPool2d(4,4)
                     → FC(64*4*4, 128) → embedding 128-dim
  model_video.py   → VideoEncoder
                     Conv3d(3→32)+ReLU+MaxPool → Conv3d(32→64)+ReLU+AdaptiveAvgPool3d(2,4,4)
                     → FC(64*2*4*4, 128) → embedding 128-dim
  fusion.py        → FusionClassifier
                     Input: cat([emb_audio(128), emb_video(128)]) → (256,)
                     FC(256,128)+ReLU → FC(128,8) → logits (8 classi)
  train.py         → Orchestrazione 3 modelli + late fusion
                     🔴 RIGHE 11-24: DummyMultimodalDataset ← DA SOSTITUIRE

DATA FLOW
---------
  Audio  .wav  → torchaudio.load() → MelSpectrogram → (1, 64, 64)  → AudioEncoder  → emb_a (128,)
                                                                                             ↓ cat
  Video  .mp4  → torchvision.io.read_video() → frame sampling → (3, 8, 64, 64) → VideoEncoder → emb_v (128,)
                                                                                              ↓
                                                                              FusionClassifier → logits (8,)

INPUT SHAPES ATTESI
-------------------
  AudioEncoder  input : (batch, 1, 64, 64)
  VideoEncoder  input : (batch, 3, 8, 64, 64)   — 3 canali RGB, 8 frame, 64×64
  FusionClassifier input: (batch, 256)

COSA SERVE PER COMPLETARE
--------------------------
  1. Real dataset loader (sostituisce DummyMultimodalDataset):
     - Audio: torchaudio.load(path) → Mel-spectrogram 64×64
     - Video: torchvision.io.read_video(path) → campiona 8 frame uniformi → resize 64×64
     - Label: parsing filename RAVDESS (campo[2], stesso schema di audio/)

  2. Sincronizzare gli actor in prepare_data.py:
     - Abbinare .wav e .mp4 dello stesso actor/take per avere coppie allineate

  3. Aggiungere validation split + eval metrics

RAVDESS LABEL PARSING (come in audio/)
--------------------------------------
  emotion_id = int(Path(filepath).stem.split('-')[2])
  label = emotion_id - 1  # range 0-7

DATASET
-------
  data/RAVDESS/
  Contiene sia audio (.wav) che video (.mp4)
  Download: https://zenodo.org/records/1188976

ESECUZIONE (attualmente gira con dati dummy)
-------------------------------------------
  source ~/projects/claude-codex/deepML1/.venv/bin/activate
  cd ~/projects/claude-codex/deepML1/multimodal
  python train.py
