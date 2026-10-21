"""Reading temperature logs.

A log is a CSV file with one reading per row. The time column may be called time_h (hours from the start),
time_min (minutes) or timestamp (any date-time pandas can read); the temperature column may be called
temp_c, temperature, temperature_c or T. Readings are sorted by time.
"""
import numpy as np
import pandas as pd

TIME_COLS = ("time_h", "time_min", "timestamp", "time", "datetime")
TEMP_COLS = ("temp_c", "temperature", "temperature_c", "t", "temp")


def read_log(path):
    """Return (hours from the first reading, temperature in deg C) as two numpy arrays."""
    df = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in df.columns}
    tcol = next((cols[c] for c in TIME_COLS if c in cols), None)
    vcol = next((cols[c] for c in TEMP_COLS if c in cols), None)
    if tcol is None or vcol is None:
        raise ValueError(f"need a time column ({', '.join(TIME_COLS)}) and a temperature column ({', '.join(TEMP_COLS)})")
    key = tcol.lower().strip()
    if key == "time_h":
        t = df[tcol].astype(float).to_numpy()
    elif key == "time_min":
        t = df[tcol].astype(float).to_numpy() / 60.0
    else:
        ts = pd.to_datetime(df[tcol])
        t = (ts - ts.min()).dt.total_seconds().to_numpy() / 3600.0
    T = df[vcol].astype(float).to_numpy()
    order = np.argsort(t, kind="stable")
    t, T = t[order], T[order]
    return t - t[0], T


def write_log(path, times_h, temps):
    pd.DataFrame({"time_h": np.round(times_h, 4), "temp_c": np.round(temps, 3)}).to_csv(path, index=False)
