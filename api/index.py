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

def sanitize_ssml(text: str) -> str:
    """
    Remove tags SSML não suportadas ou problemáticas para o edge-tts.
    """
    # Remove tags <emphasis> (não são bem suportadas por todos os modelos)
    text = re.sub(r'<emphasis[^>]*>', '', text)
    text = re.sub(r'</emphasis>', '', text)
    
    # Remove tags <mstts:express-as> (que podem quebrar o parser dependendo do modelo)
    text = re.sub(r'<mstts:express-as[^>]*>', '', text)
    text = re.sub(r'</mstts:express-as>', '', text)
    
    # Remove namespaces não suportados
    text = re.sub(r'xmlns:mstts="[^"]*"', '', text)
    
    return text

def processar_ssml(texto, voz, velocidade, tom):
    """
    Garante suporte total a tags SSML (break, prosody, etc) com sanitização.
    """
    texto = texto.strip()
    texto = sanitize_ssml(texto)
    
    # Caso o usuário já tenha enviado um bloco <speak> completo, garantimos que não tenha lixo
    if texto.startswith("<speak") and texto.endswith("</speak>"):
        return texto

    # Construímos o bloco SSML garantindo que <prosody> envolva o texto
    # para respeitar velocidade e tom da interface
    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR">'
        f'<voice name="{voz}">'
        f'<prosody rate="{velocidade}" pitch="{tom}">'
        f'{texto}'
        f'</prosody></voice></speak>'
    )
    return ssml


def contar_caracteres_uteis(texto):
    texto_sem_tags = re.sub(r'<[^>]+>', '', texto)
    texto_sem_tags = re.sub(r'\s+', ' ', texto_sem_tags).strip()
    return len(texto_sem_tags)

async def gerar_audio_edge_tts(texto, voz, velocidade, tom):
    ssml_final = processar_ssml(texto, voz, velocidade, tom)
    
    # Se passar SSML para o Communicate, NÃO deve-se passar voice, rate ou pitch separadamente
    # pois isso faz o edge-tts ignorar o SSML ou gerar blocos aninhados inválidos.
    communicate = edge_tts.Communicate(ssml_final)
    
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    buffer.seek(0)
    return buffer.getvalue()

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

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'servico': 'edge-tts-pastoral-serverless'})

# Para testes locais: python api/index.py
if __name__ == '__main__':
    app.run(debug=True, port=5000)
