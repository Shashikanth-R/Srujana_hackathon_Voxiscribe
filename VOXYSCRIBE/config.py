from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()

# Database Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

# Flask Configuration
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# Azure Face API Configuration
AZURE_FACE_ENDPOINT = os.getenv("AZURE_FACE_ENDPOINT")
AZURE_FACE_KEY = os.getenv("AZURE_FACE_KEY")

# Azure Speech-to-Text Configuration
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
