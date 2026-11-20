import json
import statistics
from datetime import datetime


class EngineeringAgent:
    """Analyzes engineering sensor readings and detects anomalies."""

    def analyze(self, readings, threshold=80):
        if not readings:
            raise ValueError("Sensor readings cannot be empty.")

        if not all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in readings
        ):
            raise ValueError("All readings must be numeric.")

        average = statistics.mean(readings)
        minimum = min(readings)
        maximum = max(readings)

        anomalies = [
            {
                "reading_index": index,
                "value": value,
                "reason": f"Reading exceeds threshold of {threshold}"
            }
            for index, value in enumerate(readings)
            if value > threshold
        ]

        return {
            "agent": "Engineering Analysis Agent",
            "domain": "Sensor Data Analysis",
            "status": "anomaly_detected" if anomalies else "normal",
            "total_readings": len(readings),
            "statistics": {
                "average": round(average, 2),
                "minimum": minimum,
                "maximum": maximum
            },
            "threshold": threshold,
            "anomalies": anomalies,
            "recommendation": (
                "Inspect the sensor and investigate abnormal readings."
                if anomalies
                else "Readings are within the configured threshold."
            ),
            "timestamp": datetime.now().isoformat()
        }


def run_lab():
    readings = [35, 40, 42, 38, 45, 91, 43, 95, 39]

    result = EngineeringAgent().analyze(
        readings,
        threshold=80
    )

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    run_lab()