"""Re-voice the narration in the Aiden reference voice (same settings as the user's other Qwen3-TTS videos)."""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.expanduser("~/qwen3-tts-env/bin/python")
MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16"
REF_AUDIO = os.environ.get("REF_AUDIO", "voice-ref.wav")  # a few seconds of reference speech for the TTS voice; not included, supply your own
REF_TEXT = "This is a BDD demo showing how we use Claude Code Skills to build Chiron-based training from scratch."
CHUNK_WORDS, MIN_WPS, CHUNK_GAP = 45, 1.9, 0.28
STAKES = "Serious and measured. Slightly slower on key contrasts. Weight on the consequences."
DATA = "Direct and clear. Even pacing. Clear emphasis on key numbers."
EXPLAIN = "Engaged and precise, like a good science explainer. Natural pauses between ideas."
CLOSE = "Clear and resolute. Slightly slower. Decisive on the final line."
INSTRUCT = {"s1": EXPLAIN, "s2": DATA, "s3": EXPLAIN, "s4": EXPLAIN, "s5": EXPLAIN, "s6": DATA, "s7": EXPLAIN, "s7b": DATA, "s8": DATA, "s9": EXPLAIN, "s10": CLOSE}
dur = lambda p: float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
def chunks(text):
    out, cur = [], []
    for s in re.split(r"(?<=[.?!])\s+", text.strip()):
        if cur and len(" ".join(cur + [s]).split()) > CHUNK_WORDS:
            out.append(" ".join(cur)); cur = []
        cur.append(s)
    return out + [" ".join(cur)]
def gen(text, prefix, instruct, temp="0.0"):
    subprocess.run([PY, "-m", "mlx_audio.tts.generate", "--model", MODEL, "--text", text, "--ref_audio", REF_AUDIO, "--ref_text", REF_TEXT,
                    "--instruct", instruct, "--lang_code", "en", "--temperature", temp, "--speed", "0.92", "--file_prefix", prefix, "--audio_format", "wav"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return prefix + "_000.wav"
for seg in json.load(open(os.path.join(HERE, "script.json"))):
    if os.path.exists(os.path.join(HERE, f"{seg['id']}_000.wav")): continue
    parts = []
    for i, c in enumerate(chunks(seg["text"])):
        pre = os.path.join(HERE, "aiden", f"{seg['id']}_c{i}")
        for attempt in (1, 2, 3):
            w = gen(c, pre, INSTRUCT[seg["id"]], "0.0" if attempt == 1 else "0.4"); wps = len(c.split()) / dur(w)
            if wps >= MIN_WPS: break
            print(f"  {seg['id']} chunk {i} looks truncated ({wps:.2f} wps), retry", flush=True)
        else:
            sys.exit(f"{seg['id']} chunk {i} truncated twice")
        parts.append(w)
    out = os.path.join(HERE, f"{seg['id']}_000.wav")
    if len(parts) == 1:
        subprocess.run(["cp", parts[0], out], check=True)
    else:
        ins = sum([["-i", p] for p in parts], []); n = len(parts)
        gap = f"anullsrc=r=24000:cl=mono:d={CHUNK_GAP}"
        fc = "".join(f"[{i}:a]" + (f"[g{i}]" if i < n - 1 else "") for i in range(n))
        fc = ";".join(f"{gap}[g{i}]" for i in range(n - 1)) + ";" + fc + f"concat=n={2*n-1}:v=0:a=1[o]"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc, "-map", "[o]", out], check=True)
    print(seg["id"], round(dur(out), 2), f"{len(seg['text'].split()) / dur(out):.2f} wps", flush=True)
