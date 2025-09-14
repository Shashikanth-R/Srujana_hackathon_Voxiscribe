# Optional helper using Azure Speech SDK.
# You must install the azure-cognitiveservices-speech package and set AZURE_SPEECH_KEY/REGION in env
import os
import tempfile
from config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION

try:
    import azure.cognitiveservices.speech as speechsdk
except Exception:
    speechsdk = None

def transcribe_file_with_azure(file_path, language="en-IN"):
    if speechsdk is None:
        raise RuntimeError("Azure Speech SDK not installed. Install azure-cognitiveservices-speech.")
    speech_key = AZURE_SPEECH_KEY
    region = AZURE_SPEECH_REGION
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=region)
    speech_config.speech_recognition_language = language
    audio_input = speechsdk.AudioConfig(filename=file_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    result = recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        return ""
