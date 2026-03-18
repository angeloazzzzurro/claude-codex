from pathlib import Path


def main():
    data_dir = Path(__file__).parent / "data" / "RAVDESS"
    if not data_dir.exists():
        raise FileNotFoundError("Place RAVDESS dataset in multimodal/data/")
    audio_files = list(data_dir.rglob("*.wav"))
    video_files = list(data_dir.rglob("*.mp4"))
    print("Audio files:", len(audio_files))
    print("Video files:", len(video_files))


if __name__ == "__main__":
    main()
