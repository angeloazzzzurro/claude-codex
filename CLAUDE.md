# claude-codex — Agent Navigation Guide

Guida dettagliata per agenti AI. Overview rapida: `~/CLAUDE.md`.

---

## Mappa Completa dei File

```
deepML1/
├── .venv/                              # Python 3.9 venv (NON toccare)
├── README.txt                          # Overview del progetto
├── images/
│   ├── prepare_data.py                 # FER2013Dataset (torch.utils.data.Dataset)
│   ├── model.py                        # SimpleCNN: Conv2d → MaxPool → FC (7 classi)
│   ├── train.py                        # Training loop: 90/10 split, Adam, 3 epoch
│   └── test_model.py                   # Sanity check con dummy tensor (1,1,48,48)
├── audio/
│   ├── prepare_data.py                 # Lister .wav in data/Audio_Speech_Actors_01-24_16k/
│   ├── features.py                     # mel_spectrogram() → torchaudio MelSpectrogram
│   ├── model.py                        # AudioCNN: Conv2d → MaxPool → FC (8 classi)
│   └── train.py                        # RAVDESSDataset + training (🔴 label=0 hardcoded)
├── multimodal/
│   ├── prepare_data.py                 # Elenca .wav + .mp4 da data/RAVDESS/
│   ├── model_audio.py                  # AudioEncoder → emb 128-dim
│   ├── model_video.py                  # VideoEncoder (Conv3d) → emb 128-dim
│   ├── fusion.py                       # FusionClassifier: [128+128] → FC → 8 classi
│   └── train.py                        # 🔴 DummyMultimodalDataset (tensori random)
└── docs/
    ├── dataset_links.txt               # URL download dataset
    └── setup_pytorch.txt               # Istruzioni setup venv

mediapipe/
└── mediapipe_webcam_demo.py            # Hand tracking: legacy API + Tasks API, salva .mp4

textual/
└── app1.py                             # TUI demo: Input + 2 Button + Label

web-ui/
├── index.html                          # Layout simulatore (76 righe)
├── styles.css                          # Design Apple-like (305 righe)
└── app.js                              # Logica 5 scenari + intent detection (400 righe)

tools/
└── sync_codici_notes.sh                # ~/codici.txt → Apple Notes via AppleScript
```

---

## deepML1 — Architettura Dettagliata

### Esecuzione (import relativi, SEMPRE dalla sottocartella)

```bash
source ~/projects/claude-codex/deepML1/.venv/bin/activate

cd ~/projects/claude-codex/deepML1/images    && python train.py
cd ~/projects/claude-codex/deepML1/audio     && python train.py
cd ~/projects/claude-codex/deepML1/multimodal && python train.py
```

### images/ — FER2013 Image Classification

**Pipeline:** `prepare_data.py` → `model.py` → `train.py`

**Dati:**
- Input CSV: `data/fer2013.csv` (colonne: `emotion`, `pixels`, `Usage`)
- Pixel: stringa spazio-separata → `np.fromstring()` (⚠️ usa `np.frombuffer()`)
- Reshape: 48×48, normalizzazione [0,1]
- Split: 90% train / 10% val

**Modello:**
```
Input (1, 48, 48)
→ Conv2d(1→32, k=3) + ReLU + MaxPool2d(2)
→ Conv2d(32→64, k=3) + ReLU + MaxPool2d(2)
→ Flatten → FC(64*10*10, 128) → ReLU → FC(128, 7)
Output: logits (7 classi)
```

**Hyperparams:** batch=64, lr=1e-3, epochs=3, Adam, CrossEntropyLoss

**Status:** ✅ Funzionante. Bug minore: `np.fromstring()` deprecated.

---

### audio/ — RAVDESS Audio Classification

**Pipeline:** `prepare_data.py` → `features.py` → `model.py` → `train.py`

**Dati:**
- Files `.wav` in `data/Audio_Speech_Actors_01-24_16k/` (ricerca ricorsiva)
- Mel-spectrogram: `n_fft=1024, n_mels=64, hop_length=512`
- Shape input modello: `(1, 64, N_frames)`

**Modello:**
```
Input (1, 64, N)
→ Conv2d(1→16, k=3) + ReLU + MaxPool2d(2)
→ Conv2d(16→32, k=3) + ReLU + MaxPool2d(2)
→ AdaptiveAvgPool2d(16,16) → Flatten → FC(32*16*16, 8)
Output: logits (8 classi)
```

**🔴 BUG CRITICO — `audio/train.py` riga 23:**
```python
label = 0  # HARDCODED — DA FIXARE
```

**Fix necessario:**
```python
# Formato filename RAVDESS: 03-01-05-02-01-01-01.wav
# Campo indice 2 (0-based) = emotion (1-8)
emotion_id = int(Path(filepath).stem.split('-')[2])
label = emotion_id - 1  # → 0-7
```

**Emotion map (1-8):** neutral, calm, happy, sad, angry, fearful, disgusted, surprised

---

### multimodal/ — Late-Fusion Audio+Video

**Pipeline:** `prepare_data.py` → `model_audio.py` + `model_video.py` → `fusion.py` → `train.py`

**Architettura:**
```
Audio (1, 64, 64)  → AudioEncoder  → emb_a (128,)
                                            ↓ torch.cat(dim=1)
Video (3, 8, 64, 64) → VideoEncoder → emb_v (128,) → FusionClassifier → logits (8,)
```

**AudioEncoder:**
```
Conv2d(1→32) + ReLU + MaxPool + Conv2d(32→64) + ReLU + AdaptiveAvgPool(4,4) → FC(64*4*4, 128)
```

**VideoEncoder:**
```
Conv3d(3→32) + ReLU + MaxPool + Conv3d(32→64) + ReLU + AdaptiveAvgPool3d(2,4,4) → FC(64*2*4*4, 128)
```

**FusionClassifier:** FC(256, 128) → ReLU → FC(128, 8)

**🔴 BUG CRITICO — `multimodal/train.py` righe 11-24:**
```python
class DummyMultimodalDataset(Dataset):  # DA SOSTITUIRE
    audio = torch.randn(1, 64, 64)       # ← random
    video = torch.randn(3, 8, 64, 64)    # ← random
    label = 0                            # ← hardcoded
```

**Fix necessario:** Loader reale con `torchaudio.load()` + Mel-spectrogram + `torchvision.io.read_video()` + frame sampling + RAVDESS label parsing (uguale ad audio/).

---

## web-ui/ — Simulatore Codex×Claude

**Apertura:** `open ~/projects/claude-codex/web-ui/index.html` (browser)

**5 Scenari disponibili in `app.js`:**

| ID | Tema | Keywords trigger |
|----|------|-----------------|
| `prodotto-ux` | Design/UX | ux, ui, design, utente, interfaccia |
| `scalabilita` | Operations | scalabilita, processo, automazione, efficienza |
| `marketing-gtm` | Go-to-market | marketing, gtm, lancio, campagna, brand |
| `tech-arch` | Technical decisions | architettura, tech, stack, infrastruttura |
| `vendite-business` | Sales/pricing | vendite, sales, prezzo, cliente, revenue |

**Struttura scenario JS:**
```javascript
{ id, titolo,
  dialogo: [{who: "Claude"|"Codex", text}...],
  ragionamento: [{who, text}...],
  opzioni: [{titolo, testo, rate: Number}...]  // rate = tasso successo %
}
```

**Funzioni chiave (`app.js`):**
- `simulate(options)` — orchestratore principale con timing sequenziale
- `handleUserPrompt()` — parse input + `scenarioFromPrompt()` + avvia simulate
- `scenarioFromPrompt(prompt)` — intent detection via keyword matching
- `addBubble(container, who, text)` — render chat bubble
- `addCard(opzione)` — render option card con tasso successo
- Filtro opzioni: `minRate` (input slider), sort desc, max 2 mostrate

---

## mediapipe/ — Hand Tracking

**File:** `mediapipe_webcam_demo.py`

**Funzioni:**
- `run_legacy_api(cap, output_path, fps)` — MediaPipe solutions.hands
- `run_tasks_api(cap, output_path, fps)` — MediaPipe vision.HandLandmarker
- `draw_task_landmarks(frame, hand_landmarks_list)` — disegna skeleton
- `ensure_writer(writer, frame, output_path, fps)` — lazy VideoWriter init

**Output:** `~/Videos/mediapipe_demos/hands_YYYYMMDD_HHMMSS.mp4`

**Tasto uscita:** `Q`

**venv:** `~/.venv` — `pip install mediapipe opencv-python`

---

## textual/ — TUI App

**File:** `app1.py` — Form interattivo con Textual framework

**Widget tree:** Header → Vertical[Label, Input, Horizontal[Button×2], Label] → Footer

**Handlers:**
- Button "Saluta" (`id="invia"`) → mostra `f"Ciao, {nome}!"`
- Button "Cancella" (`id="reset"`) → pulisce input e output

**venv:** `~/.venv` — `pip install textual`

---

## tools/ — Automation

**File:** `sync_codici_notes.sh`

**Flusso:** `~/codici.txt` → escape HTML → AppleScript → nota "codici" in Apple Notes ("On My Mac")

**Dipendenze:** macOS, `osascript`, Python 3

---

## Pattern Comuni nel Codebase

1. **Import relativi Python** — tutti gli script usano `from model import ...` → CWD deve essere la sottocartella
2. **`pathlib.Path(__file__).parent`** — per path assoluti cross-platform
3. **PyTorch standard:** `Dataset.__getitem__` + `DataLoader` + `nn.Module.forward()` + `Adam` + `CrossEntropyLoss`
4. **Nessun `requirements.txt`** — dipendenze solo documentate (in CLAUDE.md e setup_pytorch.txt)
5. **Nessun logging framework** — solo `print()` nei training loop

---

## Dipendenze Complete

```
deepML1/.venv (Python 3.9):
  torch torchvision torchaudio
  pandas numpy scikit-learn matplotlib

~/.venv (Python 3.12):
  mediapipe opencv-python
  textual

Sistema (macOS):
  osascript (AppleScript) — per sync Notes
  gh 2.86.0 — GitHub CLI
```
