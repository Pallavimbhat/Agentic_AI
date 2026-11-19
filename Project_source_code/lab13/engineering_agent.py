"""Lab 13: configurable engineering specialist analysis.

Input accepts JSON rows, CSV text, or simple key=value lines. Thresholds are
illustrative and must be supplied/validated for real equipment.
"""
import csv, io, json
DEFAULTS={"mechanical":{"vibration_mm_s":4.5,"temp_c":80},"electrical":{"voltage_v":253,"current_a":20},"civil":{"crack_width_mm":0.3,"displacement_mm":10}}

def _parse(text):
    try:
        obj=json.loads(text)
        if isinstance(obj,dict): obj=obj.get("readings",[obj])
        if isinstance(obj,list) and all(isinstance(x,dict) for x in obj): return obj
    except json.JSONDecodeError: pass
    # Treat text as CSV only when a header/data row has a delimiter. A plain
    # key=value payload must not be misread as a one-column CSV document.
    if "," in text.splitlines()[0]:
        rows=list(csv.DictReader(io.StringIO(text)))
        if rows: return rows
    values={}
    for line in text.splitlines():
        if "=" in line:
            k,v=line.split("=",1)
            try: values[k.strip()]=float(v.strip())
            except ValueError: values[k.strip()]=v.strip()
    return [values] if values else []

def analyse_engineering_input(text):
    """
    Analyse all engineering sensor readings.

    Supports mechanical, civil and electrical domains.
    Checks every reading against illustrative thresholds.
    """

    # 1. Validate input
    if not isinstance(text, str) or not text.strip():
        return {
            "success": False,
            "error": "Provide JSON, CSV, or key=value sensor readings."
        }

    # 2. Identify engineering domain
    first = text.strip().splitlines()[0].lower()

    domain = next(
        (
            d for d in DEFAULTS
            if d in first or d in text[:80].lower()
        ),
        "mechanical"
    )

    # 3. Parse all sensor readings
    rows = _parse(text)

    if not rows:
        return {
            "success": False,
            "error": "Could not parse sensor readings."
        }

    # 4. Load thresholds for the selected domain
    thresholds = DEFAULTS[domain]

    # 5. Analyse every reading
    all_breaches = []
    reading_reports = []
    valid_readings = 0

    for index, row in enumerate(rows, start=1):

        numeric = {}

        # Convert sensor values into numbers
        for key, value in row.items():
            try:
                numeric[key] = float(value)
            except (ValueError, TypeError):
                continue

        if not numeric:
            continue

        valid_readings += 1
        reading_breaches = []

        # Compare every sensor with its threshold
        for sensor, value in numeric.items():

            if sensor in thresholds and value >= thresholds[sensor]:

                breach = {
                    "reading_number": index,
                    "sensor": sensor,
                    "value": value,
                    "illustrative_limit": thresholds[sensor],
                    "status": "ABNORMAL"
                }

                reading_breaches.append(breach)
                all_breaches.append(breach)

        reading_reports.append({
            "reading_number": index,
            "sensor_values": numeric,
            "status": "ABNORMAL" if reading_breaches else "NORMAL",
            "threshold_breaches": reading_breaches
        })

    # 6. Validate numeric readings
    if valid_readings == 0:
        return {
            "success": False,
            "error": "No numeric sensor readings found."
        }

    # 7. Determine overall condition
    overall_status = (
        "ALARM" if all_breaches else "NORMAL_OR_UNASSESSED"
    )

    # 8. Return engineering analysis
    return {
        "success": True,
        "domain": domain,
        "readings_received": len(rows),
        "readings_analysed": valid_readings,
        "latest_reading": rows[-1],
        "numeric_sensors": reading_reports[-1]["sensor_values"],
        "status": overall_status,
        "reading_reports": reading_reports,
        "threshold_breaches": all_breaches,
        "thresholds": thresholds,
        "threshold_note": (
            "Illustrative demonstration thresholds only; "
            "not certified engineering limits."
        ),
        "recommended_action": (
            "Escalate to a qualified engineer for review. "
            "Do not automatically control equipment."
            if all_breaches
            else "Continue monitoring and validate against approved site limits."
        ),
        "source_format": "JSON, CSV or key=value text"
    }


def predictive_maintenance_agent(log=None):
    """Backward-compatible wrapper for the original demonstration API."""
    if log is None:
        r=analyse_engineering_input('[{"vibration_mm_s":1.8,"temp_c":61},{"vibration_mm_s":2.4,"temp_c":65},{"vibration_mm_s":6.2,"temp_c":84}]')
        r["condition"]="ALARM" if r.get("status")=="ALARM" else "NORMAL"
        r["auto_executed"]=False
        return r
    r=analyse_engineering_input(__import__("json").dumps(log))
    r["condition"]=r.get("status","UNASSESSED")
    r["auto_executed"]=False
    return r
