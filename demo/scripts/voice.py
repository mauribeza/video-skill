"""Voz en off con Kokoro (af_heart, en-us, speed 1.0), sincronizada por step."""
import json, subprocess, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

STEP_START = {"cover": 0.0, "s1": 2.55, "s2": 15.7, "s3": 26.25, "close": 36.95}
STEP_END = {"cover": 2.55, "s1": 15.7, "s2": 26.25, "s3": 36.95, "close": None}
SCRIPT = [
    ("cover", 0.5, "Welcome to Taskflow."),
    ("s1", 0.4, "First, create a new task. Click New task."),
    ("s1", 3.4, "Give it a short, clear title."),
    ("s1", 6.6, "Then set the priority and pick a due date."),
    ("s1", 9.9, "Click Create task, and it lands in To do."),
    ("s2", 0.4, "Next, drag the card to In progress."),
    ("s2", 5.5, "A few minutes later, its subtasks are done."),
    ("s2", 8.3, "So drop it in Done."),
    ("s3", 0.3, "Finally, open Filter and choose Assigned to me."),
    ("s3", 3.9, "Now you only see the tasks that are yours."),
    ("close", 0.6, "Thanks for watching. Happy planning with Taskflow!"),
]
SR = 24000
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            "build/video.mp4"], capture_output=True, text=True).stdout)
k = Kokoro("models/kokoro-v1.0.int8.onnx", "models/voices-v1.0.bin")
track = np.zeros(int(dur * SR) + SR, np.float32)
rows, prev_end, ok = [], 0, True
for step, off, txt in SCRIPT:
    s, sr = k.create(txt, voice="af_heart", speed=1.0, lang="en-us")
    t0 = STEP_START[step] + off; t1 = t0 + len(s) / sr
    lim = STEP_END[step] if STEP_END[step] is not None else dur
    flag = "OK"
    if t0 < prev_end: flag = "PISA LA ANTERIOR"; ok = False
    if t1 > lim: flag = f"SE PASA DEL STEP ({lim:.2f})"; ok = False
    rows.append(f"{step:5} {t0:6.2f}-{t1:6.2f}  {flag:10} {txt}")
    i = int(t0 * SR); track[i:i + len(s)] += s
    prev_end = t1
track = track[:int(dur * SR)]
sf.write("build/voice.wav", track, SR)
print("\n".join(rows)); print("video", dur, "todo OK" if ok else "HAY PROBLEMAS")
