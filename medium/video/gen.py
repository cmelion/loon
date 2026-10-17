"""Mix narration, time the segments, inline data + audio into loon-tracks.html (full doc) and artifact.html (skeleton-less)."""
import json, subprocess, pathlib, base64
HERE = pathlib.Path(__file__).parent
LEAD, GAP, TAIL = 0.8, 0.7, 3.0
script = json.loads((HERE / "script.json").read_text())
dur = lambda p: float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))
segs, t, parts = [], LEAD, []
for s in script:
    wav = HERE / f"{s['id']}_000.wav"; d = dur(wav)
    segs.append({"id": s["id"], "start": round(t, 3), "dur": round(d, 3), "text": s["text"]}); parts.append((wav, t)); t += d + GAP
total = round(t - GAP + TAIL, 3)
inputs, filt = [], []
for i, (wav, st) in enumerate(parts):
    inputs += ["-i", str(wav)]; filt.append(f"[{i}:a]adelay={int(st*1000)}|{int(st*1000)}[a{i}]")
filt.append("".join(f"[a{i}]" for i in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0,apad=whole_dur={total},loudnorm=I=-16:TP=-1.5[out]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-ar", "48000", "-ac", "2", str(HERE / "narration.wav")], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(HERE / "narration.wav"), "-c:a", "libmp3lame", "-b:a", "96k", str(HERE / "narration.mp3")], check=True)
b64 = "data:audio/mpeg;base64," + base64.b64encode((HERE / "narration.mp3").read_bytes()).decode()
data = (HERE / "data.json").read_text()
tpl = (HERE / "template.html").read_text()
fill = lambda audio: tpl.replace("__DATA__", data).replace("__SEGS__", json.dumps(segs)).replace("__TOTAL__", str(total)).replace("__AUDIO__", audio)
(HERE / "artifact.html").write_text(fill(b64))
(HERE / "loon-tracks.html").write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n' + fill("narration.mp3").replace("</style>", "</style></head><body>", 1) + "\n</body></html>")
(HERE / "segs.json").write_text(json.dumps({"segs": segs, "total": total}, indent=1))
print("total", total, "s; artifact", len(fill(b64)) // 1024, "KB")
for s in segs: print(s["id"], s["start"], s["dur"])
