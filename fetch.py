"""Fetch 2025 hourly GFS stratospheric winds over Europe from Open-Meteo (free, no key)."""
import json, time, urllib.request, urllib.error, numpy as np
LATS = np.arange(32.5, 65.01, 2.5)
LONS = np.arange(-15.0, 50.01, 5.0)
LEVELS = [150, 100, 70, 50, 30]  # hPa; BLE balloons fly 50-140 hPa
VARS = [f"wind_{k}_{p}hPa" for p in LEVELS for k in ("speed", "direction")]
URL = ("https://historical-forecast-api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}"
       "&start_date=2025-01-01&end_date=2025-12-31&hourly=" + ",".join(VARS) +
       "&wind_speed_unit=ms&models=gfs_global&timezone=GMT")
pts = [(la, lo) for la in LATS for lo in LONS]
U = np.full((len(LATS), len(LONS), len(LEVELS), 8760), np.nan, np.float32); V = U.copy()
B = 4
for i in range(0, len(pts), B):
    chunk = pts[i:i + B]
    url = URL.format(la=",".join(f"{a}" for a, _ in chunk), lo=",".join(f"{b}" for _, b in chunk))
    for attempt in range(30):
        try:
            res = json.load(urllib.request.urlopen(url, timeout=120)); break
        except urllib.error.HTTPError as e:
            print("HTTP", e.code, e.read()[:150], flush=True); time.sleep(60)
        except Exception as e:
            print("err", e, flush=True); time.sleep(20)
    else:
        raise SystemExit("gave up")
    res = res if isinstance(res, list) else [res]
    for (la, lo), r in zip(chunk, res):
        a, b = int(np.argmin(abs(LATS - la))), int(np.argmin(abs(LONS - lo)))
        for k, p in enumerate(LEVELS):
            s = np.array(r["hourly"][f"wind_speed_{p}hPa"], float)[:8760]
            d = np.deg2rad(np.array(r["hourly"][f"wind_direction_{p}hPa"], float)[:8760])
            U[a, b, k], V[a, b, k] = -s * np.sin(d), -s * np.cos(d)  # meteorological "from" dir
    print(f"{i + len(chunk)}/{len(pts)}", flush=True)
    time.sleep(25)
np.savez_compressed("data/gfs_europe_2025.npz", u=U, v=V, lats=LATS, lons=LONS,
                    levels_hpa=np.array(LEVELS), t0="2025-01-01T00:00")
print("done", np.isnan(U).mean())
