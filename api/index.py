from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import io
import base64
import re
import html
import os
from datetime import datetime

# Vercel entry point
app = Flask(__name__)
CORS(app)

# CONFIGURAÇÕES (Use variáveis de ambiente no Vercel!)
SENHA_CORRETA = "JSDjsd321#$%"
AZURE_API_KEY = os.getenv("AZURE_API_KEY", "7b0b691656e4480cbda68735165977a4") # Fallback para chave do usuário se existir
AZURE_REGION = os.getenv("AZURE_REGION", "brazilsouth")

def validar_senha(senha):
    return senha == SENHA_CORRETA

def contar_caracteres_uteis(texto):
    if not texto: return 0
    texto_limpo = re.sub(r'<[^>]+>', '', texto)
    return len(texto_limpo.strip())

def processar_ssml(texto, voz, velocidade, tom):
    """
    Garante suporte total a tags SSML e aplica equalização pastoral oficial (Azure).
    """
    texto = texto.strip()
    
    # Se já for SSML puro, enviamos direto
    if texto.startswith("<speak") or texto.startswith("<?xml"):
        return texto

    # Para texto puro:
    # 1. Escapamos caracteres XML
    texto = html.escape(texto)
    
    # 2. Convertemos as pontuações em pausas reais (Roteiro Limpo)
    def converter_pontos(match):
        n = len(match.group(0))
        if n >= 4: return '<break time="2000ms"/>'
        if n == 3: return '<break time="1000ms"/>'
        if n == 2: return '<break time="500ms"/>'
        return match.group(0)

    texto = re.sub(r'\.{2,}', converter_pontos, texto)
    
    # 3. Montamos o SSML com tags oficiais do Azure para estilo "calm"
    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="pt-BR">'
        f'<voice name="{voz}">'
        f'<mstts:express-as style="calm" styledegree="1.5">'
        f'<prosody rate="{velocidade}" pitch="{tom}" volume="+15%">'
        f'{texto}'
        f'</prosody></mstts:express-as></voice></speak>'
    )
    return ssml

def gerar_audio_azure(ssml):
    """Envia SSML para Azure TTS e retorna o áudio"""
    url = f"https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_API_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
        "User-Agent": "VozPastoral/2.0"
    }
    
    response = requests.post(url, headers=headers, data=ssml.encode('utf-8'))
    
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Erro Azure ({response.status_code}): {response.text}")

@app.route('/api/tts', methods=['POST'])
@app.route('/tts', methods=['POST'])
def tts_endpoint():
    try:
        dados = request.get_json()
        senha = dados.get('senha', '')
        if not validar_senha(senha):
            return jsonify({'erro': 'Senha incorreta. Acesso negado.'}), 401
        
        texto = dados.get('texto', '').strip()
        voz_nome = dados.get('voz', 'pt-BR-AntonioNeural')
        velocidade = dados.get('velocidade', '-10%')
        tom = dados.get('tom', '-10Hz')

        if not texto:
            return jsonify({'erro': 'Digite o texto para conversão'}), 400

        # Processa e gera
        ssml_final = processar_ssml(texto, voz_nome, velocidade, tom)
        audio_bytes = gerar_audio_azure(ssml_final)
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        caracteres_uteis = contar_caracteres_uteis(texto)

        return jsonify({
            'sucesso': True,
            'audio': audio_base64,
            'tamanho_bytes': len(audio_bytes),
            'caracteres_texto': caracteres_uteis
        })
    except Exception as e:
        print(f"Erro no endpoint TTS: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/health', methods=['GET'])
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'servico': 'azure-tts-pastoral'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
