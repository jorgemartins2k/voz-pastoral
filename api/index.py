from flask import Flask, request, jsonify
from flask_cors import CORS
import edge_tts
import asyncio
import nest_asyncio
import io
import base64
import re
import os
from datetime import datetime

# Vercel entry point
app = Flask(__name__)
CORS(app)

nest_asyncio.apply()

SENHA_CORRETA = "JSDjsd321#$%"

def validar_senha(senha):
    return senha == SENHA_CORRETA

def contar_caracteres_uteis(texto):
    if not texto: return 0
    # Remove qualquer tag de fallback ou espaços extras
    texto_limpo = re.sub(r'<[^>]+>', '', texto)
    return len(texto_limpo.strip())

def processar_texto_para_pausas(texto):
    """
    Converte pontuações extras em padrões que o motor TTS interpreta como silêncio, 
    SEM usar tags SSML (para evitar que sejam narradas).
    """
    texto = texto.strip()
    
    # Se o usuário enviou SSML deliberadamente, avisamos que pode narrar
    if texto.startswith("<speak"):
        return texto

    # Regra do Roteiro Limpo (Sem Tags):
    # . . . . (pontos com espaços) costumam gerar silêncio natural em cada ponto
    # .... ->  . . . . 
    # ...  ->  . . .
    # ..   ->  . .
    def repetir_pontos(match):
        n = len(match.group(0))
        return " " + ". " * n + " "

    texto = re.sub(r'\.{2,}', repetir_pontos, texto)
    return texto

async def gerar_audio_edge_tts(texto, voz, velocidade, tom):
    # Processamos o texto para pausas naturais (sem tags)
    texto_processado = processar_texto_para_pausas(texto)
    
    # Se o texto processado ainda for SSML (porque o usuário digitou), usamos direto
    if texto_processado.startswith("<speak"):
        communicate = edge_tts.Communicate(texto_processado)
    else:
        # Se for texto puro (nosso padrão), usamos os parâmetros do Communicate
        # Isso garante que NUNCA narre tags, pois o edge-tts cuidará do SSML interno.
        communicate = edge_tts.Communicate(
            texto_processado, 
            voice=voz, 
            rate=velocidade, 
            pitch=tom
        )
    
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    
    if buffer.tell() == 0:
        raise Exception("Nenhum áudio gerado.")
        
    buffer.seek(0)
    return buffer.getvalue()

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

        # Roda o processamento async
        audio_bytes = asyncio.run(gerar_audio_edge_tts(texto, voz_nome, velocidade, tom))
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        caracteres_uteis = contar_caracteres_uteis(texto)

        return jsonify({
            'sucesso': True,
            'audio': audio_base64,
            'tamanho_bytes': len(audio_bytes),
            'caracteres_texto': caracteres_uteis
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/health', methods=['GET'])
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'servico': 'edge-tts-free-pastoral'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
