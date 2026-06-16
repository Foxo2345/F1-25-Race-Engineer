import ctypes as ct

# ----------------- F1 UDP Packets Ctypes Definitions -----------------
# Based on the F1 23/24 UDP telemetry specification.
# The game must be configured to output in "2023" or "2024" telemetry format.

class PacketHeader(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_packetFormat', ct.c_uint16),           # 2023/2024
        ('m_gameYear', ct.c_uint8),                # Game year
        ('m_gameMajorVersion', ct.c_uint8),        # Game major version
        ('m_gameMinorVersion', ct.c_uint8),        # Game minor version
        ('m_packetVersion', ct.c_uint8),           # Version of this packet type
        ('m_packetId', ct.c_uint8),                # Identifier for packet type (see below)
        ('m_sessionUID', ct.c_uint64),             # Unique session identifier
        ('m_sessionTime', ct.c_float),             # Session time in seconds
        ('m_frameIdentifier', ct.c_uint32),        # Identifier for the frame the data was retrieved on
        ('m_overallFrameIdentifier', ct.c_uint32), # Overall frame identifier
        ('m_playerCarIndex', ct.c_uint8),          # Index of player's car (0-21)
        ('m_secondaryPlayerCarIndex', ct.c_uint8)  # Index of secondary player's car (255 if no second player)
    ]

# --- Packet ID 2: Lap Data ---
class LapData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_lastLapTimeInMS', ct.c_uint32),            # Last lap time in milliseconds
        ('m_currentLapTimeInMS', ct.c_uint32),         # Current time around the lap in milliseconds
        ('m_sector1TimeInMS', ct.c_uint16),            # Sector 1 time in milliseconds
        ('m_sector1TimeMinutes', ct.c_uint8),          # Sector 1 whole minute part
        ('m_sector2TimeInMS', ct.c_uint16),            # Sector 2 time in milliseconds
        ('m_sector2TimeMinutes', ct.c_uint8),          # Sector 2 whole minute part
        ('m_deltaToCarAheadInMS', ct.c_uint16),        # Time delta to car ahead in milliseconds
        ('m_deltaToCarAheadMinutes', ct.c_uint8),      # Time delta to car ahead whole minute part
        ('m_deltaToRaceLeaderInMS', ct.c_uint16),      # Time delta to race leader in milliseconds
        ('m_deltaToRaceLeaderMinutes', ct.c_uint8),    # Time delta to race leader whole minute part
        ('m_lapDistance', ct.c_float),                 # Distance vehicle is around current lap in metres
        ('m_totalDistance', ct.c_float),               # Total distance travelled in session in metres
        ('m_safetyCarDelta', ct.c_float),              # Delta in seconds for safety car
        ('m_carPosition', ct.c_uint8),                 # Car race position
        ('m_currentLapNum', ct.c_uint8),               # Current lap number
        ('m_pitStatus', ct.c_uint8),                   # 0 = none, 1 = pitting, 2 = in pit area
        ('m_numPitStops', ct.c_uint8),                 # Number of pit stops taken in this race
        ('m_sector', ct.c_uint8),                      # 0 = sector1, 1 = sector2, 2 = sector3
        ('m_currentLapInvalid', ct.c_uint8),           # Current lap invalid - 0 = valid, 1 = invalid
        ('m_penalties', ct.c_uint8),                   # Accumulated time penalties in seconds
        ('m_warnings', ct.c_uint8),                    # Accumulated number of warnings
        ('m_numUnservedDriveThroughPens', ct.c_uint8), # Num drive through pens left to serve
        ('m_numUnservedStopGoPens', ct.c_uint8),       # Num stop go pens left to serve
        ('m_gridPosition', ct.c_uint8),                # Grid position the vehicle started in
        ('m_driverStatus', ct.c_uint8),                # Status of driver: 0 = in garage, 1 = flying lap, 2 = in lap, 3 = out lap, 4 = on track
        ('m_resultStatus', ct.c_uint8),                # Result status
        ('m_pitLaneTimerActive', ct.c_uint8),          # Pit lane timer active
        ('m_pitLaneTimeInLaneInMS', ct.c_uint16),      # Pit lane time in milliseconds
        ('m_pitStopTimerInMS', ct.c_uint16),           # Pit stop time in milliseconds
        ('m_pitStopShouldServePen', ct.c_uint8)        # Pit stop should serve penalty
    ]

class PacketLapData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_header', PacketHeader),
        ('m_lapData', LapData * 22),
        ('m_timeTrialPBCarIdx', ct.c_uint8),
        ('m_timeTrialRivalCarIdx', ct.c_uint8)
    ]

# --- Packet ID 6: Car Telemetry Data ---
class CarTelemetryData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_speed', ct.c_uint16),                  # Speed of car in kilometres per hour
        ('m_throttle', ct.c_float),                # Amount of throttle applied (0.0 to 1.0)
        ('m_steer', ct.c_float),                   # Steering (-1.0 to 1.0)
        ('m_brake', ct.c_float),                   # Amount of brake applied (0.0 to 1.0)
        ('m_clutch', ct.c_uint8),                  # Amount of clutch applied (0 to 100)
        ('m_gear', ct.c_int8),                     # Gear selected (1-8, N=0, R=-1)
        ('m_engineRPM', ct.c_uint16),              # Engine RPM
        ('m_drs', ct.c_uint8),                     # 0 = off, 1 = on
        ('m_revLightsPercent', ct.c_uint8),        # Rev lights indicator (percentage)
        ('m_revLightsBitValue', ct.c_uint16),      # Rev lights (bit representation)
        ('m_brakesTemperature', ct.c_uint16 * 4),  # Brakes temperature (celsius)
        ('m_tyresSurfaceTemperature', ct.c_uint8 * 4), # Tyres surface temperature (celsius)
        ('m_tyresInnerTemperature', ct.c_uint8 * 4),   # Tyres inner temperature (celsius)
        ('m_engineTemperature', ct.c_uint16),      # Engine temperature (celsius)
        ('m_tyresPressure', ct.c_float * 4),       # Tyres pressure (psi)
        ('m_surfaceType', ct.c_uint8 * 4)          # Driving surface (see documentation)
    ]

class PacketCarTelemetryData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_header', PacketHeader),
        ('m_carTelemetryData', CarTelemetryData * 22),
        ('m_mfdPanelIndex', ct.c_uint8),
        ('m_mfdPanelIndexSecondaryPlayer', ct.c_uint8),
        ('m_suggestedGear', ct.c_int8)
    ]

# --- Packet ID 7: Car Status Data ---
class CarStatusData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_tractionControl', ct.c_uint8),         # Traction control: 0 = off, 1 = medium, 2 = full
        ('m_antiLockBrakes', ct.c_uint8),          # 0 = off, 1 = on
        ('m_fuelMix', ct.c_uint8),                 # Fuel mix: 0 = lean, 1 = standard, 2 = rich, 3 = max
        ('m_frontBrakeBias', ct.c_uint8),          # Front brake bias (percentage)
        ('m_pitLimiterStatus', ct.c_uint8),        # Pit limiter status: 0 = off, 1 = on
        ('m_fuelInTank', ct.c_float),              # Current fuel mass in tank
        ('m_fuelCapacity', ct.c_float),            # Fuel capacity
        ('m_fuelRemainingLaps', ct.c_float),       # Fuel remaining in terms of laps
        ('m_maxRPM', ct.c_uint16),                 # Cars max RPM
        ('m_idleRPM', ct.c_uint16),                # Cars idle RPM
        ('m_maxGears', ct.c_uint8),                # Maximum number of gears
        ('m_drsAllowed', ct.c_uint8),              # 0 = not allowed, 1 = allowed, -1 = unknown
        ('m_drsActivationDistance', ct.c_uint16),  # 0 = DRS not available, non-zero = DRS activation distance (m)
        ('m_actualTyreCompound', ct.c_uint8),      # Actual compound (F1 Modern compounds)
        ('m_visualTyreCompound', ct.c_uint8),      # Visual compound (soft, medium, hard, etc.)
        ('m_tyresAgeLaps', ct.c_uint8),            # Age in laps of the current tyres
        ('m_vehicleFiaFlags', ct.c_int8),          # -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow, 4 = red
        # ERS Power outputs (introduced to make status packed size correct)
        ('m_enginePowerICE', ct.c_float),
        ('m_enginePowerMGUK', ct.c_float),
        ('m_enginePowerMGUH', ct.c_float),
        ('m_enginePowerES', ct.c_float),
        ('m_enginePowerCES', ct.c_float),
        ('m_enginePowerERS', ct.c_float),
        ('m_enginePowerHeatEnergyDeploy', ct.c_float),
        ('m_enginePowerHeatEnergyHarvest', ct.c_float),
        ('m_enginePowerMGUKDeploy', ct.c_float),
        ('m_enginePowerMGUKHarvest', ct.c_float),
        ('m_enginePowerMGUHDeploy', ct.c_float),
        ('m_enginePowerMGUHHarvest', ct.c_float),
        ('m_ersStoreEnergy', ct.c_float),          # ERS energy store in Joules
        ('m_ersDeployMode', ct.c_uint8),           # ERS deployment mode: 0 = none, 1 = medium, 2 = overtake, 3 = hotlap
        ('m_ersHarvestedThisLapMGUK', ct.c_float), # ERS energy harvested this lap by MGU-K
        ('m_ersHarvestedThisLapMGUH', ct.c_float), # ERS energy harvested this lap by MGU-H
        ('m_ersDeployedThisLap', ct.c_float),      # ERS energy deployed this lap
        ('m_networkPaused', ct.c_uint8)            # 0 = online/active, 1 = paused
    ]

class PacketCarStatusData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_header', PacketHeader),
        ('m_carStatusData', CarStatusData * 22)
    ]

# --- Packet ID 10: Car Damage Data ---
class CarDamageData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_tyresWear', ct.c_float * 4),           # Tyre wear (percentage)
        ('m_tyresDamage', ct.c_uint8 * 4),         # Tyre damage (percentage)
        ('m_brakesDamage', ct.c_uint8 * 4),        # Brakes damage (percentage)
        ('m_frontLeftWingDamage', ct.c_uint8),      # Front left wing damage (percentage)
        ('m_frontRightWingDamage', ct.c_uint8),     # Front right wing damage (percentage)
        ('m_rearWingDamage', ct.c_uint8),          # Rear wing damage (percentage)
        ('m_floorDamage', ct.c_uint8),             # Floor damage (percentage)
        ('m_diffuserDamage', ct.c_uint8),          # Diffuser damage (percentage)
        ('m_sidepodDamage', ct.c_uint8),           # Sidepod damage (percentage)
        ('m_drsFault', ct.c_uint8),                # Indicator for DRS fault (0 = OK, 1 = Fault)
        ('m_ersFault', ct.c_uint8),                # Indicator for ERS fault (0 = OK, 1 = Fault)
        ('m_gearBoxDamage', ct.c_uint8),           # Gearbox damage (percentage)
        ('m_engineDamage', ct.c_uint8),            # Engine damage (percentage)
        ('m_engineMGUHWear', ct.c_uint8),          # Engine MGU-H wear (percentage)
        ('m_engineESWear', ct.c_uint8),            # Engine ES wear (percentage)
        ('m_engineCEWear', ct.c_uint8),            # Engine CE wear (percentage)
        ('m_engineICEWear', ct.c_uint8),           # Engine ICE wear (percentage)
        ('m_engineMGUKWear', ct.c_uint8),          # Engine MGU-K wear (percentage)
        ('m_engineTCWear', ct.c_uint8),            # Engine TC wear (percentage)
        ('m_engineBlown', ct.c_uint8),             # Engine blown (0 = OK, 1 = Fault)
        ('m_engineSeized', ct.c_uint8)             # Engine seized (0 = OK, 1 = Fault)
    ]

class PacketCarDamageData(ct.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_header', PacketHeader),
        ('m_carDamageData', CarDamageData * 22)
    ]

# Mapping packet IDs to their ctypes classes
PACKET_CLASSES = {
    2: PacketLapData,
    6: PacketCarTelemetryData,
    7: PacketCarStatusData,
    10: PacketCarDamageData
}
