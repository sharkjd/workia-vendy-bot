import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI()

async def transcribe_voice(file_path: str) -> str:
    """
    Univerzální metoda pro přepis audia na text pomocí Whisperu.
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                language="cs"  # Natvrdo čeština pro lepší přesnost u Vendy
            )
        return transcript.text
    except Exception as e:
        print(f"Chyba při transkripci: {e}")
        return ""
    finally:
        # Smažeme dočasný soubor, ať nezaplníme disk serveru
        if os.path.exists(file_path):
            os.remove(file_path)