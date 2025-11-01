# MedIA - Transcrição de Áudio com Whisper

Script CLI para transcrição de áudio usando o modelo Whisper da OpenAI.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

### Transcrever arquivo de áudio

```bash
python rt_transcribe.py --file caminho/para/audio.mp3
```

### Salvar transcrição em arquivo

```bash
python rt_transcribe.py --file audio.mp3 --output resultado.txt
```

### Especificar modelo e idioma

```bash
python rt_transcribe.py --file audio.mp3 --model base --language en
```

### Modo tempo real (microfone)

```bash
python rt_transcribe.py --realtime
```

### Ver ajuda

```bash
python rt_transcribe.py --help
```

## Opções Disponíveis

- `--file` ou `-f`: Caminho do arquivo de áudio para transcrever
- `--realtime` ou `-r`: Modo de transcrição em tempo real do microfone
- `--model` ou `-m`: Tamanho do modelo Whisper (tiny, base, small, medium, large). Padrão: tiny
- `--language` ou `-l`: Idioma para transcrição (padrão: pt). Use códigos ISO 639-1 (pt, en, es, etc.)
- `--output` ou `-o`: Arquivo de saída para salvar a transcrição

## Formatos de Áudio Suportados

MP3, WAV, FLAC, M4A, OGG e outros formatos comuns.

## Modelos Whisper

- `tiny`: Mais rápido, menor precisão
- `base`: Equilíbrio entre velocidade e precisão
- `small`: Melhor precisão, mais lento
- `medium`: Alta precisão, muito lento
- `large`: Máxima precisão, muito lento

O modelo padrão é `tiny`. Modelos maiores oferecem melhor precisão mas são significativamente mais lentos.

## Pré-requisitos

### ffmpeg (Obrigatório)

O Whisper requer o ffmpeg para processar arquivos de áudio. Certifique-se de que está instalado:

**Windows:**
```bash
# Verificar se está instalado
ffmpeg -version

# Se não estiver, baixe de: https://ffmpeg.org/download.html
# Ou use Chocolatey: choco install ffmpeg
# Ou use winget: winget install ffmpeg
```

**Linux:**
```bash
sudo dnf install ffmpeg  # Fedora
sudo apt-get install ffmpeg  # Ubuntu/Debian
```

**macOS:**
```bash
brew install ffmpeg
```

## Troubleshooting

### Erro "winderror2" ou "arquivo não encontrado" no Windows

Este erro geralmente ocorre por:

1. **Caminho do arquivo incorreto**
   - Use caminho absoluto com aspas: `python rt_transcribe.py --file "C:\pasta\arquivo.mp3"`
   - Se o arquivo está no mesmo diretório: `python rt_transcribe.py --file .\arquivo.mp3`

2. **ffmpeg não instalado ou não no PATH**
   - Verifique: `ffmpeg -version` no CMD
   - Se não funcionar, reinstale o ffmpeg e adicione ao PATH do sistema

3. **Espaços no caminho**
   - Sempre use aspas: `--file "C:\Minha Pasta\arquivo.mp3"`

4. **Caminho relativo não funciona**
   - Tente usar caminho absoluto completo
   - Ou navegue até o diretório do arquivo antes de executar

### Exemplo de uso no Windows

```cmd
# Com caminho absoluto
python rt_transcribe.py --file "C:\Users\Usuario\Musicas\audio.mp3"

# Com caminho relativo (se estiver no mesmo diretório)
cd C:\pasta\com\audio
python rt_transcribe.py --file audio.mp3

# Com espaços no caminho (sempre usar aspas)
python rt_transcribe.py --file "C:\Minha Pasta\Meu Audio.mp3"
```

