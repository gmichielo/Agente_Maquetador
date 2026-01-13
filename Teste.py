from openai import OpenAI
from dotenv import load_dotenv
import os
import base64

load_dotenv()
client = OpenAI()

print("OpenAI OK")