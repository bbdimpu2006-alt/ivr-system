"""
Terminal-based Multi-Language Speech-to-Text
Speak in terminal, get transcription in terminal
"""
import speech_recognition as sr
from dotenv import load_dotenv

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
            pass
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


def transcribe_speech(language, mic_index):
    """Transcribe speech from microphone"""
    try:
        if mic_index is not None:
            mic = sr.Microphone(device_index=mic_index)
        else:
            mic = sr.Microphone()

        with mic as source:
            mic_name = get_microphone_string(mic_index)
            print(f"\n🎤 Using: {mic_name}")
            print("⏳ Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"✅ Ready! Speak now...")
            print("   (Silence for 5s will end)")

            audio = recognizer.listen(source, timeout=5, phrase_time_limit=None)
            print("\n⏳ Processing speech...")

        text = recognizer.recognize_google(audio, language=language)
        return text, None

    except sr.WaitTimeoutError:
        return None, "No speech detected (timed out)"
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

    print(f"\n✅ Language set to: {language}")
    print("\nCommands:")
    print("  - Just speak, transcription appears automatically")
    print("  - Type 'lang' to change language")
    print("  - Type 'quit' or 'q' to exit")
    print("-" * 50)

    while True:
        try:
            user_input = input("\n📝 Press Enter to speak (or type command): ").strip()

            if user_input.lower() in ['quit', 'q', 'exit']:
                print("\nGoodbye!")
                break
            elif user_input.lower() == 'lang':
                language = select_language()
                if not language:
                    print("\nGoodbye!")
                    break
                print(f"\n✅ Language set to: {language}")
                continue
            elif user_input == '':
                text, error = transcribe_speech(language, mic_index)
                if error:
                    print(f"❌ {error}")
                else:
                    print("\n" + "=" * 50)
                    print(f"📄 TRANSCRIPTION ({language})")
                    print("=" * 50)
                    print(f"   {text}")
                    print("=" * 50)
            else:
                print("Unknown command. Press Enter to speak, 'lang' to change language, 'q' to quit.")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == '__main__':
    main()
