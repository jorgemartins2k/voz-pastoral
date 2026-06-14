import React, { useState, useRef } from 'react';
import './App.css';

function App() {
  const [senha, setSenha] = useState('');
  const [texto, setTexto] = useState(`<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR">
    <voice name="pt-BR-AntonioNeural">
        <prosody rate="-10%" pitch="-10Hz">
            Meus queridos irmãos, minhas queridas irmãs.
            <break time="3s"/>

            Eu vi seus olhos perderem o brilho.
            <break time="2s"/>

            <emphasis level="strong">O seu sonho não morreu.</emphasis>
            <break time="2s"/>

            Ele está dormindo.
            <break time="3s"/>

            <!-- Pausa de 30 segundos -->
            <break time="5s"/> <break time="5s"/> <break time="5s"/>
            <break time="5s"/> <break time="5s"/> <break time="5s"/>

            E Eu vou despertá-lo.
            <break time="3s"/>

            Fique na Minha paz.
        </prosody>
    </voice>
</speak>`);
  const [voz, setVoz] = useState('pt-BR-AntonioNeural');
  const [velocidade, setVelocidade] = useState('-10%');
  const [tom, setTom] = useState('-10Hz');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ msg: '', type: '' });
  const [audioData, setAudioData] = useState(null);
  
  const audioPlayerRef = useRef(null);

  const base64ToBlob = (base64, mimeType) => {
    const byteCharacters = atob(base64);
    const byteArrays = [];
    for (let i = 0; i < byteCharacters.length; i += 512) {
      const slice = byteCharacters.slice(i, i + 512);
      const byteNumbers = new Array(slice.length);
      for (let j = 0; j < slice.length; j++) {
        byteNumbers[j] = slice.charCodeAt(j);
      }
      byteArrays.push(new Uint8Array(byteNumbers));
    }
    return new Blob(byteArrays, { type: mimeType });
  };

  const handleGerarAudio = async () => {
    if (!texto.trim()) {
      setStatus({ msg: 'Por favor, insira um texto ou SSML.', type: 'error' });
      return;
    }
    if (!senha) {
      setStatus({ msg: 'A senha é obrigatória para gerar o áudio.', type: 'error' });
      return;
    }

    setLoading(true);
    setAudioData(null);
    setStatus({ msg: '🎙️ Harmonizando voz pastoral... aguarde.', type: 'loading' });

    try {
      const response = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ senha, texto, voz, velocidade, tom })
      });

      const dados = await response.json();

      if (!response.ok) {
        throw new Error(dados.erro || 'Erro na comunicação com o servidor.');
      }

      const audioBlob = base64ToBlob(dados.audio, 'audio/mpeg');
      const audioUrl = URL.createObjectURL(audioBlob);
      
      setAudioData({ url: audioUrl, size: Math.round(dados.tamanho_bytes / 1024) });
      setStatus({ msg: '✅ Áudio gerado com sucesso!', type: 'success' });
    } catch (error) {
      setStatus({ msg: `❌ Error: ${error.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-wrapper">
      <div className="background-blobs"></div>
      
      <div className="container">
        <header className="header">
          <div className="badge-group">
            <span className="badge badge-secure">🔒 USO PESSOAL</span>
            <span className="badge badge-free">🎙️ EDGE TTS (GRÁTIS)</span>
          </div>
          <h1>🎙️ Voz Pastoral</h1>
          <p>Estúdio de Voz com SSML Completo & Estética Premium</p>
        </header>

        <main className="glass-card">
          <div className="info-bar">
            <span className="info-tag">✅ Sem API key</span>
            <span className="info-tag">⏱️ Pausas Longas (30s/60s)</span>
            <span className="info-tag">🎵 Áudio HQ</span>
          </div>

          <section className="auth-section">
            <div className="input-group">
              <label htmlFor="senhaInput">🔐 SENHA DE PROTEÇÃO</label>
              <input 
                type="password" 
                id="senhaInput" 
                placeholder="Sua chave secreta..." 
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                autoComplete="off" 
              />
            </div>
          </section>

          <section className="editor-section">
            <textarea 
              id="textoInput" 
              spellCheck="false"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
            ></textarea>
          </section>

          <section className="controls-grid">
            <div className="control-item">
              <label htmlFor="vozSelect">🎤 VOZ</label>
              <select id="vozSelect" value={voz} onChange={(e) => setVoz(e.target.value)}>
                <option value="pt-BR-AntonioNeural">Antonio · Masculino (Grave) ⭐</option>
                <option value="pt-BR-ThalitaNeural">Thalita · Feminino (Calmo)</option>
                <option value="pt-BR-FranciscaNeural">Francisca · Feminino (Natural)</option>
              </select>
            </div>
            <div className="control-item">
              <label htmlFor="velocidadeSelect">⚡ VELOCIDADE</label>
              <select id="velocidadeSelect" value={velocidade} onChange={(e) => setVelocidade(e.target.value)}>
                <option value="+0%">Normal</option>
                <option value="-10%">Lento (-10%)</option>
                <option value="-20%">Muito lento (-20%)</option>
              </select>
            </div>
            <div className="control-item">
              <label htmlFor="tomSelect">🎵 TOM</label>
              <select id="tomSelect" value={tom} onChange={(e) => setTom(e.target.value)}>
                <option value="+0Hz">Normal</option>
                <option value="-10Hz">Grave (-10Hz)</option>
                <option value="-20Hz">Muito grave (-20Hz)</option>
              </select>
            </div>
          </section>

          <button 
            id="gerarBtn" 
            className="primary-btn" 
            onClick={handleGerarAudio}
            disabled={loading}
          >
            <span className="btn-text" style={{ opacity: loading ? 0.5 : 1 }}>
              🔊 GERAR ÁUDIO PASTORAL
            </span>
            {loading && <span className="loader" style={{ display: 'inline-block' }}></span>}
          </button>

          {status.msg && (
            <div className={`status-msg status-${status.type}`} style={{ display: 'block' }}>
              {status.msg}
            </div>
          )}

          {audioData && (
            <div id="playerContainer" className="player-card" style={{ display: 'block' }}>
              <div className="player-header">
                <h4>✅ ÁUDIO PROCESSADO</h4>
                <span id="audioSize">{audioData.size} KB</span>
              </div>
              <audio ref={audioPlayerRef} src={audioData.url} controls></audio>
              <p className="download-hint">💡 Clique nos três pontos do player para baixar o MP3.</p>
            </div>
          )}
        </main>

        <footer className="footer-details">
          <details className="help-details">
            <summary>📋 Guia Rápido de SSML</summary>
            <div className="details-content">
              <code>&lt;break time="5s"/&gt;</code> - Pausa (máx 5s) <br />
              <code>&lt;emphasis level="strong"&gt;...&lt;/emphasis&gt;</code> - Ênfase <br />
              <code>&lt;prosody rate="-10%" pitch="-10Hz"&gt;</code> - Tom/Velocidade
            </div>
          </details>
        </footer>
      </div>
    </div>
  );
}

export default App;
