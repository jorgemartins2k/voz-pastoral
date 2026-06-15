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


async def gerar_audio_edge_tts(texto, voz, velocidade, tom):
    ssml_final = processar_ssml(texto, voz, velocidade, tom)
    
    # Tentamos criar o objeto communicate. 
    # Se houver erro de rede ou DNS, o stream() irá falhar.
    try:
        communicate = edge_tts.Communicate(ssml_final)
        
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        
        if buffer.tell() == 0:
            raise Exception("Nenhum áudio foi gerado pelo serviço.")
            
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        raise Exception(f"Falha no Edge-TTS: {str(e)}")

def contar_caracteres_uteis(texto):
    texto_sem_tags = re.sub(r'<[^>]+>', '', texto)
    texto_sem_tags = re.sub(r'\s+', ' ', texto_sem_tags).strip()
    return len(texto_sem_tags)

def processar_ssml(texto, voz, velocidade, tom):
    """
    Garante suporte total a tags SSML e aplica equalização pastoral.
    """
    texto = texto.strip()
    
    # Escapa caracteres XML básicos (evita erro 500 se o usuário usar & ou <)
    # Primeiro escapamos tudo, depois voltamos o que queremos que seja tag
    texto = html.escape(texto)
    
    # Detecção robusta de SSML
    if re.search(r'^\s*&lt;speak', texto, re.IGNORECASE):
        # Se o usuário enviou SSML, desfazemos o escape do bloco speak
        # para que o motor reconheça como comando.
        texto = html.unescape(texto)
        texto = re.sub(r'^\s*(<\?xml[^>]*\?>\s*)?', '', texto).strip()
        return texto

    # CONVERSÃO DE PONTUAÇÃO PARA PAUSAS
    def converter_pontos(match):
        dots = match.group(0)
        n = len(dots)
        if n >= 4: return ' <break time="2000ms"/> '
        if n == 3: return ' <break time="1000ms"/> '
        if n == 2: return ' <break time="500ms"/> '
        return dots

    texto = re.sub(r'\.{2,}', converter_pontos, texto)
    
    # EQUALIZAÇÃO PASTORAL (Voz masculina profunda)
    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR">'
        f'<voice name="{voz}">'
        f'<prosody rate="{velocidade}" pitch="{tom}" volume="+10%">'
        f'{texto}'
        f'</prosody></voice></speak>'
    )
    return ssml.strip()

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
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'servico': 'edge-tts-pastoral-serverless'})

# Para testes locais: python api/index.py
if __name__ == '__main__':
    app.run(debug=True, port=5000)
