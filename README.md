# Text-to-Speech Web Application

A FastAPI-based web application that converts text to speech using Google Cloud Text-to-Speech API with various voice options.

## Features

- Web interface for text-to-speech conversion
- Multiple voice options (male/female, standard/wavenet/neural voices)
- Character voices like Rick and Morty styles
- News anchor voices
- Audio download capability

## Prerequisites

- Python 3.7+
- Google Cloud Platform account with Text-to-Speech API enabled
- Google Cloud credentials configured

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Google Cloud credentials:
   
   Option 1 - Application Default Credentials (recommended for local development):
   ```bash
   # Install Google Cloud SDK first if not already installed
   # Then run:
   gcloud auth application-default login
   ```
   
   Option 2 - Service Account Key:
   - Create a service account in Google Cloud Console
   - Download the JSON key file
   - Set the environment variable:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
     ```

## Usage

Run the application:
```bash
python main.py
```

Open your browser and go to `http://127.0.0.1:8000`

## Configuration

The application uses various voice types from Google Cloud Text-to-Speech:
- Standard voices: Lower quality, faster processing
- Wavenet voices: Higher quality, more natural sounding
- Neural voices: Latest generation, best quality

## Troubleshooting

If you encounter the error "Your default credentials were not found", please ensure you have properly configured Google Cloud credentials as described above.