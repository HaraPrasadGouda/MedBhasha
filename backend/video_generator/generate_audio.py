"""
Tight voiceover generator for exact 90s scene sync.
"""

import asyncio
import os
import subprocess
from pathlib import Path
import edge_tts
import imageio_ffmpeg

OUTPUT_DIR = Path(__file__).resolve().parent / "audio_assets"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VOICEOVER_SEGMENTS = [
    {
        "id": "scene1_en",
        "voice": "en-IN-NeerjaNeural",
        "rate": "+12%",
        "text": "Welcome to MedBhasha. Across India, millions struggle to read their doctor's prescriptions and lab reports. MedBhasha translates them into clear guidance in your mother tongue."
    },
    {
        "id": "scene2_en",
        "voice": "en-IN-NeerjaNeural",
        "rate": "+12%",
        "text": "Over 65% of Indian patients cannot read physician handwriting. Cryptic abbreviations like BD, SOS, and PC lead to missed doses and dangerous toxicity. When patients can't read their prescriptions, healing stops."
    },
    {
        "id": "scene3_en",
        "voice": "en-IN-NeerjaNeural",
        "rate": "+12%",
        "text": "With MedBhasha, patients simply click or snap a photo. Instantly, our OpenCV engine removes glare and organizes medicines into visual morning, afternoon, and night schedule cards. And for unreadable scribbles, MedBhasha never hallucinates—it alerts you to confirm with your chemist."
    },
    {
        "id": "scene4_intro",
        "voice": "en-IN-NeerjaNeural",
        "rate": "+12%",
        "text": "Listen to your prescription in your own language. Here in Hindi:"
    },
    {
        "id": "scene4_hi",
        "voice": "hi-IN-SwaraNeural",
        "rate": "+8%",
        "text": "नमस्ते। आपके पर्चे में कुल चार दवाएं हैं। डोलो और ऑगमेंटिन भोजन के बाद लें।"
    },
    {
        "id": "scene4_switch",
        "voice": "en-IN-NeerjaNeural",
        "rate": "+15%",
        "text": "Or switch instantly to Odia:"
    },
    {
        "id": "scene4_or",
        "voice": "hi-IN-SwaraNeural",
        "rate": "+8%",
        "text": "नमस्कार। आपणंक प्रेस्क्रिप्शनरे डोलो औषध खाईबा परे नियन्तु।"
    },
    {
        "id": "scene5_en",
        "voice": "en-IN-NeerjaNeural",
        "rate": "+12%",
        "text": "MedBhasha also decodes pathology lab reports. Fasting sugar and HbA1c are flagged High in red, Hemoglobin Low in amber, and Creatinine Normal in green, complete with 3-segment visual range bars."
    },
    {
        "id": "scene6_en",
        "voice": "en-IN-NeerjaNeural",
        "rate": "+12%",
        "text": "Patient safety is guaranteed: our 100% deterministic rule engine uses zero LLM guesswork, verifying over 250 Indian formulary medicines."
    },
    {
        "id": "scene7_en",
        "voice": "en-IN-NeerjaNeural",
        "rate": "+12%",
        "text": "No app installs. Works completely offline as a free PWA. Visit med-bhasha.vercel.app."
    }
]

async def generate():
    for seg in VOICEOVER_SEGMENTS:
        out_path = OUTPUT_DIR / f"{seg['id']}.mp3"
        comm = edge_tts.Communicate(text=seg["text"], voice=seg["voice"], rate=seg["rate"])
        await comm.save(str(out_path))
        print(f"Generated {seg['id']}")

    # Measure durations
    print("\nAudio Clip Durations:")
    for seg in VOICEOVER_SEGMENTS:
        f = OUTPUT_DIR / f"{seg['id']}.mp3"
        res = subprocess.run([FFMPEG, "-i", str(f)], stderr=subprocess.PIPE, text=True)
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                d = line.split("Duration:")[1].split(",")[0].strip()
                print(f"  {seg['id']}: {d}")

if __name__ == "__main__":
    asyncio.run(generate())
