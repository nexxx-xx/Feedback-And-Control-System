import pyttsx3
import time

class GateAudio:
    def __init__(self):
        self.tts_phrases = {
            "SYSTEM_START": "Smart AI Gate Control System is now online.",
            "ENTER": "Access verified. Welcome to the compound. Please proceed safely.",
            "EXIT": "Exit confirmed. Thank you and have a safe journey.",
            "FULL": "Attention please. The compound is currently full. Please wait for available space.",
            "EMPTY": "Invalid exit detected. There is currently nobody inside the compound.",
            "WARN_1": "Warning. Please clear the gate area immediately.",
            "WARN_2": "Security alert. Gate obstruction detected for too long.",
            "ACCESS_DENIED": "Access denied. AI verification failed.",
            "WAKE": "Motion detected. System activated.",
            "SLEEP": "System entering standby mode.",
            "IDLE_ALERT": "No motion detected.",
            "SHUTDOWN": "System will shutdown."
        }
        
        self.has_spoken_idle = False

        print("Initializing Native Voice Assistant Driver...")
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if "zira" in voice.name.lower() or "female" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            self.engine.setProperty('rate', 170)
            self.engine.setProperty('volume', 1.0)
            
            self.engine.startLoop(False)
            print("AI Voice Assistant Ready!")
        except Exception as e:
            print(f"TTS Driver Failure: {e}")
            self.engine = None

    def play(self, event_code):
        """Appends speech arrays to the native system buffer queue."""
        phrase = self.tts_phrases.get(event_code)
        if not phrase:
            return

        if self.engine:
            print(f"AI Queueing Speech: {phrase}")
            self.engine.say(phrase)
        else:
            print(f"Audio Offline: Skipped phrase: {phrase}")

    def play_shutdown(self, event_code):
        """Queues the final shutdown phrase and forces the engine to speak it completely before closing."""
        phrase = self.tts_phrases.get(event_code)
        if not phrase or not self.engine:
            return

        print(f"AI Final Speech: {phrase}")
        self.engine.say(phrase)
        
        # Pump the active engine loop for 2.5 seconds to ensure complete vocal track delivery
        for _ in range(25):  
            try:
                self.engine.iterate()
            except Exception:
                pass
            time.sleep(0.1)
        
        self.shutdown()

    def update(self):
        """Pumps small audio generation chunks. Called inside the main execution window loop."""
        if self.engine:
            try:
                self.engine.iterate()
            except Exception:
                pass

    def shutdown(self):
        if self.engine:
            try:
                self.engine.endLoop()
                self.engine = None
            except Exception:
                pass