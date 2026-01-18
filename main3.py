from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import pyttsx3
import uuid
from pathlib import Path
import subprocess
import threading
import time
import gc

app = FastAPI()

# Thread lock to ensure only one pyttsx3 operation at a time
tts_lock = threading.Lock()

# Create directories for audio files
AUDIO_DIR = Path("generated_audio")
AUDIO_DIR.mkdir(exist_ok=True)

class TTSRequest(BaseModel):
    text: str
    voice_type: str

# Voice configurations with different settings
VOICE_CONFIGS = {
    "male_standard": {
        "rate": 150,
        "volume": 1.0
    },
    "male_slow": {
        "rate": 130,
        "volume": 1.0
    },
    "male_fast": {
        "rate": 170,
        "volume": 1.0
    },
    "male_motivational": {
        "rate": 145,
        "volume": 1.0
    }
}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Offline TTS Voice Generator</title>
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
            <h1>Offline Voice Over Generator</h1>
            <form id="ttsForm">
                <div class="form-group">
                    <label for="text">Enter Text:</label>
                    <textarea id="text" name="text" placeholder="Type your text here..." required></textarea>
                </div>
                <div class="form-group">
                    <label for="voice">Select Voice:</label>
                    <select id="voice" name="voice" required>
                    <option value="male_standard">Male - Standard Pace</option>
                    <option value="male_slow">Male - Slow (Motivational)</option>
                    <option value="male_fast">Male - Fast Pace</option>
                    <option value="male_motivational">Male - Motivational</option>
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

def synthesize_speech_safe(text, voice_config, output_path):
    """Function to run speech synthesis with proper locking and cleanup"""
    engine = None
    try:
        # Acquire lock to ensure only one pyttsx3 engine at a time
        with tts_lock:
            engine = pyttsx3.init()
            voices_list = engine.getProperty('voices')
            
            # Set voice properties
            if voice_config["voice_index"] < len(voices_list):
                engine.setProperty('voice', voices_list[voice_config["voice_index"]].id)
            
            engine.setProperty('rate', voice_config["rate"])
            engine.setProperty('volume', voice_config["volume"])
            
            # Save to file
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            
            # IMPORTANT: Don't delete the engine immediately
            # Give time for all callbacks to complete
            time.sleep(0.5)
            
            # Now safely stop the engine
            try:
                engine.stop()
            except:
                pass
            
            # Keep a reference to the engine briefly before deletion
            # This prevents premature garbage collection
            time.sleep(0.2)
            
    except Exception as e:
        print(f"Error in speech synthesis: {str(e)}")
        raise
    finally:
        # Clean up engine reference
        if engine is not None:
            try:
                del engine
            except:
                pass
        # Force garbage collection
        gc.collect()
        
        # Verify the output file was created
        if not output_path.exists():
            raise Exception("Audio file was not created successfully")

@app.post("/generate-speech")
async def generate_speech(request: TTSRequest):
    try:
        if request.voice_type not in VOICE_CONFIGS:
            raise HTTPException(status_code=400, detail="Invalid voice type")
        
        voice_config = VOICE_CONFIGS[request.voice_type]
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = AUDIO_DIR / filename
        
        # Initialize pyttsx3
        engine = pyttsx3.init()
        
        # Get available voices and select male voice
        voices = engine.getProperty('voices')
        
        # Try to find a male voice (index 0 is usually male on most systems)
        male_voice = voices[0].id
        
        engine.setProperty('voice', male_voice)
        engine.setProperty('rate', voice_config['rate'])
        engine.setProperty('volume', voice_config['volume'])
        
        # Save to file
        engine.save_to_file(request.text, str(filepath))
        engine.runAndWait()
        
        print(f"Audio generated: {filepath}")
        
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
    if filename.endswith('.mp3'):
        media_type = "audio/mpeg"
    elif filename.endswith('.wav'):
        media_type = "audio/wav"
    else:
        media_type = "audio/mpeg"  # default
    
    return FileResponse(filepath, media_type=media_type)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)