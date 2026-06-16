import os
import subprocess
import sys
import tempfile

# Detect platform once at import time
_PLATFORM = sys.platform  # 'linux', 'darwin', or 'win32'

if _PLATFORM == "win32":
    import winsound

class TextToSpeech:
    def __init__(self, voice_name="alba", custom_voice_path=""):
        self.voice_name = voice_name
        self.custom_voice_path = custom_voice_path
        self.model = None
        self.voice_state = None
        self.initialized = False

    def initialize(self):
        """Loads the pocket-tts model and pre-computes the voice state."""
        try:
            print("Importing pocket-tts and loading model (100M parameters, CPU optimized)...")
            from pocket_tts import TTSModel

            # Load the model files (this will download them on the first run)
            self.model = TTSModel.load_model()

            # Load the custom voice (WAV file) or default built-in voice (like 'alba')
            target_voice = self.custom_voice_path if self.custom_voice_path else self.voice_name
            print(f"Loading voice state from prompt: '{target_voice}'...")

            self.voice_state = self.model.get_state_for_audio_prompt(target_voice)
            self.initialized = True
            print("pocket-tts successfully initialized!")

        except Exception as e:
            print(f"[TTS Error] Failed to initialize pocket-tts: {e}")
            print("Ensure PyTorch (>=2.5) and pocket-tts are installed.")
            print("System will fall back to printing responses directly to the console.")
            self.initialized = False

    def change_voice(self, voice_name_or_path):
        """Allows switching the voice (prompt) within the code at runtime."""
        self.voice_name = voice_name_or_path
        if os.path.exists(voice_name_or_path):
            self.custom_voice_path = voice_name_or_path
            target = self.custom_voice_path
        else:
            self.custom_voice_path = ""
            target = self.voice_name

        if self.initialized and self.model:
            try:
                print(f"Updating TTS voice state to prompt: '{target}'...")
                self.voice_state = self.model.get_state_for_audio_prompt(target)
                print("Voice updated successfully.")
            except Exception as e:
                print(f"Failed to change voice to '{target}': {e}")

    @staticmethod
    def _play_audio(filepath):
        """Play a WAV file using the platform-native audio command.

        - Linux:  aplay  (ALSA utilities, pre-installed on virtually all distros)
        - macOS:  afplay (ships with macOS)
        - Windows: winsound stdlib module (no external process needed)
        """
        if _PLATFORM.startswith("linux"):
            subprocess.run(
                ["aplay", filepath],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif _PLATFORM == "darwin":
            subprocess.run(
                ["afplay", filepath],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif _PLATFORM == "win32":
            winsound.PlaySound(filepath, winsound.SND_FILENAME)
        else:
            print(f"[TTS Warning] Unsupported platform '{_PLATFORM}' — audio not played.")

    def speak(self, text):
        """Generates WAV audio using pocket-tts and plays it via the native OS audio command."""
        if not text or not str(text).strip():
            print("[TTS Warning] Empty text received; skipping playback.")
            return

        # Clean response string of any markdown stars or brackets to prevent TTS stuttering
        cleaned_text = text.replace("*", "").replace("_", "").replace("[", "").replace("]", "").strip()
        if not cleaned_text:
            print("[TTS Warning] Text became empty after cleaning; skipping playback.")
            return

        print(f'>>> [Race Engineer]: "{cleaned_text}"')

        if not self.initialized:
            # Silent fallback if TTS model isn't active
            return

        try:
            import scipy.io.wavfile

            # Generate the raw audio tensor (returns 1D torch tensor)
            audio_tensor = self.model.generate_audio(self.voice_state, cleaned_text)

            # Save to temporary file in the workspace
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_filename = f.name

            scipy.io.wavfile.write(temp_filename, self.model.sample_rate, audio_tensor.numpy())

            # Play using the platform-appropriate audio command
            self._play_audio(temp_filename)

            # Clean up temporary WAV file
            try:
                os.remove(temp_filename)
            except OSError:
                pass

        except Exception as e:
            print(f"[TTS Audio Playback Error]: {e}")