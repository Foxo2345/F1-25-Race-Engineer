import queue
import threading

class SpeechWorker:
    def __init__(self, tts_engine):
        self.tts_engine = tts_engine
        self.queue = queue.Queue()
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()

    def speak(self, text):
        """Adds a phrase to the speech queue to be played in sequence."""
        if self.running and text and str(text).strip():
            self.queue.put(text)

    def stop(self):
        self.running = False
        self.queue.put(None)  # Sentinel to stop worker loop
        if self.thread:
            self.thread.join(timeout=2.0)
        print("Speech worker stopped.")

    def _worker_loop(self):
        # Initialize the heavy TTS engine inside the thread so the main app opens instantly
        self.tts_engine.initialize()
        
        while self.running:
            try:
                text = self.queue.get(timeout=1.0)
                if text is None:
                    break
                
                # Speak (blocks the worker thread, but not the main telemetry thread)
                self.tts_engine.speak(text)
                self.queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in speech worker thread: {e}")
