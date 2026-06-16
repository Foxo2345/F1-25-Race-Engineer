import socket
import threading
import ctypes as ct
import traceback
from telemetry.packets import PacketHeader, PACKET_CLASSES, EXPECTED_PACKET_SIZES, MAX_CARS

class TelemetryState:
    def __init__(self):
        self.lock = threading.Lock()

        # Telemetry variables
        self.speed = 0  # km/h
        self.throttle = 0.0  # 0.0 to 1.0
        self.steer = 0.0  # -1.0 to 1.0
        self.brake = 0.0  # 0.0 to 1.0
        self.gear = 0
        self.engine_rpm = 0
        self.drs = 0

        self.brakes_temp = [0, 0, 0, 0]          # FL, FR, RL, RR
        self.tyres_surface_temp = [0, 0, 0, 0]   # FL, FR, RL, RR
        self.tyres_inner_temp = [0, 0, 0, 0]     # FL, FR, RL, RR
        self.engine_temp = 0                     # C

        # Lap Data
        self.car_position = 1
        self.current_lap_num = 1
        self.lap_distance = 0.0
        self.last_lap_time_ms = 0
        self.current_lap_time_ms = 0
        self.sector1_time_ms = 0
        self.sector2_time_ms = 0
        self.sector = 0  # 0, 1, 2

        # Status
        self.fuel_in_tank = 0.0
        self.fuel_remaining_laps = 0.0
        self.ers_store_energy = 0.0
        self.ers_deploy_mode = 0

        # Damage
        self.tyres_wear = [0.0, 0.0, 0.0, 0.0]  # Rear Left, Rear Right, Front Left, Front Right
        self.front_left_wing_damage = 0
        self.front_right_wing_damage = 0
        self.rear_wing_damage = 0
        self.engine_damage = 0
        self.gearbox_damage = 0

    def get_snapshot(self):
        with self.lock:
            return {
                "speed": self.speed,
                "throttle": self.throttle,
                "steer": self.steer,
                "brake": self.brake,
                "gear": self.gear,
                "engine_rpm": self.engine_rpm,
                "drs": self.drs,
                "brakes_temp": list(self.brakes_temp),
                "tyres_surface_temp": list(self.tyres_surface_temp),
                "tyres_inner_temp": list(self.tyres_inner_temp),
                "engine_temp": self.engine_temp,
                "car_position": self.car_position,
                "current_lap_num": self.current_lap_num,
                "lap_distance": self.lap_distance,
                "last_lap_time_ms": self.last_lap_time_ms,
                "current_lap_time_ms": self.current_lap_time_ms,
                "sector1_time_ms": self.sector1_time_ms,
                "sector2_time_ms": self.sector2_time_ms,
                "sector": self.sector,
                "fuel_in_tank": self.fuel_in_tank,
                "fuel_remaining_laps": self.fuel_remaining_laps,
                "ers_store_energy": self.ers_store_energy,
                "ers_deploy_mode": self.ers_deploy_mode,
                "tyres_wear": list(self.tyres_wear),
                "front_left_wing_damage": self.front_left_wing_damage,
                "front_right_wing_damage": self.front_right_wing_damage,
                "rear_wing_damage": self.rear_wing_damage,
                "engine_damage": self.engine_damage,
                "gearbox_damage": self.gearbox_damage,
            }


class TelemetryListener:
    def __init__(self, ip="0.0.0.0", port=20777):
        self.ip = ip
        self.port = port
        self.state = TelemetryState()
        self.sock = None
        self.running = False
        self.thread = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.ip, self.port))
        self.sock.settimeout(1.0)

        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print(f"Telemetry Listener started on {self.ip}:{self.port}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.sock:
            self.sock.close()
        print("Telemetry Listener stopped.")

    @staticmethod
    def _player_index(header):
        """Return the player car index from the packet header, or None if invalid."""
        idx = header.m_playerCarIndex
        if idx >= MAX_CARS:
            return None
        return idx

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                if len(data) < ct.sizeof(PacketHeader):
                    continue

                header = PacketHeader.from_buffer_copy(data[:ct.sizeof(PacketHeader)])
                packet_id = header.m_packetId
                player_idx = self._player_index(header)
                if player_idx is None:
                    continue

                if packet_id not in PACKET_CLASSES:
                    continue

                expected_size = EXPECTED_PACKET_SIZES.get(packet_id)
                if expected_size is not None and len(data) < expected_size:
                    continue

                cls = PACKET_CLASSES[packet_id]
                packet = cls.from_buffer_copy(data)

                with self.state.lock:
                    if packet_id == 2:  # Lap Data
                        lap_data = packet.m_lapData[player_idx]
                        if lap_data.m_carPosition > 0:
                            self.state.car_position = lap_data.m_carPosition
                        if lap_data.m_currentLapNum > 0:
                            self.state.current_lap_num = lap_data.m_currentLapNum
                        self.state.lap_distance = lap_data.m_lapDistance
                        self.state.last_lap_time_ms = lap_data.m_lastLapTimeInMS
                        self.state.current_lap_time_ms = lap_data.m_currentLapTimeInMS
                        self.state.sector1_time_ms = (
                            lap_data.m_sector1TimeMSPart
                            + int(lap_data.m_sector1TimeMinutesPart) * 60000
                        )
                        self.state.sector2_time_ms = (
                            lap_data.m_sector2TimeMSPart
                            + int(lap_data.m_sector2TimeMinutesPart) * 60000
                        )
                        self.state.sector = lap_data.m_sector

                    elif packet_id == 6:  # Car Telemetry
                        telem = packet.m_carTelemetryData[player_idx]
                        self.state.speed = telem.m_speed
                        self.state.throttle = telem.m_throttle
                        self.state.steer = telem.m_steer
                        self.state.brake = telem.m_brake
                        self.state.gear = telem.m_gear
                        self.state.engine_rpm = telem.m_engineRPM
                        self.state.drs = telem.m_drs

                        # Game order: RL, RR, FL, FR -> standardise to FL, FR, RL, RR
                        self.state.brakes_temp = [
                            telem.m_brakesTemperature[2],
                            telem.m_brakesTemperature[3],
                            telem.m_brakesTemperature[0],
                            telem.m_brakesTemperature[1],
                        ]
                        self.state.tyres_surface_temp = [
                            telem.m_tyresSurfaceTemperature[2],
                            telem.m_tyresSurfaceTemperature[3],
                            telem.m_tyresSurfaceTemperature[0],
                            telem.m_tyresSurfaceTemperature[1],
                        ]
                        self.state.tyres_inner_temp = [
                            telem.m_tyresInnerTemperature[2],
                            telem.m_tyresInnerTemperature[3],
                            telem.m_tyresInnerTemperature[0],
                            telem.m_tyresInnerTemperature[1],
                        ]
                        self.state.engine_temp = telem.m_engineTemperature

                    elif packet_id == 7:  # Car Status
                        status = packet.m_carStatusData[player_idx]
                        self.state.fuel_in_tank = status.m_fuelInTank
                        self.state.fuel_remaining_laps = status.m_fuelRemainingLaps
                        self.state.ers_store_energy = status.m_ersStoreEnergy
                        self.state.ers_deploy_mode = status.m_ersDeployMode

                    elif packet_id == 10:  # Car Damage
                        damage = packet.m_carDamageData[player_idx]
                        # Wear order from game: RL, RR, FL, FR
                        self.state.tyres_wear = [
                            damage.m_tyresWear[0],
                            damage.m_tyresWear[1],
                            damage.m_tyresWear[2],
                            damage.m_tyresWear[3],
                        ]
                        self.state.front_left_wing_damage = damage.m_frontLeftWingDamage
                        self.state.front_right_wing_damage = damage.m_frontRightWingDamage
                        self.state.rear_wing_damage = damage.m_rearWingDamage
                        self.state.engine_damage = damage.m_engineDamage
                        self.state.gearbox_damage = damage.m_gearBoxDamage

            except socket.timeout:
                pass
            except Exception as e:
                print(f"Error parsing UDP packet: {e}")
                traceback.print_exc()
