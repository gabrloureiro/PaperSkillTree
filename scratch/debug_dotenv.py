
import os
from dotenv import load_dotenv, find_dotenv

print(f"Current working directory: {os.getcwd()}")
print(f"Dotenv found at: {find_dotenv()}")
load_dotenv(find_dotenv())

print(f"MODEL_NAME from env: {os.getenv('MODEL_NAME')}")
