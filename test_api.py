import requests
import json

url = "http://localhost:5000/api/tts"
payload = {
    "senha": "JSDjsd321#$%",
    "texto": "Meus queridos irmãos.... Eu vi seus olhos perderem o brilho.",
    "voz": "pt-BR-DonatoNeural",
    "velocidade": "-15%",
    "tom": "-12Hz"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
except Exception as e:
    print(f"Error: {e}")
