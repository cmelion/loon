"""Capture render(t) frame by frame and mux with narration into loon-tracks.mp4 (1920x1080, 30 fps)."""
import json, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
FPS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
total = json.loads((HERE / "segs.json").read_text())["total"]
n = int(total * FPS)
out = HERE / "loon-tracks.mp4"

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
                       "-i", str(HERE / "narration.wav"), "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto((HERE / "loon-tracks.html").as_uri())
    pg.evaluate("document.body.classList.add('capture')")
    for i in range(n):
        pg.evaluate(f"render({i / FPS})")
        ff.stdin.write(pg.screenshot(type="png"))
        if i % 300 == 0:
            print(f"{i}/{n}", flush=True)
    b.close()
ff.stdin.close(); ff.wait()
print("wrote", out, out.stat().st_size // 1024, "KB")
