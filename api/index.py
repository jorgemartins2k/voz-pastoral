from flask import Flask, request, jsonify
from flask_cors import CORS
import edge_tts
import asyncio
import nest_asyncio
import io
import base64
import re
import html
from datetime import datetime

# Vercel entry point
app = Flask(__name__)
CORS(app)

nest_asyncio.apply()

SENHA_CORRETA = "JSDjsd321#$%"

def validar_senha(senha):
    return senha == SENHA_CORRETA

def processar_ssml(texto, voz, velocidade, tom):
    texto = texto.strip()
    if "<speak" in texto and "</speak>" in texto:
        return texto, True
    ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR">
    <voice name="{voz}">
        <prosody rate="{velocidade}" pitch="{tom}">
            {html.escape(texto)}
        </prosody>
    </voice>
</speak>'''
    return ssml, False

def contar_caracteres_uteis(texto):
    texto_sem_tags = re.sub(r'<[^>]+>', '', texto)
    texto_sem_tags = re.sub(r'\s+', ' ', texto_sem_tags).strip()
    return len(texto_sem_tags)

async def gerar_audio_edge_tts(texto, voz, velocidade, tom):
    ssml_final, ja_e_ssml = processar_ssml(texto, voz, velocidade, tom)
    if ja_e_ssml:
        communicate = edge_tts.Communicate(ssml_final, voice=voz)
    else:
        communicate = edge_tts.Communicate(ssml_final, voice=voz, rate=velocidade, pitch=tom)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    buffer.seek(0)
    return buffer.getvalue()

@app.route('/api/tts', methods=['POST'])
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

        audio_bytes = asyncio.run(gerar_audio_edge_tts(texto, voz_nome, velocidade, tom))
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        caracteres_uteis = contar_caracteres_uteis(texto)

        return jsonify({
            'sucesso': True,
            'audio': audio_base64,
            'formato': 'mp3',
            'tamanho_bytes': len(audio_bytes),
            'caracteres_texto': caracteres_uteis
        })
    except Exception as e:
        print(f"Erro no endpoint TTS: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'servico': 'edge-tts-pastoral-serverless'})

# Para testes locais: python api/index.py
if __name__ == '__main__':
    app.run(debug=True, port=5000)
