#!/usr/bin/env python3
"""
Text-to-video locale su Mac M1 via MPS
Modello: ModelScope damo-vilab/text-to-video-ms-1.7b
Prima esecuzione: scarica ~3.5GB in ~/.cache/huggingface/

Uso:
    python generate.py --prompt "a cat walking in the garden"
    python generate.py --prompt "ocean waves at sunset" --frames 24 --fps 8
    python generate.py --prompt "..." --out outputs/myvideo.mp4
"""
import argparse
import sys
from pathlib import Path

import torch
import numpy as np
import imageio


def load_pipeline():
    from diffusers import DiffusionPipeline

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}")
    print("Carico il modello (prima esecuzione: scarica ~3.5GB)...")

    pipe = DiffusionPipeline.from_pretrained(
        "damo-vilab/text-to-video-ms-1.7b",
        torch_dtype=torch.float16,
    )
    pipe = pipe.to(device)
    pipe.enable_attention_slicing()
    return pipe, device


def generate(pipe, prompt: str, num_frames: int, num_steps: int):
    print(f"Genero: \"{prompt}\"")
    print(f"Frames: {num_frames}, Steps: {num_steps}")

    output = pipe(
        prompt,
        num_frames=num_frames,
        num_inference_steps=num_steps,
    )
    return output.frames[0]  # lista di PIL Image


def save_video(frames, out_path: Path, fps: int):
    frames_np = [np.array(f) for f in frames]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(str(out_path), frames_np, fps=fps)
    print(f"Salvato: {out_path.resolve()}")
    print(f"Durata: {len(frames_np) / fps:.1f}s  ({len(frames_np)} frames @ {fps}fps)")


def main():
    parser = argparse.ArgumentParser(description="Genera video da testo (locale, gratis)")
    parser.add_argument("--prompt", "-p", required=True, help="Descrizione del video in inglese")
    parser.add_argument("--out", "-o", default="outputs/output.mp4", help="File di output (.mp4 o .gif)")
    parser.add_argument("--frames", "-f", type=int, default=16,
                        help="Numero di frame (default 16, max consigliato 24)")
    parser.add_argument("--fps", type=int, default=8, help="Frame per secondo (default 8)")
    parser.add_argument("--steps", "-s", type=int, default=25,
                        help="Inference steps: più alto = migliore qualità ma più lento (default 25)")
    args = parser.parse_args()

    out_path = Path(args.out)
    if out_path.suffix not in (".mp4", ".gif"):
        print("Errore: --out deve terminare con .mp4 o .gif", file=sys.stderr)
        sys.exit(1)

    pipe, _ = load_pipeline()
    frames = generate(pipe, args.prompt, args.frames, args.steps)
    save_video(frames, out_path, args.fps)


if __name__ == "__main__":
    main()
