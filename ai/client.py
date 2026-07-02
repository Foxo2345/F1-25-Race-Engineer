import json
import time

class RaceEngineerAI:
    def __init__(self, provider="gemini", api_key="", api_url="", model="gemini-2.5-flash", personality="professional", backup_model="gemini-3.5-flash", cooldown_seconds=60):
        self.provider = provider.lower()
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.personality = personality
        self.backup_model = backup_model
        self.cooldown_seconds = cooldown_seconds

        # In-memory conversation history to keep context
        self.history = []
        self.model_retry_at = 0.0

        # System instructions guiding the AI's behavior
        self.system_instruction = self._build_system_instruction(personality)

        self.client = None
        if self.provider == "gemini":
            if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY_HERE":
                raise RuntimeError(
                    "Gemini API key is not configured. "
                    "Please set a valid 'api_key' in config.json."
                )
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print("Gemini API client initialized.")
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Gemini client: {e}") from e

        elif self.provider == "openai":
            if not self.api_key:
                raise RuntimeError(
                    "OpenAI API key is not configured. "
                    "Please set a valid 'api_key' in config.json."
                )
            try:
                from openai import OpenAI
                kwargs = {"api_key": self.api_key}
                if self.api_url:
                    kwargs["base_url"] = self.api_url
                self.client = OpenAI(**kwargs)
                print("OpenAI API client initialized.")
            except Exception as e:
                raise RuntimeError(f"Failed to initialize OpenAI client: {e}") from e

        else:
            raise RuntimeError(
                f"Unknown API provider '{self.provider}'. "
                "Supported values: 'gemini', 'openai'."
            )

    def _build_system_instruction(self, personality):
        tone_map = {
            "professional": (
                "calm, concise, and technically precise, witty and sarcastic",
                "Use a natural radio style with a little warmth. Do not sound like a checklist."
            ),
            "friendly": (
                "calm, human, and encouraging",
                "Sound like a trusted engineer who knows the driver well. Use short acknowledgements such as 'good', 'nice', or 'we're okay' when appropriate."
            ),
            "aggressive": (
                "direct, urgent, and commanding",
                "Use sharper language when the situation demands it, but still keep it human rather than robotic."
            ),
        }

        tone, extra_guidance = tone_map.get(personality, tone_map["professional"])

        return (
            "You are a Formula 1 race engineer speaking to a driver over team radio. "
            "The driver is racing on track and you receive live telemetry updates. "
            f"Your tone should be {tone}. "
            f"{extra_guidance} "
            "Rules:\n"
            "1. Keep responses short, but let them sound human. Vary the opener instead of repeating the same phrase every time.\n"
            "2. Use radio terminology where it fits: 'Copy that', 'Box box', 'Strat 2', 'Push now', 'Stay focused'.\n"
            "3. Add brief human context when useful, like reassurance or urgency, without sounding like a morale coach.\n"
            "4. Do not praise the driver unless the situation is clearly positive. Do not praise slower laps, damage, being overtaken, tyre drop-off, or other setbacks.\n"
            "5. If a lap is faster than the previous lap or the driver has clearly done something good, a short acknowledgement is fine. Otherwise stay neutral or corrective.\n"
            "6. Do not use markdown formatting (no bold, no italics) because responses go directly to text-to-speech.\n"
            "7. If telemetry shows zero fuel or zero ers while lap and position are valid, treat it as an unreliable reading and do not say the car is retired.\n"
            "8. Aim for one to two short sentences max.\n"
            "Examples:\n"
            "- 'Good lap, keep pushing.'\n"
            "- 'Understood. Tyres are going off, manage it.'\n"
            "- 'Copy that. That lap was slower, reset and go again.'\n"
        )

    def get_engineer_feedback(self, telemetry, event_type, event_details=None, lap_tracker=None):
        """
        Formats the current telemetry snapshot and event, sends it to the AI, and returns the spoken feedback.
        """
        # Build lap history context from the tracker
        lap_context = ""
        if lap_tracker:
            lap_context = lap_tracker.get_summary()

        prompt = self._build_prompt(telemetry, event_type, event_details, lap_context)

        if self.provider == "gemini" and self.client:
            try:
                model_name = self._active_gemini_model()
                ai_text = self._call_gemini(self.client, model_name, prompt)
                if not ai_text:
                    ai_text = self._fallback_message(event_type, telemetry)
                return ai_text
            except Exception as e:
                if self._is_quota_error(e):
                    self.model_retry_at = time.time() + self.cooldown_seconds
                    print(f"Gemini quota reached; cooling primary model for {self.cooldown_seconds}s and switching to {self.backup_model}.")
                    try:
                        ai_text = self._call_gemini(self.client, self.backup_model, prompt)
                        if ai_text:
                            return ai_text
                    except Exception as backup_error:
                        print(f"Backup Gemini call failed: {backup_error}")
                print(f"Error calling Gemini API: {e}")
                return self._fallback_message(event_type, telemetry)

        elif self.provider == "openai" and self.client:
            try:
                ai_text = self._call_openai(self.client, self.model, prompt, self.history)
                if not ai_text:
                    ai_text = self._fallback_message(event_type, telemetry)
                return ai_text
            except Exception as e:
                if self._is_quota_error(e):
                    print("OpenAI quota reached; switching to backup model.")
                    try:
                        ai_text = self._call_openai(self.client, self.backup_model, prompt, self.history)
                        if ai_text:
                            return ai_text
                    except Exception as backup_error:
                        print(f"Backup OpenAI call failed: {backup_error}")
                print(f"Error calling OpenAI API: {e}")
                return self._fallback_message(event_type, telemetry)

        return None

    def _active_gemini_model(self):
        if self.model_retry_at and time.time() < self.model_retry_at:
            return self.backup_model
        return self.model

    def _call_gemini(self, client, model, prompt):
        from google.genai import types

        self.history.append({"role": "user", "parts": [prompt]})
        if len(self.history) > 10:
            self.history = self.history[-10:]

        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=0.8,
            max_output_tokens=1000
        )

        contents = []
        for h in self.history:
            contents.append(types.Content(role=h["role"], parts=[types.Part.from_text(text=h["parts"][0])]))

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )

        ai_text = (response.text or "").strip()
        if not ai_text:
            print("Gemini returned an empty response; using fallback radio call.")
            return ""

        self.history.append({"role": "model", "parts": [ai_text]})
        return ai_text

    def _call_openai(self, client, model, prompt, history):
        history.append({"role": "user", "content": prompt})
        if len(history) > 10:
            history[:] = history[-10:]

        messages = [{"role": "system", "content": self.system_instruction}]
        messages.extend(history)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
            max_tokens=1000
        )

        ai_text = (response.choices[0].message.content or "").strip()
        if not ai_text:
            print("OpenAI returned an empty response; using fallback radio call.")
            return ""

        history.append({"role": "assistant", "content": ai_text})
        return ai_text

    @staticmethod
    def _is_quota_error(error):
        message = str(error).lower()
        return "resource_exhausted" in message or "quota" in message or "429" in message

    def _fallback_message(self, event_type, telemetry):
        """Returns a short safe radio message when the model output is empty or fails."""
        if event_type == "manual_status":
            return (
                f"We are on Lap {telemetry['current_lap_num']}, in P{telemetry['car_position']}. "
                f"and time last lap was {self._format_lap_time(telemetry['last_lap_time_ms'])}. "
            
            )

        if event_type == "lap_complete":
            return f"Copy that. Lap {telemetry['current_lap_num']} complete."

        if event_type == "damage_alert":
            return "Copy that. Manage the damage and stay clean."

        if event_type == "tyre_wear_alert":
            return "Copy that. Tyres are going off."

        if event_type == "overheating_alert":
            return "Copy that. Tyres are overheating."

        if event_type == "fuel_warning":
            return "Copy that. Fuel is critical."

        return "Copy that."

    def _build_prompt(self, telemetry, event_type, event_details, lap_context=""):
        """
        Creates a clean structured telemetry snapshot prompt for the AI.
        """
        last_lap_display = self._format_lap_time(telemetry['last_lap_time_ms'])
        curr_lap_display = self._format_lap_time(telemetry['current_lap_time_ms'])
        lap_delta_ms = telemetry['current_lap_time_ms'] - telemetry['last_lap_time_ms']
        if telemetry['last_lap_time_ms'] > 0 and telemetry['current_lap_time_ms'] > 0:
            lap_delta_display = f"{lap_delta_ms:+.0f} ms vs last lap"
        else:
            lap_delta_display = "Unavailable"

        fuel_value = telemetry['fuel_in_tank']
        fuel_laps = telemetry['fuel_remaining_laps']
        on_track = telemetry['current_lap_num'] > 0 and telemetry['car_position'] > 0
        if on_track and fuel_value <= 0 and fuel_laps <= 0:
            fuel_line = "Fuel reading unavailable or unreliable"
        else:
            fuel_line = f"Fuel {fuel_value:.2f}kg ({fuel_laps:.2f} laps)"

        # Tyres RL, RR, FL, FR
        tyres_wear_str = ", ".join([f"{w:.1f}%" for w in telemetry['tyres_wear']])
        tyres_surf_temp_str = ", ".join([f"{t}C" for t in telemetry['tyres_surface_temp']])

        # Build lap history section
        lap_history_section = ""
        if lap_context:
            lap_history_section = (
                f"\n--- LAP HISTORY & PERFORMANCE ---\n"
                f"{lap_context}\n"
            )

        prompt = (
            f"Event: {event_type.upper()}\n"
            f"Details: {event_details if event_details else 'None'}\n"
            f"{lap_history_section}"
            f"\n--- CURRENT CAR TELEMETRY ---\n"
            f"- Mandatory status fields: Lap {telemetry['current_lap_num']}, Position P{telemetry['car_position']}, {fuel_line}\n"
            f"- Current Lap Time: {curr_lap_display}, Last Lap Time: {last_lap_display}, Delta: {lap_delta_display}\n"
            f"- Speed: {telemetry['speed']} km/h, Gear: {telemetry['gear']}, RPM: {telemetry['engine_rpm']}\n"
            f"- DRS: {'Active' if telemetry['drs'] == 1 else 'Inactive'}\n"
            f"- Throttle Input: {telemetry['throttle']*100:.0f}%, Brake Input: {telemetry['brake']*100:.0f}%\n"
            f"- Tyres Wear (RL, RR, FL, FR): {tyres_wear_str}\n"
            f"- Tyres Surface Temp (FL, FR, RL, RR): {tyres_surf_temp_str}\n"
            f"- Engine Temp: {telemetry['engine_temp']}C\n"
            f"- ERS Energy Store: {telemetry['ers_store_energy']/1e6:.2f} MJ\n"
            f"- Damage - Front Left Wing: {telemetry['front_left_wing_damage']}%, Front Right Wing: {telemetry['front_right_wing_damage']}%, Rear Wing: {telemetry['rear_wing_damage']}%\n"
            f"- Damage - Engine: {telemetry['engine_damage']}%, Gearbox: {telemetry['gearbox_damage']}%\n\n"
            f"Respond to the driver according to the Event. Use the lap history to provide context. If they just set a PB, acknowledge it. If they are consistent, keep it brief. Be concise."
        )
        return prompt

    @staticmethod
    def _format_lap_time(milliseconds):
        if milliseconds <= 0:
            return "0:00.000"

        total_seconds = milliseconds / 1000.0
        minutes = int(total_seconds // 60)
        seconds = total_seconds - (minutes * 60)
        return f"{minutes}:{seconds:06.3f}"
