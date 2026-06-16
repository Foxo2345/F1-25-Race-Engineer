import os
import sys
import json
import time
import threading
try:
    import keyboard  # type: ignore[reportMissingModuleSource]
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
from telemetry.listener import TelemetryListener
from tts.engine import TextToSpeech
from tts.worker import SpeechWorker
from ai.client import RaceEngineerAI

CONFIG_FILE = "config.json"

def load_config():
    defaults = {
        "udp_ip": "0.0.0.0",
        "udp_port": 20777,
        "api_provider": "gemini",
        "api_key": "YOUR_GEMINI_API_KEY_HERE",
        "api_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "ai_model": "gemini-3.1-flash-lite",
        "backup_ai_model": "gemini-3.5-flash",
        "model_cooldown_seconds": 30,
        "personality": "friendly",
        "voice_name": "alba",
        "custom_voice_path": "",
        "wear_threshold": 10.0,
        "temp_threshold_high": 100
    }

    if not os.path.exists(CONFIG_FILE):
        print(f"Config file {CONFIG_FILE} not found. Creating default configuration.")
        config = dict(defaults)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return config

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    updated = False
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
            updated = True

    if updated:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

    return config

def request_status_update(listener, ai_client, speech_worker, user_question=None):
    """Triggers a manual status update or answers a typed race question."""
    try:
        if user_question:
            print(f"[Question] {user_question}")
        else:
            print("[Hotkey] Status update requested...")

        snapshot = listener.state.get_snapshot()
        # Debug: print raw telemetry values to help diagnose wrong readings
        print(f"  [DEBUG] Lap={snapshot['current_lap_num']} Pos={snapshot['car_position']} "
              f"Fuel={snapshot['fuel_in_tank']:.2f}kg ({snapshot['fuel_remaining_laps']:.1f} laps) "
              f"Speed={snapshot['speed']}kph Gear={snapshot['gear']}")
        print(f"  [DEBUG] Tyres wear={[f'{w:.1f}%' for w in snapshot['tyres_wear']]} "
              f"Temp={snapshot['tyres_surface_temp']}°C")
        print(f"  [DEBUG] Damage: FLWing={snapshot['front_left_wing_damage']}% "
              f"FRWing={snapshot['front_right_wing_damage']}% "
              f"RWing={snapshot['rear_wing_damage']}% "
              f"Engine={snapshot['engine_damage']}% Gearbox={snapshot['gearbox_damage']}%")

        event_details = user_question if user_question else "Manual status update requested."
        feedback = ai_client.get_engineer_feedback(snapshot, "manual_status", event_details)
        speech_worker.speak(feedback)
    except Exception as e:
        print(f"[Race Engineer] Error during request: {e}")

def hotkey_listener(listener, ai_client, speech_worker):
    """Listens for the Numlock global hotkey to trigger a status update from anywhere."""
    if not KEYBOARD_AVAILABLE:
        print("[Hotkey] 'keyboard' library not installed. Global hotkey disabled.")
        return

    def on_numlock():
        # Run in a separate thread so the hotkey handler returns immediately
        t = threading.Thread(
            target=request_status_update,
            args=(listener, ai_client, speech_worker),
            daemon=True
        )
        t.start()

    keyboard.add_hotkey('num lock', on_numlock, suppress=False)
    print("[Hotkey] Press [Num Lock] anywhere to request a status update.")
    keyboard.wait()  # Block this thread, keeping hotkeys active

def console_input_loop(listener, ai_client, speech_worker):
    """Listens for console input to trigger a manual status update or answer a question."""
    print("----------------------------------------------------------------")
    print("Type a race question and press Enter to ask it.")
    print("Press Enter on a blank line for a status check.")
    print("Press [Num Lock] anywhere (even in-game) for a status check.")
    print("Press Ctrl+C to exit.")
    print("----------------------------------------------------------------")

    while True:
        try:
            line = sys.stdin.readline()
            if line == "":
                break

            user_input = line.strip()
            if user_input:
                request_status_update(listener, ai_client, speech_worker, user_input)
            else:
                request_status_update(listener, ai_client, speech_worker)
        except (KeyboardInterrupt, EOFError):
            break

def monitor_loop(listener, ai_client, speech_worker, config):
    """Monitors telemetry state at 1Hz and triggers AI engineer alerts for events."""
    state = listener.state

    # State tracking variables to prevent spamming the AI
    last_processed_lap = 0
    last_wear_alert_level = 0.0  # Alert when wear crosses increments of config["wear_threshold"] (e.g. 10%)

    # Track wing damage levels - initialized to None so we set them on first packet
    last_wing_damage = None
    last_mech_damage = None

    # Temperature/fuel warning locks
    temp_warned = False
    fuel_warned = False

    # Wait for the first telemetry packet to establish initial state
    print("Waiting for game telemetry stream...")
    while True:
        snapshot = state.get_snapshot()
        # F1 23/24 packets will have format set (like 2023 or 2024)
        if snapshot["current_lap_num"] > 0 and snapshot["fuel_in_tank"] > 0:
            last_processed_lap = snapshot["current_lap_num"]
            # Initialize damage tracking from first real telemetry to avoid false alerts
            last_wing_damage = max(snapshot["front_left_wing_damage"], snapshot["front_right_wing_damage"], snapshot["rear_wing_damage"])
            last_mech_damage = max(snapshot["engine_damage"], snapshot["gearbox_damage"])
            # Initialize wear tracking from current state
            max_wear = max(snapshot["tyres_wear"])
            wear_threshold = config.get("wear_threshold", 10.0)
            last_wear_alert_level = (max_wear // wear_threshold) * wear_threshold
            print("First telemetry packet received. Connection established!")
            speech_worker.speak("Radio check. Connection established. Let's get to work.")
            break
        time.sleep(0.5)

    # Core Monitoring Loop (1Hz check)
    while True:
        try:
            time.sleep(1.0)
            snapshot = state.get_snapshot()

            # 1. Lap Complete Event
            curr_lap = snapshot["current_lap_num"]
            if curr_lap > last_processed_lap:
                # Trigger lap review
                print(f"[Event] Lap completed. Old Lap: {last_processed_lap}, New Lap: {curr_lap}")
                last_processed_lap = curr_lap
                feedback = ai_client.get_engineer_feedback(snapshot, "lap_complete", f"Completed lap {curr_lap - 1}.")
                speech_worker.speak(feedback)
                continue  # Skip checking other alerts on same tick to prevent overlapping audio

            # 2. Damage Alert Event
            curr_wing_dmg = max(snapshot["front_left_wing_damage"], snapshot["front_right_wing_damage"], snapshot["rear_wing_damage"])
            curr_mech_dmg = max(snapshot["engine_damage"], snapshot["gearbox_damage"])

            if curr_wing_dmg > last_wing_damage:
                diff = curr_wing_dmg - last_wing_damage
                last_wing_damage = curr_wing_dmg
                print(f"[Event] Aerodynamic damage increase: +{diff}%")
                feedback = ai_client.get_engineer_feedback(snapshot, "damage_alert", f"Wing damage increased by {diff}%. Current wing damage: {curr_wing_dmg}%.")
                speech_worker.speak(feedback)
                continue

            if curr_mech_dmg > last_mech_damage:
                diff = curr_mech_dmg - last_mech_damage
                last_mech_damage = curr_mech_dmg
                print(f"[Event] Mechanical wear increase: +{diff}%")
                feedback = ai_client.get_engineer_feedback(snapshot, "damage_alert", f"Mechanical engine or gearbox wear increased by {diff}%. Current mechanical damage: {curr_mech_dmg}%.")
                speech_worker.speak(feedback)
                continue

            # 3. Tyre Wear alert (triggers when max wear crosses wear_threshold increments)
            max_wear = max(snapshot["tyres_wear"])
            wear_threshold = config.get("wear_threshold", 10.0)

            # Detect pit stop / new tyres: wear dropped significantly
            if max_wear < last_wear_alert_level - 5:
                last_wear_alert_level = 0.0
                print(f"[Event] New tyres detected. Wear reset from pit stop. Resetting alerts.")

            # Find closest wear band (e.g. 10%, 20%, 30%)
            current_wear_level = (max_wear // wear_threshold) * wear_threshold
            if current_wear_level > last_wear_alert_level:
                last_wear_alert_level = current_wear_level
                print(f"[Event] Tyre wear crossed warning level: {max_wear:.1f}%")
                feedback = ai_client.get_engineer_feedback(snapshot, "tyre_wear_alert", f"Maximum tyre wear reached {max_wear:.1f}%.")
                speech_worker.speak(feedback)
                continue

            # 4. Overheating alert (triggers if tyre temp goes above threshold)
            max_temp = max(snapshot["tyres_surface_temp"])
            temp_limit = config.get("temp_threshold_high", 100)
            if max_temp > temp_limit and not temp_warned:
                temp_warned = True
                print(f"[Event] Tyre surface overheating: {max_temp}C")
                feedback = ai_client.get_engineer_feedback(snapshot, "overheating_alert", f"Tyres are overheating. Surface temp reading {max_temp}C.")
                speech_worker.speak(feedback)
            elif max_temp < (temp_limit - 10):  # Hysteresis (cool down by 10C before resetting warning)
                temp_warned = False

            # 5. Fuel Low warning (remaining laps < 1.5)
            remaining_laps = snapshot["fuel_remaining_laps"]
            if remaining_laps <= 1.5 and not fuel_warned:
                fuel_warned = True
                print(f"[Event] Critical fuel: {remaining_laps:.2f} laps remaining")
                feedback = ai_client.get_engineer_feedback(snapshot, "fuel_warning", f"Fuel is low. {remaining_laps:.2f} laps left.")
                speech_worker.speak(feedback)
            elif remaining_laps >= 2.0:
                fuel_warned = False

        except Exception as e:
            print(f"Error in monitor loop: {e}")
            time.sleep(1.0)

def main():
    print("Initializing F1 25 AI Race Engineer...")
    config = load_config()

    # 1. Initialize Speech Synthesis Module
    tts = TextToSpeech(voice_name=config["voice_name"], custom_voice_path=config["custom_voice_path"])
    speech_worker = SpeechWorker(tts)
    speech_worker.start()

    # 2. Initialize AI Race Engineer Client
    try:
        ai_client = RaceEngineerAI(
            provider=config["api_provider"],
            api_key=config["api_key"],
            api_url=config["api_url"],
            model=config["ai_model"],
            personality=config.get("personality", "friendly"),
            backup_model=config.get("backup_ai_model", "gemini-3.5-flash"),
            cooldown_seconds=config.get("model_cooldown_seconds", 60)
        )
    except RuntimeError as e:
        print(f"[ERROR] Could not initialize AI client: {e}")
        print("Please check your 'api_provider' and 'api_key' settings in config.json.")
        speech_worker.stop()
        sys.exit(1)

    # 3. Initialize Telemetry Listener
    listener = TelemetryListener(ip=config["udp_ip"], port=config["udp_port"])
    listener.start()

    # 4. Start Monitoring Thread
    monitor_thread = threading.Thread(
        target=monitor_loop,
        args=(listener, ai_client, speech_worker, config),
        daemon=True
    )
    monitor_thread.start()

    # 5. Start global hotkey listener thread (Numlock)
    hotkey_thread = threading.Thread(
        target=hotkey_listener,
        args=(listener, ai_client, speech_worker),
        daemon=True
    )
    hotkey_thread.start()

    # 6. Start console loop for keyboard triggers (Blocks main thread)
    try:
        console_input_loop(listener, ai_client, speech_worker)
    except KeyboardInterrupt:
        print("Shutting down AI Race Engineer...")
    finally:
        listener.stop()
        speech_worker.stop()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
