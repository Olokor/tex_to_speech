from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.cloud import texttospeech
import os
import uuid
from pathlib import Path

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace the client initialization with this:
try:
    client = texttospeech.TextToSpeechClient()
    logger.info("Google TTS client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Google TTS client: {e}")
    logger.error("Make sure GOOGLE_APPLICATION_CREDENTIALS is set correctly")
    client = None

app = FastAPI()

# Create directories for audio files
AUDIO_DIR = Path("generated_audio")
AUDIO_DIR.mkdir(exist_ok=True)

class TTSRequest(BaseModel):
    text: str
    voice_type: str

# Voice configurations
VOICE_CONFIGS = {
    "male_standard": {
        "language_code": "en-US",
        "name": "en-US-Standard-D",
        "ssml_gender": texttospeech.SsmlVoiceGender.MALE
    },
    "female_standard": {
        "language_code": "en-US",
        "name": "en-US-Standard-C",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },
    "male_deep": {
        "language_code": "en-US",
        "name": "en-US-Wavenet-D",
        "ssml_gender": texttospeech.SsmlVoiceGender.MALE
    },
    "female_soft": {
        "language_code": "en-US",
        "name": "en-US-Wavenet-C",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },
    "rick_style": {
        "language_code": "en-US",
        "name": "en-US-Wavenet-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.MALE,
        "pitch": -2.0,
        "speaking_rate": 1.15
    },
    "morty_style": {
        "language_code": "en-US",
        "name": "en-US-Wavenet-B",
        "ssml_gender": texttospeech.SsmlVoiceGender.MALE,
        "pitch": 4.0,
        "speaking_rate": 1.1
    },
    "female_news": {
        "language_code": "en-US",
        "name": "en-US-Neural2-F",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },
    "male_news": {
        "language_code": "en-US",
        "name": "en-US-Neural2-D",
        "ssml_gender": texttospeech.SsmlVoiceGender.MALE
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
                        <option value="male_standard">Male - Standard</option>
                        <option value="female_standard">Female - Standard</option>
                        <option value="male_deep">Male - Deep (Wavenet)</option>
                        <option value="female_soft">Female - Soft (Wavenet)</option>
                        <option value="male_news">Male - News Anchor (Neural)</option>
                        <option value="female_news">Female - News Anchor (Neural)</option>
                        <option value="rick_style">Rick Style - Gruff Scientist</option>
                        <option value="morty_style">Morty Style - Young & Anxious</option>
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

app.post("/generate-speech")
async def generate_speech(request: TTSRequest):
    try:
        if client is None:
            raise HTTPException(
                status_code=503, 
                detail="Google TTS client not initialized. Please set GOOGLE_APPLICATION_CREDENTIALS environment variable."
            )
        
        if request.voice_type not in VOICE_CONFIGS:
            raise HTTPException(status_code=400, detail="Invalid voice type")
        
        voice_config = VOICE_CONFIGS[request.voice_type]
        
        synthesis_input = texttospeech.SynthesisInput(text=request.text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code=voice_config["language_code"],
            name=voice_config["name"],
            ssml_gender=voice_config["ssml_gender"]
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch=voice_config.get("pitch", 0.0),
            speaking_rate=voice_config.get("speaking_rate", 1.0)
        )
        
        logger.info(f"Generating speech with voice: {request.voice_type}")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        filename = f"{uuid.uuid4()}.mp3"
        filepath = AUDIO_DIR / filename
        
        with open(filepath, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"Audio generated successfully: {filename}")
        
        return {
            "status": "success",
            "audio_url": f"/audio/{filename}",
            "filename": filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")
@app.get("/audio/{filename}")
async def get_audio(filename: str):
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(filepath, media_type="audio/mpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)