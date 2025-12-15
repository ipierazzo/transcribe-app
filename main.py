import os
import json
import tempfile
import subprocess
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq
from dotenv import load_dotenv

# 1. Carrega variáveis de ambiente (.env) - apenas em desenvolvimento
# Em produção (Render.com), as variáveis vêm das configurações do serviço
load_dotenv()

# Verifica se a chave existe (pode vir de .env ou variáveis de ambiente do sistema)
if not os.getenv("GROQ_API_KEY"):
    raise ValueError(
        "A chave GROQ_API_KEY não foi encontrada. "
        "Configure-a no arquivo .env (desenvolvimento) ou nas variáveis de ambiente (produção)."
    )

# Verifica se OPENAI_API_KEY existe (opcional, para Whisper)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_WHISPER = OPENAI_API_KEY is not None

# 2. Configuração do Cliente Groq
client_groq = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# 3. Configuração do App e Templates
app = FastAPI(
    title="MVP Doctor AI Scribe",
    description="Sistema de transcrição e análise de consultas médicas com IA"
)
templates = Jinja2Templates(directory="templates")

# 4. Prompt de Sistema (Especialista em Endocrinologia + SOAP)
SYSTEM_PROMPT = """
Você é um Médico Endocrinologista Sênior, renomado por sua precisão clínica e humanização.
Sua tarefa é analisar a transcrição bruta de uma consulta médica e estruturar as informações seguindo rigorosamente o protocolo SOAP.
Ao final, você deve gerar o rascunho de todos os documentos médicos necessários (Receituários, Pedidos de Exame, Atestados) baseados na conduta clínica definida.

DIRETRIZES DE ANÁLISE:
1. Ignore erros gramaticais ou de concordância advindos da transcrição automática, focando no contexto clínico.
2. Identifique nuances endocrinológicas (metabolismo, tireoide, diabetes, obesidade, hormônios, rotina alimentar e sono).
3. Seja formal, técnico e objetivo na estrutura SOAP.

ESTRUTURA DE RESPOSTA OBRIGATÓRIA:

--- INÍCIO DO PRONTUÁRIO (SOAP) ---

# 1. SUBJETIVO (S)
- **Queixa Principal (QP):** O motivo da consulta.
- **História da Moléstia Atual (HMA):** Narrativa dos sintomas, tempo de evolução.
- **Histórico Patológico/Familiar:** Doenças prévias, histórico familiar relevante.
- **Estilo de Vida:** Alimentação, atividade física, sono, tabagismo/etilismo.

# 2. OBJETIVO (O)
- **Dados Vitais e Antropometria:** (Extraia se citado: Peso, Altura, IMC, PA, Glicemia).
- **Exame Físico:** (Extraia se citado: tireoide, pele, edemas).

# 3. AVALIAÇÃO (A)
- **Hipóteses Diagnósticas:** Liste as prováveis condições.
- **Raciocínio Clínico:** Breve justificativa endocrinológica.

# 4. PLANO (P)
- **Conduta Terapêutica:** Medicamentos prescritos ou ajustados.
- **Orientações:** Mudanças de estilo de vida.
- **Seguimento:** Retorno.

--- FIM DO PRONTUÁRIO ---

--- DOCUMENTOS PARA EMISSÃO ---
(Gere o texto exato para o documento, pronto para assinatura)

[DOCUMENTO 1: RECEITUÁRIO MÉDICO]
- Nome do Paciente: (Use "Paciente" se não identificado)
- Via de administração:
- Medicamento + Concentração
- Posologia detalhada
- Quantidade

[DOCUMENTO 2: PEDIDO DE EXAMES]
- Lista de exames (Ex: TSH, T4 Livre, Glicemia, HbA1c, etc.)
- Justificativa (se aplicável)

--- FIM DOS DOCUMENTOS ---
"""

# Função auxiliar para chamar a IA
def process_with_groq(full_text: str):
    try:
        chat_completion = client_groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Transcrição da consulta para análise:\n\n{full_text}",
                }
            ],
            model="llama-3.3-70b-versatile",  # Modelo atualizado (substitui llama3-70b-8192 descontinuado)
            temperature=0.3, # Baixa temperatura para precisão técnica
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Erro ao processar com a IA: {str(e)}"

# Função para transcrever áudio com Whisper
async def transcribe_with_whisper(audio_file_path: str) -> str:
    """Transcreve áudio usando Whisper API da OpenAI"""
    try:
        if not USE_WHISPER:
            return "Erro: OPENAI_API_KEY não configurada. Configure no arquivo .env"
        
        import openai
        client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        with open(audio_file_path, "rb") as audio_file:
            transcript = client_openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt",
                response_format="text"
            )
        
        return transcript if isinstance(transcript, str) else transcript.text
    except ImportError:
        return "Erro: Biblioteca openai não instalada. Execute: pip install openai"
    except Exception as e:
        return f"Erro ao transcrever com Whisper: {str(e)}"

# Health check endpoint para Render
@app.get("/health")
async def health_check():
    """Endpoint de health check para monitoramento"""
    return {"status": "ok", "service": "medIA"}

# Rota Principal (Frontend)
@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Endpoint para transcrição com Whisper
@app.post("/api/transcribe-whisper")
async def transcribe_whisper_endpoint(audio: UploadFile = File(...)):
    """Recebe áudio e retorna transcrição usando Whisper"""
    if not USE_WHISPER:
        return JSONResponse(
            status_code=400,
            content={"error": "Whisper não configurado. Adicione OPENAI_API_KEY no arquivo .env"}
        )
    
    try:
        # Salva arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Converte para formato compatível com Whisper (mp3 ou wav)
        # Whisper aceita webm, mas vamos garantir compatibilidade
        output_path = tmp_path.replace(".webm", ".mp3")
        
        try:
            # Tenta converter usando ffmpeg se disponível
            subprocess.run(
                ["ffmpeg", "-i", tmp_path, "-y", "-acodec", "libmp3lame", output_path],
                check=True,
                capture_output=True
            )
            audio_path = output_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Se ffmpeg não estiver disponível, tenta usar o arquivo original
            audio_path = tmp_path
        
        # Transcreve
        transcription = await transcribe_with_whisper(audio_path)
        
        # Limpa arquivos temporários
        try:
            os.unlink(tmp_path)
            if audio_path != tmp_path:
                os.unlink(audio_path)
        except:
            pass
        
        return JSONResponse(content={"transcription": transcription})
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Erro ao processar áudio: {str(e)}"}
        )

# Endpoint para análise de transcrição
@app.post("/api/analyze")
async def analyze_endpoint(request: Request):
    """Recebe transcrição e retorna análise com IA"""
    try:
        data = await request.json()
        transcription = data.get("transcription", "")
        
        if not transcription:
            return JSONResponse(
                status_code=400,
                content={"error": "Transcrição vazia"}
            )
        
        ai_report = process_with_groq(transcription)
        
        return JSONResponse(content={"resultado": ai_report})
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Erro ao processar análise: {str(e)}"}
        )

# Rota WebSocket (aceita client_id dinâmico)
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    transcription_buffer = []
    
    try:
        while True:
            # Recebe dados do frontend (pode ser texto ou JSON)
            data = await websocket.receive_text()
            
            # Tenta parsear como JSON
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "fim":
                    # Protocolo de Encerramento
                    if not transcription_buffer:
                        await websocket.send_json({
                            "type": "erro",
                            "mensagem": "Nenhuma voz detectada para analisar."
                        })
                    else:
                        await websocket.send_json({
                            "type": "confirmacao",
                            "status": "Processando análise clínica... Aguarde..."
                        })
                        
                        # 1. Junta todo o texto acumulado
                        full_text = " ".join(transcription_buffer)
                        print(f"Texto total capturado: {len(full_text)} caracteres")
                        
                        # 2. Envia para a Groq
                        ai_report = process_with_groq(full_text)
                        
                        # 3. Devolve o relatório para o Frontend em formato JSON
                        await websocket.send_json({
                            "type": "analise_completa",
                            "resultado": ai_report
                        })
                    
                    # Fecha conexão após enviar o relatório
                    break
                    
                elif message_type == "texto":
                    # Recebe texto da transcrição
                    texto = message.get("texto", "").strip()
                    if texto:
                        print(f"Recebido trecho: {texto}")
                        transcription_buffer.append(texto)
                        
            except json.JSONDecodeError:
                # Se não for JSON, trata como texto simples (compatibilidade)
                if data == ">>FINALIZE<<":
                    if not transcription_buffer:
                        await websocket.send_text("Erro: Nenhuma voz detectada para analisar.")
                    else:
                        await websocket.send_text("Processando análise clínica... Aguarde...")
                        
                        full_text = " ".join(transcription_buffer)
                        print(f"Texto total capturado: {len(full_text)} caracteres")
                        
                        ai_report = process_with_groq(full_text)
                        await websocket.send_text(ai_report)
                    
                    break
                else:
                    # Texto simples
                    print(f"Recebido trecho: {data}")
                    transcription_buffer.append(data)
                
    except WebSocketDisconnect:
        print("Cliente desconectado")
    except Exception as e:
        print(f"Erro no WebSocket: {e}")
        try:
            await websocket.send_json({
                "type": "erro",
                "mensagem": str(e)
            })
        except:
            pass