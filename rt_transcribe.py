import sounddevice as sd
import numpy as np
import whisper
import queue
import threading
import time
import argparse
import sys
import os

def load_model(model_size="tiny"):
    """Load Whisper model with fallback."""
    print(f"Carregando modelo Whisper '{model_size}'...")
    try:
        model = whisper.load_model(model_size)
        print(f"Modelo '{model_size}' carregado com sucesso!")
        return model
    except Exception as e:
        print(f"Erro ao carregar modelo '{model_size}': {e}")
        if model_size != "tiny":
            print("Tentando carregar modelo 'tiny'...")
            return load_model("tiny")
        else:
            print("Tentando carregar modelo 'base'...")
            try:
                model = whisper.load_model("base")
                print("Modelo 'base' carregado com sucesso!")
                return model
            except Exception as e2:
                print(f"Erro ao carregar modelo 'base': {e2}")
                sys.exit(1)

# Audio parameters
SAMPLE_RATE = 16000
BUFFER_SIZE = 1024
CHUNK_DURATION = 3  # seconds of audio to accumulate before transcribing
audio_queue = queue.Queue()
audio_buffer = []

def audio_callback(indata, frames, time, status):
    """Callback function to capture audio data."""
    if status:
        print(f"Audio status: {status}")
    audio_queue.put(indata.copy())

def detect_audio_activity(audio_data, threshold=0.005):
    """Detect if there's significant audio activity."""
    # Calculate RMS (Root Mean Square) to detect audio level
    rms = np.sqrt(np.mean(audio_data**2))
    return rms > threshold

def show_progress_indicator(stop_event):
    """Mostra indicador de progresso enquanto transcreve."""
    # Usar caracteres ASCII simples para compatibilidade com Windows CMD
    indicators = ["|", "/", "-", "\\"]
    messages = [
        "Processando áudio",
        "Analisando conteúdo",
        "Transcrevendo",
        "Finalizando"
    ]
    i = 0
    dots = ""
    while not stop_event.is_set():
        indicator = indicators[i % len(indicators)]
        message = messages[(i // 4) % len(messages)]
        dots = "." * ((i // 2) % 4)
        print(f"\r[ {indicator} ] {message}{dots}", end="", flush=True)
        i += 1
        time.sleep(0.3)

def transcribe_file(file_path, model, language="pt", output_file=None, model_name="tiny"):
    """Transcribe an audio file."""
    # Normalizar caminho do arquivo (importante para Windows)
    file_path = os.path.abspath(os.path.normpath(file_path))
    
    if not os.path.exists(file_path):
        print(f"❌ Arquivo não encontrado: {file_path}")
        print(f"📁 Diretório atual: {os.getcwd()}")
        print(f"📋 Listando arquivos no diretório atual:")
        try:
            for f in os.listdir('.'):
                print(f"   - {f}")
        except Exception as e:
            print(f"   Erro ao listar diretório: {e}")
        sys.exit(1)
    
    # Verificar se é um arquivo (não diretório)
    if not os.path.isfile(file_path):
        print(f"❌ Caminho especificado não é um arquivo: {file_path}")
        sys.exit(1)
    
    file_size_mb = os.path.getsize(file_path) / (1024*1024)
    file_name = os.path.basename(file_path)
    
    # Informações do arquivo
    print("\n" + "="*60)
    print("📋 INFORMAÇÕES DO ARQUIVO")
    print("="*60)
    print(f"📂 Arquivo: {file_name}")
    print(f"📁 Caminho: {file_path}")
    print(f"📏 Tamanho: {file_size_mb:.2f} MB")
    print(f"🌐 Idioma: {language.upper()}")
    print(f"🤖 Modelo: {model_name}")
    print("="*60)
    print("\n🎤 INICIANDO TRANSCRIÇÃO...")
    print("⏳ Isso pode levar alguns minutos dependendo do tamanho do arquivo...")
    print("💡 Aguarde enquanto processamos o áudio...\n")
    
    start_time = time.time()
    stop_event = threading.Event()
    
    # Iniciar indicador de progresso em thread separada
    progress_thread = threading.Thread(target=show_progress_indicator, args=(stop_event,), daemon=True)
    progress_thread.start()
    
    try:
        # Usar caminho absoluto normalizado para evitar problemas no Windows
        result = model.transcribe(file_path, language=language)
        
        # Parar indicador de progresso
        stop_event.set()
        progress_thread.join(timeout=0.5)
        
        elapsed_time = time.time() - start_time
        
        print(f"\r✅ Transcrição concluída em {elapsed_time:.1f} segundos!{' ' * 50}")
        print("="*60)
        text = result['text'].strip()
        
        if text:
            print("\n" + "="*60)
            print("📝 TRANSCRIÇÃO:")
            print("="*60)
            print(text)
            print("="*60)
            
            # Save to file if output_file is specified
            if output_file:
                try:
                    # Normalizar caminho de saída também
                    output_file = os.path.abspath(os.path.normpath(output_file))
                    # Criar diretório se não existir
                    output_dir = os.path.dirname(output_file)
                    if output_dir and not os.path.exists(output_dir):
                        os.makedirs(output_dir, exist_ok=True)
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"\n💾 Transcrição salva em: {output_file}")
                except Exception as e:
                    print(f"❌ Erro ao salvar arquivo: {e}")
        else:
            print("🔇 Nenhuma fala detectada no áudio")
            
    except FileNotFoundError as e:
        print(f"❌ Erro: Arquivo ou dependência não encontrada")
        print(f"   Detalhes: {e}")
        print(f"\n💡 Possíveis soluções:")
        print(f"   1. Verifique se o arquivo existe: {file_path}")
        print(f"   2. No Windows, certifique-se de que o ffmpeg está instalado e no PATH")
        print(f"   3. Tente usar o caminho completo do arquivo (ex: C:\\pasta\\arquivo.mp3)")
        print(f"   4. Verifique se há espaços no caminho e use aspas se necessário")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erro na transcrição: {error_msg}")
        
        # Dicas específicas para Windows
        if "winderror" in error_msg.lower() or "cannot find" in error_msg.lower():
            print(f"\n💡 Este erro geralmente indica:")
            print(f"   1. Arquivo não encontrado ou caminho incorreto")
            print(f"   2. ffmpeg não instalado ou não no PATH")
            print(f"   3. Problema com espaços ou caracteres especiais no caminho")
            print(f"\n🔧 Soluções:")
            print(f"   - Use caminho absoluto: python rt_transcribe.py --file \"C:\\caminho\\completo\\arquivo.mp3\"")
            print(f"   - Verifique instalação do ffmpeg: ffmpeg -version")
            print(f"   - Tente mover o arquivo para um caminho sem espaços")
        
        sys.exit(1)

def transcribe_realtime(model, language="pt"):
    """Thread to transcribe audio in real time."""
    global audio_buffer
    
    while True:
        try:
            # Collect audio data for a few seconds
            start_time = time.time()
            audio_detected = False
            
            while time.time() - start_time < CHUNK_DURATION:
                if not audio_queue.empty():
                    audio_data = audio_queue.get()
                    audio_buffer.append(audio_data.copy())
                    
                    # Check if this chunk has audio activity
                    if detect_audio_activity(audio_data.flatten()):
                        audio_detected = True
                        
                time.sleep(0.1)  # Small delay to prevent busy waiting
            
            if audio_buffer and audio_detected:
                # Combine all buffered audio
                combined_audio = np.concatenate(audio_buffer)
                audio_buffer.clear()
                
                # Only transcribe if we have enough audio data and detected activity
                if len(combined_audio) > SAMPLE_RATE:  # At least 1 second of audio
                    print("🎤 Transcribing...")
                    try:
                        # Transcribe the audio
                        result = model.transcribe(combined_audio.flatten(), language=language)
                        text = result['text'].strip()
                        if text:
                            print(f"📝 Transcrição: {text}")
                        else:
                            print("🔇 Nenhuma fala detectada")
                    except Exception as e:
                        print(f"❌ Erro na transcrição: {e}")
                else:
                    print("🔇 Áudio insuficiente para transcrição")
            elif audio_buffer:
                # Clear buffer if no audio was detected
                audio_buffer.clear()
                
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            time.sleep(1)

def main_realtime(model, language="pt"):
    """Main function to start real-time transcription."""
    print("Iniciando sistema de transcrição em tempo real...")
    
    # Start the transcription thread
    transcription_thread = threading.Thread(target=transcribe_realtime, args=(model, language), daemon=True)
    transcription_thread.start()
    
    # Start capturing audio from the microphone
    try:
        with sd.InputStream(callback=audio_callback, channels=1, samplerate=SAMPLE_RATE, blocksize=BUFFER_SIZE):
            print("Escutando... Pressione Ctrl+C para parar.")
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nParando...")
    except Exception as e:
        print(f"Erro: {e}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Transcrição de áudio usando Whisper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python rt_transcribe.py --file audio.mp3
  python rt_transcribe.py --file audio.mp3 --output resultado.txt
  python rt_transcribe.py --file audio.mp3 --model base --language en
  python rt_transcribe.py --realtime --model tiny
        """
    )
    
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Caminho do arquivo de áudio para transcrever'
    )
    
    parser.add_argument(
        '--realtime', '-r',
        action='store_true',
        help='Modo de transcrição em tempo real do microfone'
    )
    
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='tiny',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Tamanho do modelo Whisper (padrão: tiny)'
    )
    
    parser.add_argument(
        '--language', '-l',
        type=str,
        default='pt',
        help='Idioma para transcrição (padrão: pt). Use códigos ISO 639-1 (pt, en, es, etc.)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Arquivo de saída para salvar a transcrição'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.file and not args.realtime:
        parser.error("Você deve especificar --file ou --realtime")
    
    if args.file and args.realtime:
        parser.error("Use apenas --file ou --realtime, não ambos")
    
    return args

def main():
    """Main entry point."""
    args = parse_args()
    
    # Load model
    model = load_model(args.model)
    
    # Process file or realtime
    if args.file:
        transcribe_file(args.file, model, args.language, args.output, args.model)
    elif args.realtime:
        main_realtime(model, args.language)

if __name__ == "__main__":
    main()