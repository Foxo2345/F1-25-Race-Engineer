import time


def format_lap_time(milliseconds):
    """Formats a lap time from milliseconds to M:SS.mmm string."""
    if milliseconds <= 0:
        return "0:00.000"
    total_seconds = milliseconds / 1000.0
    minutes = int(total_seconds // 60)
    seconds = total_seconds - (minutes * 60)
    return f"{minutes}:{seconds:06.3f}"


class LapTracker:
    """Tracks lap history, calculates deltas to personal best, and provides
    a formatted summary for the AI race engineer prompt."""

    def __init__(self, max_history=5):
        self.laps = []  # List of dicts: {'lap_num', 'time_ms', 'sector1_ms', 'sector2_ms', 'sector3_ms'}
        self.personal_best_ms = None
        self.max_history = max_history

    def record_lap(self, lap_num, time_ms, sector1_ms=0, sector2_ms=0):
        """Records a completed lap and updates the personal best.

        Args:
            lap_num: The lap number that was just completed.
            time_ms: Total lap time in milliseconds.
            sector1_ms: Sector 1 time in milliseconds (0 if unavailable).
            sector2_ms: Sector 2 time in milliseconds (0 if unavailable).

        Returns:
            True if a new personal best was set, False otherwise.
        """
        if time_ms <= 0:
            return False

        # Derive sector 3 from total lap time minus S1 and S2
        sector3_ms = 0
        if sector1_ms > 0 and sector2_ms > 0:
            sector3_ms = time_ms - sector1_ms - sector2_ms
            if sector3_ms < 0:
                sector3_ms = 0  # Guard against timing inconsistencies

        lap_data = {
            'lap_num': lap_num,
            'time_ms': time_ms,
            'sector1_ms': sector1_ms,
            'sector2_ms': sector2_ms,
            'sector3_ms': sector3_ms,
            'timestamp': time.time(),
        }

        self.laps.append(lap_data)

        # Keep only the last N laps
        if len(self.laps) > self.max_history:
            self.laps.pop(0)

        # Update Personal Best
        is_new_pb = False
        if self.personal_best_ms is None or time_ms < self.personal_best_ms:
            self.personal_best_ms = time_ms
            is_new_pb = True

        return is_new_pb

    def get_summary(self):
        """Returns a formatted string of recent performance for the AI prompt."""
        if not self.laps:
            return "No lap history recorded yet."

        lines = []

        # Personal Best line
        if self.personal_best_ms:
            lines.append(f"Personal Best: {format_lap_time(self.personal_best_ms)}")

        # Recent laps with delta-to-PB
        lines.append("Recent Laps (newest last):")
        for lap in self.laps:
            time_str = format_lap_time(lap['time_ms'])

            # Delta to PB
            delta_str = ""
            if self.personal_best_ms:
                diff_ms = lap['time_ms'] - self.personal_best_ms
                if diff_ms == 0:
                    delta_str = " (PB)"
                else:
                    sign = "+" if diff_ms > 0 else ""
                    delta_str = f" ({sign}{diff_ms / 1000:.3f}s)"

            # Sector breakdown if available
            sector_str = ""
            if lap['sector1_ms'] > 0 and lap['sector2_ms'] > 0:
                s1 = format_lap_time(lap['sector1_ms'])
                s2 = format_lap_time(lap['sector2_ms'])
                s3 = format_lap_time(lap['sector3_ms']) if lap['sector3_ms'] > 0 else "N/A"
                sector_str = f" [S1:{s1} S2:{s2} S3:{s3}]"

            lines.append(f"  Lap {lap['lap_num']}: {time_str}{delta_str}{sector_str}")

        # Consistency metric — std deviation of last few laps if we have 3+
        if len(self.laps) >= 3:
            times = [lap['time_ms'] for lap in self.laps]
            avg = sum(times) / len(times)
            variance = sum((t - avg) ** 2 for t in times) / len(times)
            std_dev_ms = variance ** 0.5
            lines.append(f"Consistency (std dev): {std_dev_ms / 1000:.3f}s over last {len(self.laps)} laps")

        return "\n".join(lines)

    def reset(self):
        """Clears all lap history and PB. Called on session restart."""
        self.laps.clear()
        self.personal_best_ms = None
