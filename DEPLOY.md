# Guia de Deploy no Render.com

Este guia explica como fazer o deploy do projeto medIA no Render.com.

## 📋 Pré-requisitos

1. Conta no [Render.com](https://render.com) (gratuita)
2. Conta no [Groq Console](https://console.groq.com) com API Key
3. (Opcional) Conta na OpenAI para usar Whisper

## 🚀 Passo a Passo

### 1. Preparar o Repositório

Certifique-se de que seu código está em um repositório Git (GitHub, GitLab ou Bitbucket).

### 2. Criar Novo Serviço no Render

1. Acesse [Render Dashboard](https://dashboard.render.com)
2. Clique em **"New +"** → **"Web Service"**
3. Conecte seu repositório Git
4. Selecione o repositório do projeto medIA

### 3. Configurar o Serviço

**Configurações Básicas:**
- **Name**: `medIA` (ou o nome que preferir)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Ou use o arquivo `render.yaml`:**
- Render detectará automaticamente o arquivo `render.yaml` na raiz do projeto
- As configurações serão aplicadas automaticamente

### 4. Configurar Variáveis de Ambiente

No painel do serviço, vá em **"Environment"** e adicione:

**Obrigatório:**
- `GROQ_API_KEY`: Sua chave da API Groq (obtenha em https://console.groq.com/)

**Opcional (para usar Whisper):**
- `OPENAI_API_KEY`: Sua chave da API OpenAI (se quiser usar Whisper para transcrição)

### 5. Deploy

1. Clique em **"Create Web Service"**
2. Render iniciará o build e deploy automaticamente
3. Aguarde o processo concluir (pode levar alguns minutos)
4. Quando concluir, você verá a URL do seu serviço (ex: `https://media.onrender.com`)

## 🔧 Configurações Avançadas

### Usando render.yaml (Recomendado)

O arquivo `render.yaml` já está configurado. Basta:

1. Fazer commit do arquivo no repositório
2. No Render, ao criar o serviço, selecione **"Apply render.yaml"**
3. As configurações serão aplicadas automaticamente

### Health Check

O Render verificará automaticamente se o serviço está funcionando através do endpoint `/`.

### Auto-Deploy

Por padrão, o Render faz deploy automático a cada push para a branch principal.

Para desabilitar:
- Vá em **Settings** → **Auto-Deploy**
- Desmarque a opção

## ⚠️ Notas Importantes

### Plano Gratuito

- O serviço pode "dormir" após 15 minutos de inatividade
- O primeiro acesso após dormir pode levar 30-60 segundos
- Para evitar isso, considere o plano pago

### WebSockets

- Render suporta WebSockets no plano gratuito
- Certifique-se de que a URL usa `wss://` (WebSocket seguro) em produção

### Limites

- **Build Time**: 45 minutos (plano gratuito)
- **Memory**: 512 MB (plano gratuito)
- **CPU**: Compartilhado (plano gratuito)

## 🐛 Troubleshooting

### Erro: "Module not found"

- Verifique se todas as dependências estão no `requirements.txt`
- Verifique os logs do build no Render

### Erro: "GROQ_API_KEY not found"

- Verifique se a variável de ambiente está configurada no Render
- Nome da variável deve ser exatamente `GROQ_API_KEY`

### Serviço não inicia

- Verifique os logs em **"Logs"** no painel do Render
- Certifique-se de que o `startCommand` está correto
- Verifique se a porta está usando `$PORT` (variável do Render)

### WebSocket não funciona

- Certifique-se de usar `wss://` em vez de `ws://` na URL
- Verifique se o Render está usando HTTPS (padrão)

## 📝 Checklist de Deploy

- [ ] Código commitado no repositório Git
- [ ] `render.yaml` está na raiz do projeto
- [ ] `requirements.txt` está atualizado
- [ ] Variável `GROQ_API_KEY` configurada no Render
- [ ] (Opcional) Variável `OPENAI_API_KEY` configurada
- [ ] Build Command configurado: `pip install -r requirements.txt`
- [ ] Start Command configurado: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Testado localmente antes do deploy

## 🔗 Links Úteis

- [Documentação Render](https://render.com/docs)
- [Render Status](https://status.render.com)
- [Groq Console](https://console.groq.com)
- [OpenAI API](https://platform.openai.com)

## 💡 Dicas

1. **Teste localmente primeiro**: Use `uvicorn main:app --host 0.0.0.0 --port 8000` para testar
2. **Monitore os logs**: Use a aba "Logs" no Render para debug
3. **Use variáveis de ambiente**: Nunca commite chaves de API no código
4. **Backup**: Mantenha backup das variáveis de ambiente em local seguro
