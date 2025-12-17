#!/usr/bin/env python3
"""Script de teste para verificar se o servidor inicia corretamente"""
import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("1. Testando importações...")
    from fastapi import FastAPI
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse
    from fastapi.requests import Request
    import uvicorn
    print("   ✓ Importações OK")
    
    print("2. Testando criação do app...")
    app = FastAPI()
    templates = Jinja2Templates(directory="templates")
    print("   ✓ App criado")
    
    print("3. Testando rota...")
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    print("   ✓ Rota configurada")
    
    print("4. Iniciando servidor...")
    print("   Servidor será iniciado em http://0.0.0.0:8000")
    print("   Acesse http://localhost:8000 no navegador")
    print("   Pressione Ctrl+C para parar\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("   Execute: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
