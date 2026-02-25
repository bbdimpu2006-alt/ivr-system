"""
Voice-to-Voice Response System
Speech-to-Text → Process → Text-to-Speech
"""
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import pyaudio
import threading
import sys
import time
import re
from dotenv import load_dotenv

load_dotenv()

# Supported languages
SUPPORTED_LANGUAGES = {
    '1': 'en',      # English
    '2': 'hi',      # Hindi
    '3': 'te',      # Telugu
    '4': 'ta',      # Tamil
    '5': 'bn',      # Bengali
    '6': 'mr',      # Marathi
    '7': 'gu',      # Gujarati
    '8': 'kn',      # Kannada
    '9': 'ml',      # Malayalam
}

# Microphone index
MICROPHONE_INDEX = 2


class VoiceToVoice:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 350
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.0
        self.mic_index = self.get_working_microphone()

    def get_working_microphone(self):
        """Find and test microphone"""
        mics = sr.Microphone.list_microphone_names()

        print(f"\n📋 Available microphones ({len(mics)}):")
        for i, name in enumerate(mics):
            print(f"   {i}: {name}")

        if MICROPHONE_INDEX is not None and MICROPHONE_INDEX < len(mics):
            try:
                mic = sr.Microphone(device_index=MICROPHONE_INDEX)
                with mic:
                    pass
                print(f"✓ Using: {mics[MICROPHONE_INDEX]}\n")
                return MICROPHONE_INDEX
            except Exception as e:
                print(f"  Index {MICROPHONE_INDEX} failed: {e}")

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

        print("✓ Using default microphone\n")
        return None

    def listen(self, language='en'):
        """Listen and transcribe speech"""
        for attempt in range(2):
            try:
                with sr.Microphone(device_index=self.mic_index) as source:
                    source.gain = 10
                    print(f"\n🎤 Listening... (speak clearly)")
                    sys.stdout.flush()

                    print("  calibrating...", end='', flush=True)
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.7)
                    print(" done")

                    try:
                        audio = self.recognizer.listen(
                            source,
                            timeout=5,
                            phrase_time_limit=5
                        )

                        print("⏳ Recognizing...")
                        sys.stdout.flush()

                        text = self.recognizer.recognize_google(audio, language=language)
                        return text, None

                    except sr.WaitTimeoutError:
                        if attempt < 1:
                            print("⚠️  No speech detected, try again...")
                            time.sleep(0.5)
                            continue
                        return None, "No speech detected"

            except sr.UnknownValueError:
                if attempt < 1:
                    print("⚠️  Couldn't understand, speak again...")
                    time.sleep(0.5)
                    continue
                return None, "Could not understand"
            except sr.RequestError as e:
                return None, f"API Error: Check internet ({e})"
            except Exception as e:
                return None, f"Error: {e}"

        return None, "Max retries"

    def speak(self, text, language='en'):
        """Convert text to speech and play audio"""
        try:
            print(f"\n🔊 Speaking: \"{text}\"")
            
            # Generate speech audio
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Play audio using pyaudio
            audio_bytes = BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            
            # Save temp file for playback
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                temp_path = f.name
                tts.save(f.name)
            
            # Play using system player
            if sys.platform == 'win32':
                os.system(f'start /min wmplayer "{temp_path}"')
            else:
                os.system(f'afplay "{temp_path}"' if sys.platform == 'darwin' else f'aplay "{temp_path}"')
            
            time.sleep(2)  # Wait for playback
            
            # Cleanup
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            print(f"⚠️  TTS Error: {e}")

    def detect_language(self, text):
        """Detect language of transcribed text"""
        if not text:
            return None
        
        # Check for Hindi characters (Devanagari script)
        if re.search(r'[\u0900-\u097F]', text):
            return 'hi'
        # Check for Telugu characters
        elif re.search(r'[\u0C00-\u0C7F]', text):
            return 'te'
        # Check for Tamil characters
        elif re.search(r'[\u0B80-\u0BFF]', text):
            return 'ta'
        # Check for Bengali characters
        elif re.search(r'[\u0980-\u09FF]', text):
            return 'bn'
        # Check for Marathi (also Devanagari)
        elif re.search(r'[\u0900-\u097F]', text):
            return 'mr'
        # Check for Gujarati characters
        elif re.search(r'[\u0A80-\u0AFF]', text):
            return 'gu'
        # Check for Kannada characters
        elif re.search(r'[\u0C80-\u0CFF]', text):
            return 'kn'
        # Check for Malayalam characters
        elif re.search(r'[\u0D00-\u0D7F]', text):
            return 'ml'
        # Default to English
        else:
            return 'en'

    def process_response(self, text, language='en'):
        """Process input and generate response - echoes back in selected language"""
        # Detect the language of spoken text
        detected_lang = self.detect_language(text)
        
        # Language names for response
        lang_names = {
            'en': 'English',
            'hi': 'Hindi (हिन्दी)',
            'te': 'Telugu (తెలుగు)',
            'ta': 'Tamil (தமிழ்)',
            'bn': 'Bengali (বাংলা)',
            'mr': 'Marathi (मराठी)',
            'gu': 'Gujarati (ગુજરાતી)',
            'kn': 'Kannada (ಕನ್ನಡ)',
            'ml': 'Malayalam (മലയാളം)',
        }
        
        # Messages for "speak in X language"
        wrong_lang_messages = {
            'en': 'Please speak in English',
            'hi': 'कृपया हिंदी में बोलें',
            'te': 'దయచేసి తెలుగులో మాట్లాడండి',
            'ta': 'தயவுசெய்து தமிழில் பேசவும்',
            'bn': 'অনুগ্রহ করে বাংলায় কথা বলুন',
            'mr': 'कृपया मराठीत बोला',
            'gu': 'કૃપા કરીને ગુજરાતીમાં બોલો',
            'kn': 'ದಯವಿಟ್ಟು ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ',
            'ml': 'ദയവായി മലയാളത്തിൽ സംസാരിക്കുക',
        }
        
        # If detected language doesn't match selected language
        if detected_lang != language:
            selected_lang_name = lang_names.get(language, language)
            return wrong_lang_messages.get(language, f'Please speak in {selected_lang_name}')
        
        # Return the text to echo back
        return text


def show_languages():
    """Display available languages"""
    print("\n" + "=" * 50)
    print("SUPPORTED LANGUAGES")
    print("=" * 50)
    for key, value in SUPPORTED_LANGUAGES.items():
        lang_names = {
            'en': 'English',
            'hi': 'Hindi (हिन्दी)',
            'te': 'Telugu (తెలుగు)',
            'ta': 'Tamil (தமிழ்)',
            'bn': 'Bengali (বাংলা)',
            'mr': 'Marathi (मराठी)',
            'gu': 'Gujarati (ગુજરાતી)',
            'kn': 'Kannada (ಕನ್ನಡ)',
            'ml': 'Malayalam (മലയാളം)',
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
    """Main voice-to-voice loop"""
    print("\n" + "=" * 50)
    print("🎙️🔊 VOICE-TO-VOICE RESPONSE")
    print("=" * 50)

    system = VoiceToVoice()

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

    # Greeting
    greetings = {
        'en': "Hello! I'm ready to help. Press Enter and speak.",
        'hi': "नमस्ते! मैं तैयार हूं। Enter दबाएं और बोलें।",
        'te': "నమస్కారం! నేను సిద్ధంగా ఉన్నాను. Enter నొక్కి మాట్లాడండి.",
        'ta': "வணக்கம்! நான் தயாராக உள்ளேன். Enter அழுத்தி பேசவும்.",
        'bn': "নমস্কার! আমি প্রস্তুত। Enter চাপুন এবং কথা বলুন।",
        'mr': "नमस्कार! मी तयार आहे. Enter दाबा आणि बोला.",
        'gu': "નમસ્તે! હું તૈયાર છું. Enter દબાવો અને બોલો.",
        'kn': "ನಮಸ್ಕಾರ! ನಾನು ಸಿದ್ಧನಾಗಿದ್ದೇನೆ. Enter ಒತ್ತಿ ಮಾತನಾಡಿ.",
        'ml': "നമസ്കാരം! ഞാൻ തയ്യാറാണ്. Enter അമർത്തി സംസാരിക്കുക.",
    }
    system.speak(greetings.get(language, "Hello! Press Enter and speak."), language)

    while True:
        try:
            user_input = input("\nPress ENTER to speak (or 'q'/'lang'): ").strip()

            if user_input.lower() in ['quit', 'q', 'exit']:
                goodbye = {
                    'en': "Goodbye! Have a great day!",
                    'hi': "अलविदा! अच्छा दिन हो!",
                    'te': "వీడ్కోలు! మంచి రోజు!",
                    'ta': "விடை! நல்ல நாள்!",
                    'bn': "বিদায়! ভাল দিন!",
                    'mr': "अलविदा! चांगला दिवस!",
                    'gu': "અલવિદા! સારો દિવસ!",
                    'kn': "ವಿದಾಯ! ಒಳ್ಳೆಯ ದಿನ!",
                    'ml': "വിട! നല്ല ദിവസം!",
                }
                system.speak(goodbye.get(language, "Goodbye!"), language)
                print("\n👋 Goodbye!")
                break

            elif user_input.lower() == 'lang':
                language = select_language()
                if not language:
                    print("\n👋 Goodbye!")
                    break
                print(f"\n✅ Language: {language}")
                continue

            elif user_input == '':
                # Listen
                text, error = system.listen(language)

                if error:
                    print(f"⚠️  {error}")
                else:
                    print(f"\n📄 You said: \"{text}\"")
                    
                    # Process and respond
                    response = system.process_response(text, language)
                    system.speak(response, language)

            else:
                print("⚠️  Press ENTER to speak, 'lang' to change language, 'q' to quit")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == '__main__':
    main()
