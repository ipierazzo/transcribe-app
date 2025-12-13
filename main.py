"""
Sistema de Transcrição de Áudio em Tempo Real com Análise de IA
Backend FastAPI com WebSocket para receber transcrições e processar com Groq API
"""

import asyncio
import json
import os
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from groq import Groq
from dotenv import load_dotenv
import time

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa FastAPI
app = FastAPI(title="Sistema de Transcrição e Análise com IA")

# Configura templates
templates = Jinja2Templates(directory="templates")

# Inicializa cliente Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Dicionário global para armazenar transcrições por client_id
transcriptions: Dict[str, str] = {}

# #region agent log
LOG_PATH = "/home/ipierazzo/Documents/projetos/medIA/.cursor/debug.log"
def log_debug(session_id, run_id, hypothesis_id, location, message, data):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({
                "sessionId": session_id,
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except:
        pass
# #endregion

# Modelo Groq a ser usado (pode ser configurado via variável de ambiente)
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Prompt do sistema para análise médica
SYSTEM_PROMPT = """Você é um assistente médico especialista. Analise a transcrição a seguir e gere um relatório estruturado contendo:
1. Resumo do caso
2. Principais Sintomas
3. Ações sugeridas

Seja objetivo, claro e profissional na análise."""


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Endpoint raiz que serve a interface HTML"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Endpoint WebSocket que recebe fragmentos de transcrição do frontend.
    
    Fluxo:
    1. Aceita conexão WebSocket
    2. Recebe fragmentos de texto e acumula em memória
    3. Quando recebe comando "fim" ou conexão fecha, processa com Groq API
    4. Retorna análise para o cliente
    """
    # #region agent log
    log_debug("debug-session", "run1", "A", "main.py:57", "WebSocket connection attempt", {"client_id": client_id})
    # #endregion
    await websocket.accept()
    # #region agent log
    log_debug("debug-session", "run1", "A", "main.py:60", "WebSocket accepted", {"client_id": client_id})
    # #endregion
    
    # Inicializa string de transcrição para este cliente
    if client_id not in transcriptions:
        transcriptions[client_id] = ""
        # #region agent log
        log_debug("debug-session", "run1", "E", "main.py:64", "New client_id initialized", {"client_id": client_id, "existing_clients": list(transcriptions.keys())})
        # #endregion
    else:
        # #region agent log
        log_debug("debug-session", "run1", "E", "main.py:67", "Existing client_id reused", {"client_id": client_id, "current_length": len(transcriptions[client_id])})
        # #endregion
    
    try:
        while True:
            # Recebe dados do frontend
            data = await websocket.receive_text()
            # #region agent log
            log_debug("debug-session", "run1", "D", "main.py:70", "Raw WebSocket data received", {"client_id": client_id, "data_length": len(data), "data_preview": data[:100]})
            # #endregion
            try:
                message = json.loads(data)
            except json.JSONDecodeError as e:
                # #region agent log
                log_debug("debug-session", "run1", "D", "main.py:74", "JSON decode error", {"client_id": client_id, "error": str(e), "data": data[:200]})
                # #endregion
                raise
            # #region agent log
            log_debug("debug-session", "run1", "D", "main.py:77", "Message parsed", {"client_id": client_id, "message_type": message.get("type"), "has_texto": "texto" in message})
            # #endregion
            
            # Verifica se é comando de fim
            if message.get("type") == "fim":
                # #region agent log
                log_debug("debug-session", "run1", "B", "main.py:81", "Fim command received", {"client_id": client_id, "transcription_length": len(transcriptions.get(client_id, ""))})
                # #endregion
                # Processa transcrição completa com Groq
                transcription_text = transcriptions.get(client_id, "")
                # #region agent log
                log_debug("debug-session", "run1", "B", "main.py:85", "Transcription before processing", {"client_id": client_id, "text_length": len(transcription_text), "text_preview": transcription_text[:200]})
                # #endregion
                
                if transcription_text.strip():
                    # Envia para análise na Groq API
                    try:
                        # #region agent log
                        log_debug("debug-session", "run1", "C", "main.py:90", "Calling Groq API", {"client_id": client_id, "text_length": len(transcription_text)})
                        # #endregion
                        analysis = await analyze_with_groq(transcription_text)
                        # #region agent log
                        log_debug("debug-session", "run1", "C", "main.py:93", "Groq API response received", {"client_id": client_id, "analysis_length": len(analysis) if analysis else 0})
                        # #endregion
                        
                        # Envia resultado para o cliente
                        await websocket.send_json({
                            "type": "analise_completa",
                            "resultado": analysis
                        })
                        # #region agent log
                        log_debug("debug-session", "run1", "A", "main.py:99", "Analysis sent to client", {"client_id": client_id})
                        # #endregion
                    except Exception as e:
                        # #region agent log
                        log_debug("debug-session", "run1", "C", "main.py:102", "Groq API error", {"client_id": client_id, "error": str(e), "error_type": type(e).__name__})
                        # #endregion
                        await websocket.send_json({
                            "type": "erro",
                            "mensagem": f"Erro ao processar com Groq: {str(e)}"
                        })
                else:
                    # #region agent log
                    log_debug("debug-session", "run1", "B", "main.py:109", "Empty transcription", {"client_id": client_id})
                    # #endregion
                    await websocket.send_json({
                        "type": "erro",
                        "mensagem": "Nenhuma transcrição recebida para análise"
                    })
                
                # Limpa transcrição após processamento
                transcriptions[client_id] = ""
                # #region agent log
                log_debug("debug-session", "run1", "E", "main.py:117", "Transcription cleared after processing", {"client_id": client_id})
                # #endregion
                break
            
            # Se for fragmento de texto, acumula
            elif message.get("type") == "texto":
                texto = message.get("texto", "")
                # #region agent log
                log_debug("debug-session", "run1", "B", "main.py:123", "Text fragment received", {"client_id": client_id, "texto_length": len(texto), "texto_preview": texto[:100], "before_length": len(transcriptions.get(client_id, ""))})
                # #endregion
                if texto:
                    # Adiciona espaço se já houver texto anterior
                    if transcriptions[client_id]:
                        transcriptions[client_id] += " "
                    transcriptions[client_id] += texto
                    # #region agent log
                    log_debug("debug-session", "run1", "B", "main.py:129", "Text fragment accumulated", {"client_id": client_id, "after_length": len(transcriptions[client_id]), "full_text_preview": transcriptions[client_id][-200:]})
                    # #endregion
                    
                    # Confirma recebimento (opcional)
                    await websocket.send_json({
                        "type": "confirmacao",
                        "status": "recebido"
                    })
                else:
                    # #region agent log
                    log_debug("debug-session", "run1", "B", "main.py:137", "Empty texto fragment ignored", {"client_id": client_id})
                    # #endregion
            
            # Comando para limpar transcrição (útil para nova sessão)
            elif message.get("type") == "limpar":
                # #region agent log
                log_debug("debug-session", "run1", "E", "main.py:144", "Clear command received", {"client_id": client_id, "before_length": len(transcriptions.get(client_id, ""))})
                # #endregion
                transcriptions[client_id] = ""
                await websocket.send_json({
                    "type": "confirmacao",
                    "status": "limpo"
                })
            else:
                # #region agent log
                log_debug("debug-session", "run1", "D", "main.py:151", "Unknown message type", {"client_id": client_id, "message_type": message.get("type"), "message_keys": list(message.keys())})
                # #endregion
    
    except WebSocketDisconnect:
        # #region agent log
        log_debug("debug-session", "run1", "A", "main.py:155", "WebSocket disconnected", {"client_id": client_id, "transcription_length": len(transcriptions.get(client_id, ""))})
        # #endregion
        # Se desconectar sem enviar "fim", processa o que foi acumulado
        transcription_text = transcriptions.get(client_id, "")
        
        if transcription_text.strip():
            try:
                # Tenta enviar análise mesmo após desconexão
                # (Nota: isso pode falhar se cliente já desconectou)
                analysis = await analyze_with_groq(transcription_text)
                await websocket.send_json({
                    "type": "analise_completa",
                    "resultado": analysis
                })
            except Exception as e:
                # #region agent log
                log_debug("debug-session", "run1", "A", "main.py:164", "Error processing after disconnect", {"client_id": client_id, "error": str(e)})
                # #endregion
                pass  # Cliente já desconectou
        
        # Limpa transcrição
        if client_id in transcriptions:
            del transcriptions[client_id]
            # #region agent log
            log_debug("debug-session", "run1", "E", "main.py:171", "Client transcription deleted", {"client_id": client_id})
            # #endregion
    
    except Exception as e:
        # #region agent log
        log_debug("debug-session", "run1", "A", "main.py:175", "WebSocket exception", {"client_id": client_id, "error": str(e), "error_type": type(e).__name__})
        # #endregion
        print(f"Erro no WebSocket: {str(e)}")
        try:
            await websocket.send_json({
                "type": "erro",
                "mensagem": f"Erro no servidor: {str(e)}"
            })
        except:
            pass  # Cliente pode ter desconectado


def _call_groq_api(transcription: str) -> str:
    """
    Função síncrona que chama a API Groq.
    Executada em thread separada para não bloquear o event loop.
    """
    # #region agent log
    log_debug("debug-session", "run1", "C", "main.py:180", "Groq API call starting", {"transcription_length": len(transcription), "api_key_set": bool(os.getenv("GROQ_API_KEY"))})
    # #endregion
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Transcrição da consulta:\n\n{transcription}"
                }
            ],
            model=GROQ_MODEL,
            temperature=0.3,
            max_tokens=2048
        )
        # #region agent log
        log_debug("debug-session", "run1", "C", "main.py:197", "Groq API call successful", {"choices_count": len(chat_completion.choices) if chat_completion.choices else 0, "has_content": bool(chat_completion.choices[0].message.content if chat_completion.choices else False)})
        # #endregion
        result = chat_completion.choices[0].message.content
        # #region agent log
        log_debug("debug-session", "run1", "C", "main.py:200", "Groq API response content", {"content_length": len(result) if result else 0, "content_preview": result[:200] if result else None})
        # #endregion
        return result
    except Exception as e:
        # #region agent log
        log_debug("debug-session", "run1", "C", "main.py:203", "Groq API call failed", {"error": str(e), "error_type": type(e).__name__})
        # #endregion
        raise


async def analyze_with_groq(transcription: str) -> str:
    """
    Envia transcrição para Groq API e retorna análise.
    Executa a chamada síncrona em thread separada para não bloquear.
    
    Args:
        transcription: Texto completo da transcrição
        
    Returns:
        Resposta da IA com análise estruturada
    """
    # #region agent log
    log_debug("debug-session", "run1", "C", "main.py:213", "analyze_with_groq called", {"transcription_length": len(transcription)})
    # #endregion
    try:
        # Executa chamada síncrona em thread separada
        analysis = await asyncio.to_thread(_call_groq_api, transcription)
        # #region agent log
        log_debug("debug-session", "run1", "C", "main.py:217", "analyze_with_groq completed", {"analysis_length": len(analysis) if analysis else 0})
        # #endregion
        return analysis
    
    except Exception as e:
        # #region agent log
        log_debug("debug-session", "run1", "C", "main.py:221", "analyze_with_groq exception", {"error": str(e), "error_type": type(e).__name__})
        # #endregion
        raise Exception(f"Erro na API Groq: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

