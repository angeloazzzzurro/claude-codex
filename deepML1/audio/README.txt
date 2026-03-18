audio/ — Audio Emotion Classification (RAVDESS 16k)
====================================================

STATUS: INCOMPLETO — label hardcoded a 0 in train.py:23

FILE
----
  prepare_data.py  → Ricerca ricorsiva .wav in data/Audio_Speech_Actors_01-24_16k/
                     Restituisce lista di path assoluti
  features.py      → mel_spectrogram(waveform, sr) → MelSpectrogram
                     Params: n_fft=1024, n_mels=64, hop_length=512
                     Output: tensor (1, 64, N_frames)
  model.py         → AudioCNN: Conv2d(1→16) → MaxPool → Conv2d(16→32) → MaxPool
                     → AdaptiveAvgPool2d(16,16) → FC(32*16*16, 8)
  train.py         → RAVDESSDataset + training loop (1 epoch)
                     🔴 RIGA 23: label = 0  ← DA FIXARE

BUG CRITICO — train.py riga 23
-------------------------------
  Attuale:  label = 0
  Fix:      emotion_id = int(Path(filepath).stem.split('-')[2])
            label = emotion_id - 1  # → range 0-7

RAVDESS FILENAME FORMAT
-----------------------
  Esempio: 03-01-05-02-01-01-01.wav
  Campi (separati da '-', 0-indexed):
    [0] modality    03=audio-only
    [1] vocal_channel 01=speech
    [2] emotion     01-08 (vedi sotto)  ← USARE QUESTO
    [3] intensity   01=normal 02=strong
    [4] statement   01="Kids are talking..." 02="Dogs are sitting..."
    [5] repetition  01 o 02
    [6] actor       01-24

EMOTION MAP (campo[2] → label)
-------------------------------
  01=neutral (0)  02=calm (1)  03=happy (2)  04=sad (3)
  05=angry (4)    06=fearful (5) 07=disgusted (6) 08=surprised (7)

INPUT/OUTPUT MODELLO
--------------------
  Input : (batch, 1, 64, N_frames)  — Mel-spectrogram
  Output: (batch, 8)                 — logits per 8 emozioni

DATASET
-------
  data/Audio_Speech_Actors_01-24_16k/
  Struttura: Actor_01/ Actor_02/ ... Actor_24/ (ognuno con file .wav)
  Download: https://zenodo.org/records/11063852

ESECUZIONE
----------
  source ~/projects/claude-codex/deepML1/.venv/bin/activate
  cd ~/projects/claude-codex/deepML1/audio
  python train.py
