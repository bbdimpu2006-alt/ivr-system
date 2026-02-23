"""
Terminal-based Multi-Language Speech-to-Text
Speak in terminal, get transcription in terminal
"""
import speech_recognition as sr
from dotenv import load_dotenv
import pyaudio
import wave
import io
import threading

load_dotenv()

# Supported languages (9 languages)
SUPPORTED_LANGUAGES = {
    '1': 'en-US',      # English
    '2': 'hi-IN',      # Hindi
    '3': 'te-IN',      # Telugu
    '4': 'ta-IN',      # Tamil
    '5': 'bn-IN',      # Bengali
    '6': 'mr-IN',      # Marathi
    '7': 'gu-IN',      # Gujarati
    '8': 'kn-IN',      # Kannada
    '9': 'ml-IN',      # Malayalam
}

# Microphone index (Realtek Audio) - auto-detect if this fails
MICROPHONE_INDEX = 3


def get_working_microphone():
    """Find a working microphone"""
    mics = sr.Microphone.list_microphone_names()

    # Try specified index first
    try:
        mic = sr.Microphone(device_index=MICROPHONE_INDEX)
        with mic:
            pass  # Just test if it opens
        return MICROPHONE_INDEX
    except:
        pass

    # Try to find Realtek in name
    for i, name in enumerate(mics):
        if 'realtek' in name.lower() or 'audio' in name.lower():
            try:
                mic = sr.Microphone(device_index=i)
                with mic:
                    pass
                return i
            except:
                continue

    # Use default
    return None


def get_microphone_string(index):
    """Get microphone name for display"""
    mics = sr.Microphone.list_microphone_names()
    if index is not None and index < len(mics):
        return mics[index]
    return "Default Microphone"

# Initialize recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8


def show_languages():
    """Display available languages"""
    print("\n" + "=" * 50)
    print("SUPPORTED LANGUAGES")
    print("=" * 50)
    for key, value in SUPPORTED_LANGUAGES.items():
        print(f"  {key:>2}. {value}")
    print("=" * 50)


def select_language():
    """Let user select language"""
    show_languages()
    while True:
        choice = input("\nSelect language (number), or 'q' to quit: ").strip()
        if choice.lower() == 'q':
            return None
        if choice in SUPPORTED_LANGUAGES:
            return SUPPORTED_LANGUAGES[choice]
        print("Invalid choice. Try again.")


def transcribe_speech(language, mic_index, silence_timeout=5):
    """Transcribe speech from microphone

    Args:
        language: Language code for recognition
        mic_index: Microphone device index
        silence_timeout: Seconds of silence before auto-stop (default: 5)

    Returns:
        tuple: (transcribed_text, error_message)

    Note: Recording continues until user presses Enter or 5s of silence
    """
    import time
    import struct
    import numpy as np
    from scipy import signal
    from scipy.ndimage import median_filter

    # Audio settings
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    # Frequency detection settings
    MIN_FREQUENCY = 85      # Lowest human voice frequency (Hz)
    MAX_FREQUENCY = 4000    # Upper limit for voice (includes harmonics)
    ENERGY_THRESHOLD = 30   # Minimum energy in voice frequency range
    
    # Noise filtering settings
    NOISE_FLOOR_DB = -40    # Noise floor in dB
    SPECTRAL_GATE = 0.3     # Spectral gating threshold (0-1)

    print(f"\nRecording... Speak now!")
    print(f"   Press ENTER to stop (or {silence_timeout}s silence)")
    print()

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open microphone stream
    try:
        if mic_index is not None:
            stream = p.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           input_device_index=mic_index,
                           frames_per_buffer=CHUNK)
        else:
            stream = p.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           frames_per_buffer=CHUNK)
    except Exception as e:
        p.terminate()
        return None, f"Error opening microphone: {e}"

    frames = []
    recording = True
    
    # Shared state
    state = {
        'silence_start': None,
        'last_speech_time': None,
        'start_time': time.time(),
        'speech_started': False
    }
    
    # Noise profile (collected during initial silence)
    noise_profile = None
    noise_frames_collected = 0
    NOISE_SAMPLES = 10  # Collect first 10 frames for noise profile

    def collect_noise_profile(data):
        """Collect noise profile from initial frames"""
        nonlocal noise_profile, noise_frames_collected
        audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        
        if noise_profile is None:
            noise_profile = np.zeros_like(audio_data)
        
        noise_profile += np.abs(np.fft.fft(audio_data))
        noise_frames_collected += 1
        
        if noise_frames_collected >= NOISE_SAMPLES:
            noise_profile /= noise_frames_collected

    def apply_noise_filter(data):
        """Apply spectral subtraction and filtering to reduce noise"""
        audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        
        # Apply FFT
        fft_data = np.fft.fft(audio_data)
        magnitude = np.abs(fft_data)
        phase = np.angle(fft_data)
        
        # Spectral subtraction using noise profile
        if noise_profile is not None:
            # Subtract noise spectrum with flooring
            magnitude_filtered = np.maximum(magnitude - SPECTRAL_GATE * noise_profile, 
                                            magnitude * 0.1)  # Spectral floor at 10%
        else:
            magnitude_filtered = magnitude
        
        # Apply bandpass filter for voice frequencies (80Hz - 4000Hz)
        freqs = np.fft.fftfreq(len(audio_data), 1.0/RATE)
        bandpass_mask = (np.abs(freqs) >= MIN_FREQUENCY) & (np.abs(freqs) <= MAX_FREQUENCY)
        magnitude_filtered = magnitude_filtered * bandpass_mask
        
        # Reconstruct signal
        fft_filtered = magnitude_filtered * np.exp(1j * phase)
        filtered_audio = np.fft.ifft(fft_filtered).real.astype(np.int16)
        
        return filtered_audio.tobytes()

    def detect_voice(data):
        """Detect voice based on frequency analysis (FFT) with noise filtering"""
        # Apply noise filter first
        filtered_data = apply_noise_filter(data)
        audio_data = np.frombuffer(filtered_data, dtype=np.int16).astype(np.float32)
        
        # Apply FFT to get frequency spectrum
        fft_data = np.fft.fft(audio_data)
        freqs = np.fft.fftfreq(len(audio_data), 1.0/RATE)
        
        # Get magnitude spectrum (only positive frequencies)
        magnitude = np.abs(fft_data[:len(fft_data)//2])
        pos_freqs = freqs[:len(freqs)//2]
        
        # Filter for human voice frequency range (fundamental + harmonics)
        voice_mask = (pos_freqs >= MIN_FREQUENCY) & (pos_freqs <= MAX_FREQUENCY)
        voice_energy = np.sum(magnitude[voice_mask])
        
        # Also check energy in fundamental frequency range (85-255 Hz)
        fundamental_mask = (pos_freqs >= 85) & (pos_freqs <= 255)
        fundamental_energy = np.sum(magnitude[fundamental_mask])
        
        # Voice detected if either total voice energy or fundamental energy is high
        return (voice_energy > ENERGY_THRESHOLD * 100) or (fundamental_energy > ENERGY_THRESHOLD * 50)

    def record():
        """Record audio in background with frequency-based silence detection"""
        nonlocal noise_frames_collected
        while recording:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                
                # Collect noise profile during first few frames
                if noise_frames_collected < NOISE_SAMPLES:
                    collect_noise_profile(data)
                
                # Apply noise filtering and store filtered audio
                filtered_data = apply_noise_filter(data)
                frames.append(filtered_data)

                # Detect voice using frequency analysis
                if detect_voice(data):
                    if not state['speech_started']:
                        state['speech_started'] = True
                    state['last_speech_time'] = time.time()
                    state['silence_start'] = None
                else:
                    if state['speech_started'] and state['silence_start'] is None:
                        state['silence_start'] = time.time()
            except:
                break

    # Start recording thread
    record_thread = threading.Thread(target=record)
    record_thread.start()

    # Monitor for silence timeout or user input
    input_received = threading.Event()

    def wait_for_input():
        input()
        input_received.set()

    input_thread = threading.Thread(target=wait_for_input, daemon=True)
    input_thread.start()

    # Check for silence timeout in main thread
    while recording:
        # Timeout if no speech at start (5 seconds)
        if not state['speech_started'] and time.time() - state['start_time'] > silence_timeout:
            recording = False
            print(f"\nNo speech detected ({silence_timeout}s), stopping...")
            break
        # Timeout if silence after speech (5 seconds)
        if state['speech_started'] and state['silence_start'] is not None and time.time() - state['silence_start'] > silence_timeout:
            recording = False
            print(f"\nSilence detected ({silence_timeout}s), stopping...")
            break
        if input_received.is_set():
            recording = False
            break
        time.sleep(0.1)

    record_thread.join(timeout=1)

    # Stop and close stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    if not frames:
        return None, "No audio captured"

    print("\nProcessing speech...")

    # Convert to WAV format in memory
    wav_buffer = io.BytesIO()
    wf = wave.open(wav_buffer, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Recognize speech
    try:
        wav_buffer.seek(0)
        with sr.AudioFile(wav_buffer) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language=language)
        return text, None
    except sr.UnknownValueError:
        return None, "Could not understand audio. Please try again."
    except sr.RequestError as e:
        return None, f"API Error: {e}"
    except Exception as e:
        return None, f"Error: {e}"


def main():
    """Main loop"""
    print("\n" + "=" * 50)
    print("MULTI-LANGUAGE SPEECH-TO-TEXT (TERMINAL)")
    print("=" * 50)

    # Find working microphone
    mic_index = get_working_microphone()

    language = select_language()
    if not language:
        print("Goodbye!")
        return

    print(f"\nLanguage set to: {language}")
    print("\nCommands:")
    print("  - Just speak, transcription appears automatically")
    print("  - Type 'lang' to change language")
    print("  - Type 'quit' or 'q' to exit")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nPress Enter to speak (or type command): ").strip()

            if user_input.lower() in ['quit', 'q', 'exit']:
                print("\nGoodbye!")
                break
            elif user_input.lower() == 'lang':
                language = select_language()
                if not language:
                    print("\nGoodbye!")
                    break
                print(f"\nLanguage set to: {language}")
                continue
            elif user_input == '':
                text, error = transcribe_speech(language, mic_index)
                if error:
                    print(f"Error: {error}")
                else:
                    print("\n" + "=" * 50)
                    print(f"TRANSCRIPTION ({language})")
                    print("=" * 50)
                    print(f"   {text}")
                    print("=" * 50)
            else:
                print("Unknown command. Press Enter to speak, 'lang' to change language, 'q' to quit.")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == '__main__':
    main()
