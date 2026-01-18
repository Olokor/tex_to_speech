from TTS.api import TTS

print("Downloading models... This may take several minutes.")

# Download the models you want to use
models_to_download = [
    "tts_models/en/vctk/vits",
    "tts_models/en/ljspeech/tacotron2-DDC",
    "tts_models/en/ljspeech/glow-tts",
]

for model_name in models_to_download:
    print(f"\nDownloading: {model_name}")
    try:
        tts = TTS(model_name=model_name, progress_bar=True, gpu=False)
        print(f"✓ Successfully downloaded: {model_name}")
    except Exception as e:
        print(f"✗ Failed to download {model_name}: {e}")

print("\nAll models downloaded! You can now run your app.")