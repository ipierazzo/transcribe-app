# main.py ATUALIZADO
import os
import io
import json
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="medIA - Sistema de Transcrição e Análise",
    description="Sistema de transcrição de áudio com análise de IA",
    version="1.0.0"
)
templates = Jinja2Templates(directory="templates")

# Armazena transcrições por cliente
client_transcriptions = {}

def get_groq_client():
    """Retorna cliente Groq, criando apenas quando necessário"""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY não configurada no arquivo .env")
    return Groq(api_key=api_key)

# Lê o prompt do arquivo .env, com valor padrão caso não esteja definido
SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    """Você é um Médico Endocrinologista Sênior. 
Analise a transcrição e gere um relatório SOAP completo e documentos para emissão.
(Mantenha o prompt detalhado que criamos anteriormente aqui)"""
)

# Log para confirmar qual prompt está sendo usado
if os.environ.get("SYSTEM_PROMPT"):
    print("✅ SYSTEM_PROMPT carregado do arquivo .env")
else:
    print("ℹ️  Usando SYSTEM_PROMPT padrão (defina SYSTEM_PROMPT no .env para personalizar)")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    """Endpoint de health check"""
    return {"status": "ok", "service": "medIA"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    print(f"🔌 Tentativa de conexão WebSocket do cliente: {client_id}")
    try:
        await websocket.accept()
        print(f"✅ WebSocket conectado: {client_id}")
        client_transcriptions[client_id] = ""
    except Exception as e:
        print(f"❌ Erro ao aceitar conexão WebSocket: {e}")
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            print(f"📨 Mensagem recebida de {client_id}: {message.get('type', 'unknown')}")
            
            if message.get("type") == "texto":
                # Acumula transcrição
                texto = message.get("texto", "")
                if client_id in client_transcriptions:
                    client_transcriptions[client_id] += " " + texto
                await websocket.send_json({"type": "confirmacao", "status": "recebido"})
                
            elif message.get("type") == "fim":
                # Processa análise quando recebe comando de fim
                transcription = client_transcriptions.get(client_id, "")
                if transcription.strip():
                    try:
                        client = get_groq_client()
                        print("Iniciando análise clínica...")
                        chat_completion = client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": transcription}
                            ],
                            model="llama-3.3-70b-versatile",
                            temperature=0.3
                        )
                        
                        resultado = chat_completion.choices[0].message.content
                        await websocket.send_json({
                            "type": "analise_completa",
                            "resultado": resultado
                        })
                    except Exception as e:
                        print(f"Erro na análise: {e}")
                        await websocket.send_json({
                            "type": "erro",
                            "mensagem": str(e)
                        })
                else:
                    await websocket.send_json({
                        "type": "erro",
                        "mensagem": "Nenhuma transcrição disponível para análise"
                    })
                    
            elif message.get("type") == "limpar":
                client_transcriptions[client_id] = ""
                await websocket.send_json({"type": "confirmacao", "status": "limpo"})
                
    except WebSocketDisconnect:
        print(f"🔌 Cliente {client_id} desconectado normalmente")
    except Exception as e:
        print(f"❌ Erro no WebSocket {client_id}: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({"type": "erro", "mensagem": str(e)})
        except:
            print(f"   Não foi possível enviar mensagem de erro ao cliente")
    finally:
        if client_id in client_transcriptions:
            del client_transcriptions[client_id]
            print(f"🧹 Limpeza: transcrição do cliente {client_id} removida")

@app.post("/api/transcribe-whisper")
async def transcribe_whisper(audio: UploadFile = File(...)):
    try:
        audio_content = await audio.read()
        
        print("Iniciando transcrição com Groq Whisper...")
        client = get_groq_client()
        transcription = client.audio.transcriptions.create(
            file=(audio.filename, audio_content),
            model="whisper-large-v3",
            response_format="text",
            language="pt"
        )
        
        print(f"Transcrição concluída: {len(transcription)} caracteres.")
        return {"transcription": transcription}
        
    except Exception as e:
        print(f"Erro na transcrição: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        transcription = body.get("transcription", "")
        
        if not transcription.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Transcrição vazia"}
            )
        
        print("Iniciando análise clínica...")
        client = get_groq_client()
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcription}
            ],
                            model="llama-3.3-70b-versatile",
            temperature=0.3
        )
        
        resultado = chat_completion.choices[0].message.content
        return {"resultado": resultado}
        
    except Exception as e:
        print(f"Erro na análise: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/upload-audio")
async def handle_audio(file: UploadFile = File(...)):
    try:
        # 1. Ler o arquivo de áudio recebido do frontend
        audio_content = await file.read()
        
        # 2. Transcrever usando Groq (Whisper Large V3)
        print("Iniciando transcrição com Groq Whisper...")
        client = get_groq_client()
        transcription = client.audio.transcriptions.create(
            file=(file.filename, audio_content),
            model="whisper-large-v3",
            response_format="text",
            language="pt"
        )
        
        print(f"Transcrição concluída: {len(transcription)} caracteres.")

        # 3. Analisar com Llama 3 (Também na Groq)
        print("Iniciando análise clínica...")
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcription}
            ],
                            model="llama-3.3-70b-versatile",
            temperature=0.3
        )
        
        return {"report": chat_completion.choices[0].message.content}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    import sys
    
    print("=" * 60)
    print("🚀 INICIANDO SERVIDOR medIA")
    print("=" * 60)
    print("📍 URL Local: http://localhost:8000")
    print("📍 URL Local: http://127.0.0.1:8000")
    print("📍 Health Check: http://localhost:8000/health")
    print("=" * 60)
    print("⚠️  Mantenha este terminal aberto enquanto usar o sistema")
    print("⚠️  Pressione Ctrl+C para parar o servidor")
    print("=" * 60)
    print()
    
    # Verifica se a porta está em uso
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8000))
    sock.close()
    if result == 0:
        print("⚠️  AVISO: A porta 8000 já está em uso!")
        print("   Pode haver outro servidor rodando.")
        print("   Se quiser continuar mesmo assim, pressione Enter...")
        print("   Ou pressione Ctrl+C para cancelar e parar o outro processo")
        try:
            input()
        except KeyboardInterrupt:
            print("\nCancelado pelo usuário")
            sys.exit(0)
    
    try:
        print("✅ Iniciando servidor...\n")
        # Usa string de importação para permitir reload
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True, 
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("🛑 SERVIDOR PARADO PELO USUÁRIO")
        print("=" * 60)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ ERRO: Porta 8000 já está em uso!")
            print("   Execute: lsof -ti:8000 | xargs kill")
            print("   Ou mude a porta no código")
        else:
            print(f"\n❌ Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)