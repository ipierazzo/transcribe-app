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

