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

def transcribe_file(file_path, model, language="pt", output_file=None):
    """Transcribe an audio file."""
    if not os.path.exists(file_path):
        print(f"❌ Arquivo não encontrado: {file_path}")
        sys.exit(1)
    
    print(f"📂 Processando arquivo: {file_path}")
    print("🎤 Transcrevendo...")
    
    try:
        result = model.transcribe(file_path, language=language)
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
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"\n💾 Transcrição salva em: {output_file}")
                except Exception as e:
                    print(f"❌ Erro ao salvar arquivo: {e}")
        else:
            print("🔇 Nenhuma fala detectada no áudio")
            
    except Exception as e:
        print(f"❌ Erro na transcrição: {e}")
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
        transcribe_file(args.file, model, args.language, args.output)
    elif args.realtime:
        main_realtime(model, args.language)

if __name__ == "__main__":
    main()