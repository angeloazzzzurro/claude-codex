from pathlib import Path


def list_audio_files(root: Path):
    return sorted([p for p in root.rglob("*.wav")])


def main():
    data_dir = Path(__file__).parent / "data"
    root = data_dir / "Audio_Speech_Actors_01-24_16k"
    if not root.exists():
        raise FileNotFoundError("Place RAVDESS 16k folder in audio/data/")
    files = list_audio_files(root)
    print("Files:", len(files))
    if files:
        print("Example:", files[0].name)


if __name__ == "__main__":
    main()
