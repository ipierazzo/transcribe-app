#!/usr/bin/env python3
"""Script de diagnóstico para verificar problemas de conexão"""
import sys
import socket
import requests
from urllib.parse import urlparse

def verificar_porta(host, porta):
    """Verifica se uma porta está aberta"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        resultado = sock.connect_ex((host, porta))
        sock.close()
        return resultado == 0
    except Exception as e:
        print(f"   Erro ao verificar porta: {e}")
        return False

def verificar_servidor(url):
    """Verifica se o servidor está respondendo"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200, response.text
    except requests.exceptions.ConnectionError:
        return False, "Erro de conexão - servidor não está rodando"
    except requests.exceptions.Timeout:
        return False, "Timeout - servidor não respondeu a tempo"
    except Exception as e:
        return False, f"Erro: {e}"

def main():
    print("=" * 60)
    print("DIAGNÓSTICO DO SERVIDOR medIA")
    print("=" * 60)
    
    # Verifica porta 8000
    print("\n1. Verificando porta 8000...")
    if verificar_porta('localhost', 8000):
        print("   ✅ Porta 8000 está aberta")
    else:
        print("   ❌ Porta 8000 não está aberta")
        print("   → O servidor provavelmente não está rodando")
        print("   → Execute: python main.py")
        return
    
    # Verifica endpoint health
    print("\n2. Verificando endpoint /health...")
    ok, msg = verificar_servidor("http://localhost:8000/health")
    if ok:
        print(f"   ✅ Servidor está respondendo: {msg}")
    else:
        print(f"   ❌ Servidor não está respondendo: {msg}")
        return
    
    # Verifica endpoint raiz
    print("\n3. Verificando endpoint / (raiz)...")
    ok, msg = verificar_servidor("http://localhost:8000/")
    if ok:
        print("   ✅ Página principal está acessível")
    else:
        print(f"   ❌ Página principal não está acessível: {msg}")
    
    # Verifica WebSocket (básico)
    print("\n4. Verificando suporte WebSocket...")
    try:
        import websockets
        print("   ✅ Biblioteca websockets está instalada")
    except ImportError:
        print("   ⚠️  Biblioteca websockets não está instalada")
        print("   → Execute: pip install websockets")
    
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("=" * 60)
    print("\nSe todos os testes passaram, o servidor está funcionando.")
    print("Se houver problemas, verifique:")
    print("  1. Se o servidor está rodando (python main.py)")
    print("  2. Se a porta 8000 não está sendo usada por outro processo")
    print("  3. Se há erros no console do servidor")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnóstico interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante diagnóstico: {e}")
        import traceback
        traceback.print_exc()
