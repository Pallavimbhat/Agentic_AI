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
    if not isinstance(text,str) or not text.strip():
        return {"success":False,"error":"Provide JSON, CSV, or key=value sensor readings."}
    first=text.strip().splitlines()[0].lower()
    domain=next((d for d in DEFAULTS if d in first or d in text[:80].lower()),"mechanical")
    rows=_parse(text)
    if not rows: return {"success":False,"error":"Could not parse readings. Provide CSV headers or JSON objects."}
    latest=rows[-1]; numeric={}
    for k,v in latest.items():
        try:numeric[k]=float(v)
        except (ValueError,TypeError): pass
    if not numeric: return {"success":False,"error":"No numeric sensor columns found."}
    thresholds=DEFAULTS[domain]
    breaches=[{"sensor":k,"value":v,"illustrative_limit":thresholds[k]} for k,v in numeric.items() if k in thresholds and v>=thresholds[k]]
    return {"success":True,"domain":domain,"readings_received":len(rows),"latest_reading":latest,
      "numeric_sensors":numeric,"status":"ALARM" if breaches else "NORMAL_OR_UNASSESSED",
      "threshold_breaches":breaches,"thresholds":thresholds,
      "threshold_note":"Illustrative demonstration thresholds only; not certified engineering limits.",
      "recommended_action":"Escalate to a qualified engineer for review; do not automatically control equipment." if breaches else "Continue monitoring and validate against approved site limits.",
      "source_format":"JSON, CSV or key=value text"}

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
