#!/usr/bin/env python3
"""Script simplificado para iniciar o servidor"""
import sys
import os

# Verifica se estamos no diretório correto
if not os.path.exists("templates/index.html"):
    print("❌ Erro: templates/index.html não encontrado!")
    print("   Certifique-se de estar no diretório do projeto")
    sys.exit(1)

# Tenta importar
try:
    print("Carregando módulos...")
    from main import app
    import uvicorn
    print("✓ Módulos carregados com sucesso")
except Exception as e:
    print(f"❌ Erro ao carregar módulos: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Inicia servidor
print("\n" + "="*60)
print("🚀 SERVIDOR INICIANDO")
print("="*60)
print("📍 URL: http://localhost:8000")
print("📍 URL: http://127.0.0.1:8000")
print("📍 URL: http://0.0.0.0:8000")
print("="*60)
print("Pressione Ctrl+C para parar\n")

try:
    uvicorn.run(
        app, 
        host="127.0.0.1",  # Usando 127.0.0.1 em vez de 0.0.0.0
        port=8000, 
        reload=False,  # Desabilitando reload para evitar problemas
        log_level="info"
    )
except KeyboardInterrupt:
    print("\n\nServidor parado pelo usuário")
except Exception as e:
    print(f"\n\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
