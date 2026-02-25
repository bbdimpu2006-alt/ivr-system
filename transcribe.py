"""
Terminal-based Multi-Language Speech-to-Text
Accurate transcription with noise filtering
"""
import speech_recognition as sr
from dotenv import load_dotenv
import sys
import time

load_dotenv()

# Supported languages (9 Indian languages + English)
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

# Microphone index (set to 2 for Realtek Audio)
MICROPHONE_INDEX = 2


class Transcriber:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Optimized settings for accurate speech recognition
        self.recognizer.energy_threshold = 350  # Balanced - filters background noise
        self.recognizer.dynamic_energy_threshold = True  # Auto-adjusts to environment
        self.recognizer.dynamic_energy_adjustment_damping = 0.15  # Smooth adjustments
        self.recognizer.dynamic_energy_ratio = 0.65  # Sensitivity ratio
        self.recognizer.pause_threshold = 1.0  # Longer pause = complete phrase
        self.recognizer.phrase_threshold = 0.5  # Min 0.5s of speech required
        self.recognizer.non_speaking_duration = 0.5  # Buffer before/after speech
        self.mic_index = self.get_working_microphone()

    def get_working_microphone(self):
        """Find and test microphone"""
        mics = sr.Microphone.list_microphone_names()

        print(f"\n📋 Available microphones ({len(mics)}):")
        for i, name in enumerate(mics):
            print(f"   {i}: {name}")

        # Try specified index first
        if MICROPHONE_INDEX is not None and MICROPHONE_INDEX < len(mics):
            try:
                mic = sr.Microphone(device_index=MICROPHONE_INDEX)
                with mic:
                    pass
                print(f"✓ Using: {mics[MICROPHONE_INDEX]}\n")
                return MICROPHONE_INDEX
            except Exception as e:
                print(f"  Index {MICROPHONE_INDEX} failed: {e}")

        # Auto-detect common mics
        keywords = ['realtek', 'microphone', 'usb', 'headset', 'headphone', 'audio']
        for i, name in enumerate(mics):
            name_lower = name.lower()
            if any(kw in name_lower for kw in keywords):
                try:
                    mic = sr.Microphone(device_index=i)
                    with mic:
                        pass
                    print(f"✓ Using: {name}\n")
                    return i
                except:
                    continue

        # Fallback to default
        print("✓ Using default microphone\n")
        return None

    def transcribe_speech(self, language, retries=2):
        """
        Transcribe speech with retry logic for better accuracy

        Args:
            language: Language code (e.g., 'te-IN')
            retries: Number of retry attempts on failure

        Returns:
            tuple: (transcribed_text, error_message)
        """
        for attempt in range(1, retries + 1):
            try:
                with sr.Microphone(device_index=self.mic_index) as source:
                    # Set source energy level
                    source.gain = 10  # Boost input signal

                    print(f"\n🎤 Listening... (speak clearly, 5s timeout)")
                    sys.stdout.flush()

                    # Ambient noise calibration
                    print("  calibrating for noise...", end='', flush=True)
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.7)
                    print(" done")

                    try:
                        # Listen for speech
                        audio = self.recognizer.listen(
                            source,
                            timeout=5,  # Wait 5s for speech to start
                            phrase_time_limit=5  # Max 5s of recording
                        )

                        print("⏳ Recognizing...")
                        sys.stdout.flush()

                        # Recognize with Google
                        text = self.recognizer.recognize_google(audio, language=language)
                        return text, None

                    except sr.WaitTimeoutError:
                        if attempt < retries:
                            print("⚠️  No speech detected, try again...")
                            time.sleep(0.5)
                            continue
                        return None, "No speech detected (timeout)"

            except sr.UnknownValueError:
                if attempt < retries:
                    print("⚠️  Couldn't understand, please speak again...")
                    time.sleep(0.5)
                    continue
                return None, "Could not understand. Speak clearly and try again."
            except sr.RequestError as e:
                return None, f"API Error: Check internet connection ({e})"
            except Exception as e:
                return None, f"Error: {e}"

        return None, "Max retries exceeded"


def show_languages():
    """Display available languages"""
    print("\n" + "=" * 50)
    print("SUPPORTED LANGUAGES")
    print("=" * 50)
    for key, value in SUPPORTED_LANGUAGES.items():
        lang_names = {
            'en-US': 'English',
            'hi-IN': 'Hindi (हिन्दी)',
            'te-IN': 'Telugu (తెలుగు)',
            'ta-IN': 'Tamil (தமிழ்)',
            'bn-IN': 'Bengali (বাংলা)',
            'mr-IN': 'Marathi (मराठी)',
            'gu-IN': 'Gujarati (ગુજરાતી)',
            'kn-IN': 'Kannada (ಕನ್ನಡ)',
            'ml-IN': 'Malayalam (മലയാളം)',
        }
        print(f"  {key}. {value} - {lang_names.get(value, '')}")
    print("=" * 50)


def select_language():
    """Let user select language"""
    show_languages()
    while True:
        choice = input("\nSelect language (1-9), or 'q' to quit: ").strip()
        if choice.lower() == 'q':
            return None
        if choice in SUPPORTED_LANGUAGES:
            return SUPPORTED_LANGUAGES[choice]
        print("Invalid choice. Try again.")


def main():
    """Main transcription loop"""
    print("\n" + "=" * 50)
    print("🎙️  SPEECH-TO-TEXT (ACCURATE MODE)")
    print("=" * 50)

    transcriber = Transcriber()

    language = select_language()
    if not language:
        print("\n👋 Goodbye!")
        return

    print(f"\n✅ Language: {language}")
    print("\n📝 Instructions:")
    print("   • Press ENTER to start recording")
    print("   • Speak clearly and at normal pace")
    print("   • Type 'lang' to change language")
    print("   • Type 'q' to quit")
    print("-" * 50)

    consecutive_errors = 0

    while True:
        try:
            user_input = input("\nPress ENTER to speak (or 'q'/'lang'): ").strip()

            if user_input.lower() in ['quit', 'q', 'exit']:
                print("\n👋 Goodbye!")
                break
            elif user_input.lower() == 'lang':
                language = select_language()
                if not language:
                    print("\n👋 Goodbye!")
                    break
                print(f"\n✅ Language: {language}")
                consecutive_errors = 0
                continue
            elif user_input == '':
                text, error = transcriber.transcribe_speech(language)

                if error:
                    consecutive_errors += 1
                    print(f"⚠️  {error}")
                    if consecutive_errors >= 3:
                        print("\n💡 Tip: Speak louder/closer to mic, or check mic settings")
                        consecutive_errors = 0
                else:
                    consecutive_errors = 0
                    print("\n" + "=" * 50)
                    print(f"📄 TRANSCRIPTION ({language})")
                    print("=" * 50)
                    print(f"   \"{text}\"")
                    print("=" * 50)
            else:
                print("⚠️  Press ENTER to speak, 'lang' to change language, 'q' to quit")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            consecutive_errors = 0


if __name__ == '__main__':
    main()
