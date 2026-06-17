import ctypes as ct

# ----------------- F1 25 UDP Packets Ctypes Definitions -----------------
# Based on the official F1 25 UDP telemetry specification (format 2025).

MAX_CARS = 22
HEADER_SIZE = 29

class PacketHeader(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_packetFormat', ct.c_uint16),           # 2025
        ('m_gameYear', ct.c_uint8),                # Game year (e.g. 25)
        ('m_gameMajorVersion', ct.c_uint8),
        ('m_gameMinorVersion', ct.c_uint8),
        ('m_packetVersion', ct.c_uint8),
        ('m_packetId', ct.c_uint8),
        ('m_sessionUID', ct.c_uint64),
        ('m_sessionTime', ct.c_float),
        ('m_frameIdentifier', ct.c_uint32),
        ('m_overallFrameIdentifier', ct.c_uint32),
        ('m_playerCarIndex', ct.c_uint8),          # Index of player's car (0-21)
        ('m_secondaryPlayerCarIndex', ct.c_uint8)  # 255 if no second player
    ]

# --- Packet ID 2: Lap Data ---
class LapData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_lastLapTimeInMS', ct.c_uint32),
        ('m_currentLapTimeInMS', ct.c_uint32),
        ('m_sector1TimeMSPart', ct.c_uint16),
        ('m_sector1TimeMinutesPart', ct.c_uint8),
        ('m_sector2TimeMSPart', ct.c_uint16),
        ('m_sector2TimeMinutesPart', ct.c_uint8),
        ('m_deltaToCarInFrontMSPart', ct.c_uint16),
        ('m_deltaToCarInFrontMinutesPart', ct.c_uint8),
        ('m_deltaToRaceLeaderMSPart', ct.c_uint16),
        ('m_deltaToRaceLeaderMinutesPart', ct.c_uint8),
        ('m_lapDistance', ct.c_float),
        ('m_totalDistance', ct.c_float),
        ('m_safetyCarDelta', ct.c_float),
        ('m_carPosition', ct.c_uint8),
        ('m_currentLapNum', ct.c_uint8),
        ('m_pitStatus', ct.c_uint8),
        ('m_numPitStops', ct.c_uint8),
        ('m_sector', ct.c_uint8),
        ('m_currentLapInvalid', ct.c_uint8),
        ('m_penalties', ct.c_uint8),
        ('m_totalWarnings', ct.c_uint8),
        ('m_cornerCuttingWarnings', ct.c_uint8),
        ('m_numUnservedDriveThroughPens', ct.c_uint8),
        ('m_numUnservedStopGoPens', ct.c_uint8),
        ('m_gridPosition', ct.c_uint8),
        ('m_driverStatus', ct.c_uint8),
        ('m_resultStatus', ct.c_uint8),
        ('m_pitLaneTimerActive', ct.c_uint8),
        ('m_pitLaneTimeInLaneInMS', ct.c_uint16),
        ('m_pitStopTimerInMS', ct.c_uint16),
        ('m_pitStopShouldServePen', ct.c_uint8),
        ('m_speedTrapFastestSpeed', ct.c_float),
        ('m_speedTrapFastestLap', ct.c_uint8),
    ]

class PacketLapData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_header', PacketHeader),
        ('m_lapData', LapData * MAX_CARS),
        ('m_timeTrialPBCarIdx', ct.c_uint8),
        ('m_timeTrialRivalCarIdx', ct.c_uint8),
    ]

# --- Packet ID 6: Car Telemetry Data ---
class CarTelemetryData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_speed', ct.c_uint16),
        ('m_throttle', ct.c_float),
        ('m_steer', ct.c_float),
        ('m_brake', ct.c_float),
        ('m_clutch', ct.c_uint8),
        ('m_gear', ct.c_int8),
        ('m_engineRPM', ct.c_uint16),
        ('m_drs', ct.c_uint8),
        ('m_revLightsPercent', ct.c_uint8),
        ('m_revLightsBitValue', ct.c_uint16),
        ('m_brakesTemperature', ct.c_uint16 * 4),
        ('m_tyresSurfaceTemperature', ct.c_uint8 * 4),
        ('m_tyresInnerTemperature', ct.c_uint8 * 4),
        ('m_engineTemperature', ct.c_uint16),
        ('m_tyresPressure', ct.c_float * 4),
        ('m_surfaceType', ct.c_uint8 * 4),
    ]

class PacketCarTelemetryData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_header', PacketHeader),
        ('m_carTelemetryData', CarTelemetryData * MAX_CARS),
        ('m_mfdPanelIndex', ct.c_uint8),
        ('m_mfdPanelIndexSecondaryPlayer', ct.c_uint8),
        ('m_suggestedGear', ct.c_int8),
    ]

# --- Packet ID 7: Car Status Data ---
class CarStatusData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_tractionControl', ct.c_uint8),
        ('m_antiLockBrakes', ct.c_uint8),
        ('m_fuelMix', ct.c_uint8),
        ('m_frontBrakeBias', ct.c_uint8),
        ('m_pitLimiterStatus', ct.c_uint8),
        ('m_fuelInTank', ct.c_float),
        ('m_fuelCapacity', ct.c_float),
        ('m_fuelRemainingLaps', ct.c_float),
        ('m_maxRPM', ct.c_uint16),
        ('m_idleRPM', ct.c_uint16),
        ('m_maxGears', ct.c_uint8),
        ('m_drsAllowed', ct.c_uint8),
        ('m_drsActivationDistance', ct.c_uint16),
        ('m_actualTyreCompound', ct.c_uint8),
        ('m_visualTyreCompound', ct.c_uint8),
        ('m_tyresAgeLaps', ct.c_uint8),
        ('m_vehicleFiaFlags', ct.c_int8),
        ('m_enginePowerICE', ct.c_float),
        ('m_enginePowerMGUK', ct.c_float),
        ('m_ersStoreEnergy', ct.c_float),
        ('m_ersDeployMode', ct.c_uint8),
        ('m_ersHarvestedThisLapMGUK', ct.c_float),
        ('m_ersHarvestedThisLapMGUH', ct.c_float),
        ('m_ersDeployedThisLap', ct.c_float),
        ('m_networkPaused', ct.c_uint8),
    ]

class PacketCarStatusData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_header', PacketHeader),
        ('m_carStatusData', CarStatusData * MAX_CARS),
    ]

# --- Packet ID 10: Car Damage Data ---
class CarDamageData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_tyresWear', ct.c_float * 4),
        ('m_tyresDamage', ct.c_uint8 * 4),
        ('m_brakesDamage', ct.c_uint8 * 4),
        ('m_tyreBlisters', ct.c_uint8 * 4),
        ('m_frontLeftWingDamage', ct.c_uint8),
        ('m_frontRightWingDamage', ct.c_uint8),
        ('m_rearWingDamage', ct.c_uint8),
        ('m_floorDamage', ct.c_uint8),
        ('m_diffuserDamage', ct.c_uint8),
        ('m_sidepodDamage', ct.c_uint8),
        ('m_drsFault', ct.c_uint8),
        ('m_ersFault', ct.c_uint8),
        ('m_gearBoxDamage', ct.c_uint8),
        ('m_engineDamage', ct.c_uint8),
        ('m_engineMGUHWear', ct.c_uint8),
        ('m_engineESWear', ct.c_uint8),
        ('m_engineCEWear', ct.c_uint8),
        ('m_engineICEWear', ct.c_uint8),
        ('m_engineMGUKWear', ct.c_uint8),
        ('m_engineTCWear', ct.c_uint8),
        ('m_engineBlown', ct.c_uint8),
        ('m_engineSeized', ct.c_uint8),
    ]

class PacketCarDamageData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_header', PacketHeader),
        ('m_carDamageData', CarDamageData * MAX_CARS),
    ]

PACKET_CLASSES = {
    2: PacketLapData,
    6: PacketCarTelemetryData,
    7: PacketCarStatusData,
    10: PacketCarDamageData,
}

# Official F1 25 packet sizes (bytes) for validation.
EXPECTED_PACKET_SIZES = {
    2: 1285,
    6: 1352,
    7: 1239,
    10: 1041,
}
