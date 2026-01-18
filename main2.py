from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from gtts import gTTS
import uuid
from pathlib import Path
import pyrubberband as pyrb
import soundfile as sf
from TTS.api import TTS
app = FastAPI()

# Create directories for audio files
AUDIO_DIR = Path("generated_audio")
AUDIO_DIR.mkdir(exist_ok=True)

class TTSRequest(BaseModel):
    text: str
    voice_type: str

# Voice configurations with different accents and speeds
VOICE_CONFIGS = {
    "male_deep": {
        "model": "tts_models/en/vctk/vits",
        "speaker": "p226"  # Male speaker
    },
    "male_standard": {
        "model": "tts_models/en/vctk/vits",
        "speaker": "p245"  # Male speaker
    },
    "male_british": {
        "model": "tts_models/en/vctk/vits",
        "speaker": "p227"  # Male British
    },
    "male_american": {
        "model": "tts_models/en/ljspeech/tacotron2-DDC",
        "speaker": None
    }
}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Google TTS Voice Generator</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 600px;
                width: 100%;
            }
            h1 {
                color: #333;
                margin-bottom: 30px;
                text-align: center;
                font-size: 28px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                color: #555;
                font-weight: 600;
            }
            textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                resize: vertical;
                min-height: 120px;
                font-family: inherit;
            }
            select {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                background: white;
                cursor: pointer;
            }
            textarea:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            .audio-container {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                display: none;
            }
            audio {
                width: 100%;
                margin-bottom: 15px;
            }
            .download-btn {
                background: #28a745;
                margin-top: 10px;
            }
            .download-btn:hover {
                background: #218838;
            }
            .loading {
                text-align: center;
                color: #667eea;
                margin-top: 15px;
                display: none;
            }
            .error {
                color: #dc3545;
                margin-top: 15px;
                padding: 10px;
                background: #f8d7da;
                border-radius: 5px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Voice Over Generator</h1>
            <form id="ttsForm">
                <div class="form-group">
                    <label for="text">Enter Text:</label>
                    <textarea id="text" name="text" placeholder="Type your text here..." required></textarea>
                </div>
                <div class="form-group">
                    <label for="voice">Select Voice:</label>
                  <select id="voice" name="voice" required>
                    <option value="male_deep">Male - Deep Voice</option>
                    <option value="male_standard">Male - Standard</option>
                    <option value="male_british">Male - British Accent</option>
                    <option value="male_american">Male - American Accent</option>
                  </select>
                    </div>
                <button type="submit" id="generateBtn">Generate Speech</button>
            </form>
            <div class="loading" id="loading">Generating audio...</div>
            <div class="error" id="error"></div>
            <div class="audio-container" id="audioContainer">
                <audio id="audioPlayer" controls></audio>
                <button class="download-btn" id="downloadBtn">Download Audio</button>
            </div>
        </div>

        <script>
            let currentAudioUrl = '';

            document.getElementById('ttsForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const text = document.getElementById('text').value;
                const voice = document.getElementById('voice').value;
                const generateBtn = document.getElementById('generateBtn');
                const loading = document.getElementById('loading');
                const error = document.getElementById('error');
                const audioContainer = document.getElementById('audioContainer');
                
                generateBtn.disabled = true;
                loading.style.display = 'block';
                error.style.display = 'none';
                audioContainer.style.display = 'none';
                
                try {
                    const response = await fetch('/generate-speech', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ text, voice_type: voice })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to generate speech');
                    }
                    
                    const data = await response.json();
                    currentAudioUrl = data.audio_url;
                    
                    const audioPlayer = document.getElementById('audioPlayer');
                    audioPlayer.src = currentAudioUrl;
                    
                    audioContainer.style.display = 'block';
                    
                } catch (err) {
                    error.textContent = 'Error: ' + err.message;
                    error.style.display = 'block';
                } finally {
                    generateBtn.disabled = false;
                    loading.style.display = 'none';
                }
            });
            
            document.getElementById('downloadBtn').addEventListener('click', () => {
                if (currentAudioUrl) {
                    const a = document.createElement('a');
                    a.href = currentAudioUrl;
                    a.download = 'voiceover.mp3';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                }
            });
        </script>
    </body>
    </html>
    """

# Initialize TTS model (add this after your app creation)


@app.post("/generate-speech")
async def generate_speech(request: TTSRequest):
    try:
        if request.voice_type not in VOICE_CONFIGS:
            raise HTTPException(status_code=400, detail="Invalid voice type")
        
        voice_config = VOICE_CONFIGS[request.voice_type]
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.wav"
        filepath = AUDIO_DIR / filename
        
        print(f"Initializing TTS model: {voice_config['model']}")
        
        # Initialize TTS with the specified model (downloads if needed)
        tts = TTS(model_name=voice_config["model"], progress_bar=True, gpu=False)
        
        # Generate speech
        if voice_config["speaker"]:
            print(f"Generating speech with speaker: {voice_config['speaker']}")
            tts.tts_to_file(
                text=request.text,
                file_path=str(filepath),
                speaker=voice_config["speaker"]
            )
        else:
            print("Generating speech without specific speaker")
            tts.tts_to_file(
                text=request.text,
                file_path=str(filepath)
            )
        
        print(f"Audio saved to: {filepath}")
        
        return {
            "status": "success",
            "audio_url": f"/audio/{filename}",
            "filename": filename
        }
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Determine media type based on file extension
    media_type = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"
    return FileResponse(filepath, media_type=media_type)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)