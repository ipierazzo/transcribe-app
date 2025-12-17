# Sistema de Transcrição de Áudio em Tempo Real com Análise de IA

MVP completo para transcrição de consultas longas (60-80 minutos) com análise usando Groq API.

## 🚀 Características

- **Transcrição em Tempo Real**: Usa Web Speech API nativa do navegador
- **Análise com IA**: Processa transcrições completas com Groq (llama-3.3-70b-versatile)
- **Interface Moderna**: UI responsiva com TailwindCSS
- **Reconexão Automática**: Reinicia reconhecimento de voz automaticamente
- **WebSocket**: Comunicação em tempo real entre frontend e backend

## 📋 Pré-requisitos

- Python 3.8+
- Navegador moderno com suporte a Web Speech API (Chrome, Edge, Safari)
- Chave da API Groq (obtenha em: https://console.groq.com/)

## 🔧 Instalação

1. **Clone ou navegue até o diretório do projeto**

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure a chave da API Groq:**
   
   Crie um arquivo `.env` na raiz do projeto:
```bash
GROQ_API_KEY=sua_chave_groq_aqui
GROQ_MODEL=llama-3.3-70b-versatile  # Opcional: modelo a ser usado (padrão: llama-3.3-70b-versatile)

# Opcional: Personalize o prompt do sistema para análise
SYSTEM_PROMPT="Você é um Médico Endocrinologista Sênior. Analise a transcrição e gere um relatório SOAP completo e documentos para emissão."
```

   **Nota sobre SYSTEM_PROMPT:**
   - Se não definido, será usado o prompt padrão
   - Você pode usar múltiplas linhas no .env usando aspas
   - O prompt define como a IA analisa as transcrições

   **Modelos alternativos disponíveis:**
   - `llama-3.3-70b-versatile` (padrão, recomendado)
   - `llama-3.1-8b-instant` (mais rápido, menor custo)
   - `mixtral-8x7b-32768` (alternativa)
   - `gemma2-9b-it` (alternativa)
   
   Consulte https://console.groq.com/docs/models para modelos atualizados.

## 🎯 Como Usar

1. **Inicie o servidor:**
```bash
python main.py
```

   Ou usando uvicorn diretamente:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Acesse a interface:**
   Abra seu navegador em: `http://localhost:8000`

3. **Use o sistema:**
   - Clique em "Iniciar Gravação" para começar a transcrever
   - A transcrição aparecerá em tempo real na tela
   - Clique em "Parar e Analisar" para processar com a IA
   - A análise estruturada aparecerá na área de resultado

## 📁 Estrutura do Projeto

```
medIA/
├── main.py              # Backend FastAPI com WebSocket
├── requirements.txt     # Dependências Python
├── .env                 # Variáveis de ambiente (criar manualmente)
├── templates/
│   └── index.html      # Interface frontend
└── README.md           # Este arquivo
```

## 🔌 Endpoints

- `GET /`: Interface web
- `WebSocket /ws/{client_id}`: Conexão para receber transcrições

## 🛠️ Tecnologias

- **Backend**: FastAPI, Uvicorn, WebSockets
- **Frontend**: HTML5, JavaScript (Web Speech API), TailwindCSS
- **IA**: Groq SDK (Model: llama-3.3-70b-versatile)

## ⚠️ Notas Importantes

- A Web Speech API funciona melhor no Chrome/Edge
- O reconhecimento pode parar automaticamente após períodos de silêncio - o sistema reinicia automaticamente
- Certifique-se de ter uma conexão estável com a internet para a API Groq
- O sistema acumula transcrições em memória durante a sessão

## 🚀 Deploy

Este projeto está preparado para deploy no Render.com. Veja o guia completo em [DEPLOY.md](./DEPLOY.md).

**Deploy rápido:**
1. Faça push do código para um repositório Git
2. Crie um novo Web Service no Render.com
3. Configure as variáveis de ambiente (`GROQ_API_KEY` e opcionalmente `OPENAI_API_KEY`)
4. Use o arquivo `render.yaml` para configuração automática

## 📝 Licença

Este é um projeto MVP para demonstração.

