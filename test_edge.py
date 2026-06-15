import asyncio
import edge_tts
import io

async def test():
    # Attempt 1: Full Azure-style SSML
    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="pt-BR">'
        f'<voice name="pt-BR-AntonioNeural">'
        f'<prosody rate="-10%" pitch="-10Hz">'
        f'Teste de áudio.'
        f'</prosody></voice></speak>'
    )
    
    communicate = edge_tts.Communicate(ssml)
    print("Testing Communicate with full SSML...")
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            print("Audio received!")
            break
            
    # Attempt 2: Just the text to see what edge-tts generates
    simple_text = "Teste simples."
    comm2 = edge_tts.Communicate(simple_text, "pt-BR-AntonioNeural", rate="-10%", pitch="-10Hz")
    # We can inspect the internal SSML if we want
    # print(comm2._get_ssml()) # This is a private method but useful for debugging

if __name__ == "__main__":
    asyncio.run(test())
