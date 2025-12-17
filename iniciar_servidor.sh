#!/bin/bash

echo "=========================================="
echo "Iniciando servidor medIA"
echo "=========================================="
echo ""

# Verifica se está no diretório correto
if [ ! -f "main.py" ]; then
    echo "❌ Erro: main.py não encontrado!"
    echo "   Execute este script no diretório do projeto"
    exit 1
fi

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: Python3 não encontrado!"
    exit 1
fi

# Verifica dependências básicas
echo "Verificando dependências..."
python3 -c "import fastapi" 2>/dev/null || {
    echo "❌ FastAPI não está instalado"
    echo "   Execute: pip install -r requirements.txt"
    exit 1
}

echo "✅ Dependências OK"
echo ""

# Inicia o servidor
echo "Iniciando servidor na porta 8000..."
echo "Acesse: http://localhost:8000"
echo "Pressione Ctrl+C para parar"
echo ""

python3 main.py
