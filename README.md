# claude-codex

Personal AI/ML workspace — esperimenti con Claude API, computer vision, audio emotion recognition e generazione video su Mac M1.

```
claude-codex/
├── ai-task-manager/   ← Task manager conversazionale (Claude + tool use + SQLite)
├── deepML1/           ← Emotion recognition con PyTorch
│   ├── images/        ← CNN su FER2013 (7 classi)
│   ├── audio/         ← CNN su RAVDESS 16k (8 classi)
│   └── multimodal/    ← Late-fusion audio+video (stub)
├── gaming-agent/      ← Agente Claude per gaming
├── mediapipe/         ← Hand tracking via webcam
├── mockups/           ← SVG mockup UI
├── react-motion/      ← Animazioni React
├── textual/           ← TUI demo (Textual framework)
├── tools/             ← sync_codici_notes.sh
├── video_gen/         ← Text-to-video locale (ModelScope su MPS)
└── web-ui/            ← Simulatore Codex×Claude (HTML/CSS/JS)
```

---

## ai-task-manager

Task manager CLI conversazionale: parla in italiano, gestisce task via tool use Claude, persistenza SQLite con storico conversazione.

```bash
cd ai-task-manager
python -m agent.agent
```

**Features:**
- Tool use: `add_task`, `list_tasks`, `update_task`, `delete_task`
- Storico conversazione persistente su SQLite
- Trim automatico history (ultimi 20 turni)
- Error handling con MAX_STEPS = 10
- Priorità: 🔴 alta / 🟡 media / 🟢 bassa

---

## deepML1 — Emotion Recognition

**Ambiente:** Python 3.9 · PyTorch · `.venv` dedicato

```bash
source deepML1/.venv/bin/activate
```

### images — FER2013 (facial expressions)

| Dataset | Classi | Input |
|---------|--------|-------|
| FER2013 | 7 (angry, disgust, fear, happy, neutral, sad, surprise) | 48×48 grayscale |

```bash
cd deepML1/images && python train.py
```

### audio — RAVDESS (speech emotion)

| Dataset | Classi | Input |
|---------|--------|-------|
| RAVDESS | 8 (neutral, calm, happy, sad, angry, fearful, disgusted, surprised) | MFCC 16kHz |

```bash
cd deepML1/audio && python train.py
```

**RAVDESS filename format:** `03-01-05-02-01-01-01.wav` → campo `[2]` = emozione (01–08)

### multimodal — Late fusion audio+video

Combina i due modelli con late fusion. In sviluppo.

```bash
cd deepML1/multimodal && python train.py
```

---

## video_gen — Text-to-Video locale

Genera video da testo usando ModelScope (`damo-vilab/text-to-video-ms-1.7b`) su Apple Silicon MPS. Prima esecuzione scarica ~3.5 GB.

```bash
cd video_gen
python generate.py --prompt "ocean waves at sunset" --frames 24 --fps 8
python generate.py --prompt "a cat walking in the garden" --out outputs/cat.mp4
```

| Flag | Default | Descrizione |
|------|---------|-------------|
| `--prompt` / `-p` | obbligatorio | Descrizione in inglese |
| `--frames` / `-f` | 16 | Numero di frame (max consigliato 24) |
| `--fps` | 8 | Frame per secondo |
| `--steps` / `-s` | 25 | Inference steps (↑ qualità, ↓ velocità) |
| `--out` / `-o` | `outputs/output.mp4` | File di output (`.mp4` o `.gif`) |

---

## mediapipe — Hand Tracking

Demo webcam hand tracking in tempo reale.

```bash
mediapipedemo1   # alias → attiva ~/.venv, lancia demo
```

---

## textual — TUI Demo

```bash
source ~/.venv/bin/activate
cd textual
python app1.py              # run
textual run --dev app1.py   # dev mode con hot reload
```

---

## web-ui — Simulatore Codex×Claude

Interfaccia web statica che simula l'interazione tra Codex e Claude.

```
web-ui/
├── index.html
├── styles.css
└── app.js
```

Apri `index.html` direttamente nel browser.

---

## Environment

| venv | Python | Progetti |
|------|--------|----------|
| `deepML1/.venv` | 3.9 | deepML1 |
| `~/.venv` | 3.12 | mediapipe, textual, tools |

**Datasets:**
- FER2013 → `deepML1/images/data/fer2013.csv` — [zenodo.org/records/11063852](https://zenodo.org/records/11063852)
- RAVDESS → `deepML1/audio/data/Audio_Speech_Actors_01-24_16k/` — [zenodo.org/records/1188976](https://zenodo.org/records/1188976)
