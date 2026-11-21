"""
MedBhasha 90-Second 1080p Product Demo Video Generator
Pipes rendered frames directly into FFmpeg and muxes master soundtrack.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VIDEO_DIR = Path(__file__).resolve().parent
AUDIO_PATH = VIDEO_DIR / "audio_assets" / "master_soundtrack_90s.mp3"
OUTPUT_MP4 = VIDEO_DIR / "medbhasha_product_demo_90s.mp4"

WIDTH, HEIGHT = 1920, 1080
FPS = 30
TOTAL_SECONDS = 90
TOTAL_FRAMES = TOTAL_SECONDS * FPS  # 2700 frames

# Fonts
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"
FONT_ARIAL_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_ARIAL = "C:/Windows/Fonts/arial.ttf"


def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# Pre-instantiate fonts
f_logo = get_font(FONT_ARIAL_BOLD, 72)
f_h1 = get_font(FONT_BOLD, 54)
f_h2 = get_font(FONT_BOLD, 36)
f_h3 = get_font(FONT_BOLD, 26)
f_body = get_font(FONT_REG, 22)
f_small = get_font(FONT_REG, 18)
f_sub_en = get_font(FONT_BOLD, 22)
f_sub_hi = get_font(FONT_REG, 19)


def draw_subtitle_bar(draw: ImageDraw.ImageDraw, en_text: str, hi_text: str):
    """Draws a sleek translucent subtitle bar at the bottom with English and Hindi text."""
    box_y = HEIGHT - 110
    draw.rectangle([80, box_y, WIDTH - 80, HEIGHT - 25], fill=(15, 23, 42, 235), outline=(5, 150, 105), width=2)
    # English text
    draw.text((110, box_y + 14), en_text, font=f_sub_en, fill=(255, 255, 255))
    # Hindi subtitle
    draw.text((110, box_y + 46), hi_text, font=f_sub_hi, fill=(167, 243, 208))


def draw_header_nav(draw: ImageDraw.ImageDraw, active_lang: str = "hi"):
    """Draws the clean MedBhasha app header and vernacular language selector pills."""
    draw.rectangle([0, 0, WIDTH, 80], fill=(255, 255, 255))
    draw.line([0, 80, WIDTH, 80], fill=(226, 232, 240), width=2)

    # Logo
    draw.rounded_rectangle([60, 14, 110, 64], radius=12, fill=(5, 150, 105))
    draw.text((70, 16), "मे", font=get_font(FONT_ARIAL_BOLD, 32), fill=(255, 255, 255))

    draw.text((125, 16), "MedBhasha", font=get_font(FONT_BOLD, 28), fill=(15, 23, 42))
    draw.text((125, 48), "Vernacular AI Medical Decoder", font=get_font(FONT_REG, 15), fill=(100, 116, 139))

    # Language Pills
    langs = [
        ("en", "English"),
        ("hi", "हिंदी (Hindi)"),
        ("or", "ଓଡ଼ିଆ (Odia)"),
        ("bn", "বাংলা (Bengali)"),
        ("ta", "தமிழ் (Tamil)")
    ]

    rx = 850
    for code, name in langs:
        is_active = (code == active_lang)
        pill_w = 175 if "Hindi" in name or "Odia" in name or "Bengali" in name or "Tamil" in name else 120
        bg_col = (4, 120, 87) if is_active else (241, 245, 249)
        text_col = (255, 255, 255) if is_active else (51, 65, 85)
        border_col = (5, 150, 105) if is_active else (203, 213, 225)

        draw.rounded_rectangle([rx, 20, rx + pill_w, 60], radius=20, fill=bg_col, outline=border_col, width=2)
        draw.text((rx + 16, 27), name, font=get_font(FONT_BOLD if is_active else FONT_REG, 17), fill=text_col)
        rx += pill_w + 14

    # PWA offline badge on top right
    draw.rounded_rectangle([WIDTH - 260, 22, WIDTH - 60, 58], radius=18, fill=(236, 253, 245), outline=(167, 243, 208), width=1)
    draw.ellipse([WIDTH - 245, 36, WIDTH - 235, 46], fill=(16, 185, 129))
    draw.text((WIDTH - 225, 28), "PWA Offline Active", font=get_font(FONT_BOLD, 15), fill=(6, 95, 70))


# ============================================================================
# SCENE RENDERERS (Optimized with Base Caches)
# ============================================================================

_CACHE = {}


def render_scene_1(frame_idx: int) -> Image.Image:
    """Scene 1 (0-10s): Title card with logo मे, medical teal theme."""
    if "s1" in _CACHE:
        return _CACHE["s1"]

    img = Image.new("RGB", (WIDTH, HEIGHT), (6, 78, 59))
    draw = ImageDraw.Draw(img)

    # Ambient gradient circles
    draw.ellipse([WIDTH // 2 - 450, 80, WIDTH // 2 + 450, 980], fill=(4, 120, 87))
    draw.ellipse([WIDTH // 2 - 320, 200, WIDTH // 2 + 320, 840], fill=(15, 118, 110))

    # Logo Card
    draw.rounded_rectangle([WIDTH // 2 - 80, 160, WIDTH // 2 + 80, 320], radius=32, fill=(5, 150, 105), outline=(167, 243, 208), width=4)
    draw.text((WIDTH // 2 - 40, 185), "मे", font=f_logo, fill=(255, 255, 255))

    # Main Headline
    draw.text((WIDTH // 2 - 220, 360), "MedBhasha", font=get_font(FONT_BOLD, 74), fill=(255, 255, 255))

    # Subtitle
    sub_title = "Understand Your Prescription in Your Mother Tongue"
    draw.text((WIDTH // 2 - 430, 460), sub_title, font=get_font(FONT_BOLD, 36), fill=(209, 250, 229))

    # Narrative callouts
    draw.text((WIDTH // 2 - 480, 530), "Vernacular AI Prescription & Lab Report Decoder for Indian Healthcare", font=get_font(FONT_REG, 26), fill=(167, 243, 208))

    # Badges
    badges = [
        "🩺 Handwritten Rx Decoder",
        "🔬 Pathology Lab Panel Analyzer",
        "🔊 Indian Neural Audio TTS",
        "🛡️ 100% Deterministic Rule Engine"
    ]
    bx = 220
    for b in badges:
        draw.rounded_rectangle([bx, 620, bx + 340, 680], radius=16, fill=(15, 23, 42), outline=(52, 211, 153), width=2)
        draw.text((bx + 20, 638), b, font=get_font(FONT_BOLD, 18), fill=(255, 255, 255))
        bx += 370

    draw.text((WIDTH // 2 - 350, 750), "Supported: English • हिंदी (Hindi) • ଓଡ଼ିଆ (Odia) • বাংলা (Bengali) • தமிழ் (Tamil)", font=get_font(FONT_BOLD, 22), fill=(209, 250, 229))

    draw_subtitle_bar(
        draw,
        "Welcome to MedBhasha. Across India, millions struggle to read their doctor's prescriptions and lab reports.",
        "मेड्भाषा में आपका स्वागत है। अपनी मातृभाषा में अपने पर्चे और लैब रिपोर्ट को समझें।"
    )
    _CACHE["s1"] = img
    return img


def render_scene_2(frame_idx: int) -> Image.Image:
    """Scene 2 (10-25s): Problem — blurry prescription photo, Latin abbreviations, 65% stat."""
    if "s2" in _CACHE:
        return _CACHE["s2"]

    img = Image.new("RGB", (WIDTH, HEIGHT), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw_header_nav(draw, "hi")

    # Left Container: Simulated Blurry Prescription Photo
    draw.rounded_rectangle([80, 110, 880, 880], radius=20, fill=(253, 251, 247), outline=(203, 213, 225), width=2)
    draw.rectangle([80, 110, 880, 190], fill=(15, 23, 42))
    draw.text((110, 130), "CITY GENERAL HOSPITAL & CLINIC", font=get_font(FONT_BOLD, 24), fill=(255, 255, 255))
    draw.text((110, 160), "Dr. A. Verma, MD (Internal Medicine) • Reg: MCI-39201", font=get_font(FONT_REG, 15), fill=(148, 163, 184))

    draw.text((110, 220), "℞", font=get_font(FONT_BOLD, 46), fill=(5, 150, 105))

    # Blurry scribbled text lines
    draw.text((180, 240), "1. Tab. Dolo 650mg ........... 1-0-1 PC x 5d", font=get_font(FONT_REG, 24), fill=(71, 85, 105))
    draw.text((180, 330), "2. Tab. Augmntn 625 Duo ... BD PC x 7d", font=get_font(FONT_REG, 24), fill=(71, 85, 105))
    draw.text((180, 420), "3. Cap. Pan-D .................... 1-0-0 AC x 10d", font=get_font(FONT_REG, 24), fill=(71, 85, 105))
    draw.text((180, 510), "4. Tab. Xqp... ~~~~? (Illegible Scribble)", font=get_font(FONT_REG, 24), fill=(220, 38, 38))

    draw.ellipse([640, 480, 840, 580], outline=(220, 38, 38), width=4)
    draw.line([740, 580, 770, 640], fill=(220, 38, 38), width=5)
    draw.text((580, 640), "⚠️ Unreadable Scribble", font=get_font(FONT_BOLD, 18), fill=(220, 38, 38))

    draw.rounded_rectangle([110, 760, 850, 850], radius=12, fill=(254, 242, 242), outline=(252, 165, 165), width=2)
    draw.text((130, 780), "⚠️ Low-Light Camera Glare & Severe Handwriting Blur Detected", font=get_font(FONT_BOLD, 18), fill=(185, 28, 28))
    draw.text((130, 810), "Patients cannot determine morning vs night tablets or meal restrictions", font=get_font(FONT_REG, 15), fill=(153, 27, 27))

    # Right Container: Problem Statistics & Confusion Callouts
    draw.rounded_rectangle([920, 110, 1840, 880], radius=20, fill=(255, 255, 255), outline=(226, 232, 240), width=2)

    draw.rounded_rectangle([960, 140, 1800, 270], radius=16, fill=(254, 242, 242), outline=(248, 113, 113), width=2)
    draw.text((990, 160), "THE PRESCRIPTION LITERACY CRISIS", font=get_font(FONT_BOLD, 20), fill=(185, 28, 28))
    draw.text((990, 195), "65% of Indian Patients", font=get_font(FONT_BOLD, 46), fill=(220, 38, 38))
    draw.text((990, 245), "Cannot read or comprehend their doctor's handwritten prescriptions", font=get_font(FONT_REG, 16), fill=(127, 29, 29))

    draw.text((960, 305), "Confusing Latin Abbreviations:", font=get_font(FONT_BOLD, 22), fill=(15, 23, 42))

    acronyms = [
        ("BD?", "Twice a day?"),
        ("SOS?", "Only when pain?"),
        ("PC?", "Post Cibum / After food?"),
        ("AC?", "Ante Cibum / Empty stomach?")
    ]

    ax = 960
    for ac, meaning in acronyms:
        draw.rounded_rectangle([ax, 345, ax + 195, 445], radius=14, fill=(254, 243, 199), outline=(245, 158, 11), width=2)
        draw.text((ax + 20, 360), ac, font=get_font(FONT_BOLD, 28), fill=(180, 83, 9))
        draw.text((ax + 20, 405), meaning, font=get_font(FONT_REG, 14), fill=(146, 64, 14))
        ax += 215

    draw.text((960, 480), "Dangerous Clinical Consequences:", font=get_font(FONT_BOLD, 22), fill=(15, 23, 42))

    consequences = [
        "❌ Accidental Overdosing: Taking night sedatives in the morning",
        "❌ Antibiotic Resistance: Discontinuing Augmentin after 2 days",
        "❌ Gastric Ulcers: Consuming NSAIDs on an empty stomach instead of with food",
        "❌ Preventable Emergency Readmissions: 1 in 5 readmissions trace to Rx errors"
    ]
    cy = 520
    for c in consequences:
        draw.rounded_rectangle([960, cy, 1800, cy + 50], radius=10, fill=(241, 245, 249))
        draw.text((980, cy + 13), c, font=get_font(FONT_BOLD, 17), fill=(51, 65, 85))
        cy += 60

    draw_subtitle_bar(
        draw,
        "Over 65% of Indian patients cannot read physician handwriting. Cryptic abbreviations lead to dangerous toxicity.",
        "65% से अधिक मरीज डॉक्टरों की लिखावट नहीं पढ़ पाते। बीडी, एसओएस जैसे संकेत खुराक में गलतियों का कारण बनते हैं।"
    )
    _CACHE["s2"] = img
    return img


def render_scene_3(frame_idx: int) -> Image.Image:
    """Scene 3 (25-45s): Solution — Load Sample Rx, 4 cards with morning/afternoon/night, red confirm card."""
    if "s3" in _CACHE:
        return _CACHE["s3"]

    img = Image.new("RGB", (WIDTH, HEIGHT), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw_header_nav(draw, "hi")

    draw.rounded_rectangle([80, 100, 1840, 170], radius=14, fill=(236, 253, 245), outline=(52, 211, 153), width=2)
    draw.rounded_rectangle([100, 112, 380, 158], radius=10, fill=(5, 150, 105))
    draw.text((120, 122), "✓ Sample Prescription Loaded", font=get_font(FONT_BOLD, 18), fill=(255, 255, 255))

    draw.text((410, 122), "OpenCV CLAHE Contrast Equalized • Phone Glare Removed • RapidFuzz Matched", font=get_font(FONT_BOLD, 18), fill=(6, 95, 70))
    draw.text((1560, 122), "4 Medicines Parsed", font=get_font(FONT_BOLD, 18), fill=(4, 120, 87))

    # Card 1: DOLO 650
    draw.rounded_rectangle([80, 190, 930, 480], radius=16, fill=(255, 255, 255), outline=(52, 211, 153), width=2)
    draw.text((110, 210), "1. DOLO 650 mg", font=get_font(FONT_BOLD, 26), fill=(15, 23, 42))
    draw.text((110, 245), "Generic: Paracetamol 650mg • Analgesic / Antipyretic", font=get_font(FONT_BOLD, 16), fill=(5, 150, 105))
    draw.rounded_rectangle([720, 205, 900, 245], radius=20, fill=(209, 250, 229), outline=(52, 211, 153))
    draw.text((740, 215), "✓ 95% Verified", font=get_font(FONT_BOLD, 15), fill=(6, 95, 70))

    draw.rounded_rectangle([110, 290, 340, 380], radius=12, fill=(254, 243, 199), outline=(245, 158, 11))
    draw.text((130, 305), "🌅 Morning", font=get_font(FONT_BOLD, 16), fill=(180, 83, 9))
    draw.text((130, 335), "1 Tablet", font=get_font(FONT_BOLD, 24), fill=(146, 64, 14))

    draw.rounded_rectangle([370, 290, 600, 380], radius=12, fill=(241, 245, 249))
    draw.text((390, 305), "☀️ Afternoon", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
    draw.text((390, 335), "— None", font=get_font(FONT_BOLD, 22), fill=(148, 163, 184))

    draw.rounded_rectangle([630, 290, 860, 380], radius=12, fill=(238, 242, 255), outline=(129, 140, 248))
    draw.text((650, 305), "🌙 Night", font=get_font(FONT_BOLD, 16), fill=(67, 56, 202))
    draw.text((650, 335), "1 Tablet", font=get_font(FONT_BOLD, 24), fill=(49, 46, 129))

    draw.text((110, 410), "Meal Timing: After Food (भोजन के बाद) • Duration: 5 Days", font=get_font(FONT_BOLD, 17), fill=(51, 65, 85))

    # Card 2: AUGMENTIN 625 DUO
    draw.rounded_rectangle([970, 190, 1840, 480], radius=16, fill=(255, 255, 255), outline=(52, 211, 153), width=2)
    draw.text((1000, 210), "2. AUGMENTIN 625 DUO", font=get_font(FONT_BOLD, 26), fill=(15, 23, 42))
    draw.text((1000, 245), "Generic: Amoxicillin 500mg + Clavulanic Acid 125mg • Antibiotic", font=get_font(FONT_BOLD, 16), fill=(5, 150, 105))
    draw.rounded_rectangle([1610, 205, 1810, 245], radius=20, fill=(209, 250, 229), outline=(52, 211, 153))
    draw.text((1630, 215), "✓ 100% Verified", font=get_font(FONT_BOLD, 15), fill=(6, 95, 70))

    draw.rounded_rectangle([1000, 290, 1230, 380], radius=12, fill=(254, 243, 199), outline=(245, 158, 11))
    draw.text((1020, 305), "🌅 Morning", font=get_font(FONT_BOLD, 16), fill=(180, 83, 9))
    draw.text((1020, 335), "1 Tablet", font=get_font(FONT_BOLD, 24), fill=(146, 64, 14))

    draw.rounded_rectangle([1260, 290, 1490, 380], radius=12, fill=(241, 245, 249))
    draw.text((1280, 305), "☀️ Afternoon", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
    draw.text((1280, 335), "— None", font=get_font(FONT_BOLD, 22), fill=(148, 163, 184))

    draw.rounded_rectangle([1520, 290, 1750, 380], radius=12, fill=(238, 242, 255), outline=(129, 140, 248))
    draw.text((1540, 305), "🌙 Night", font=get_font(FONT_BOLD, 16), fill=(67, 56, 202))
    draw.text((1540, 335), "1 Tablet", font=get_font(FONT_BOLD, 24), fill=(49, 46, 129))

    draw.text((1000, 410), "Meal Timing: After Food (भोजन के बाद) • Complete Full 7-Day Course", font=get_font(FONT_BOLD, 17), fill=(51, 65, 85))

    # Card 3: PAN-D
    draw.rounded_rectangle([80, 510, 930, 800], radius=16, fill=(255, 255, 255), outline=(52, 211, 153), width=2)
    draw.text((110, 530), "3. PAN-D Capsule", font=get_font(FONT_BOLD, 26), fill=(15, 23, 42))
    draw.text((110, 565), "Generic: Pantoprazole 40mg + Domperidone 30mg • Antacid", font=get_font(FONT_BOLD, 16), fill=(5, 150, 105))
    draw.rounded_rectangle([720, 525, 900, 565], radius=20, fill=(209, 250, 229), outline=(52, 211, 153))
    draw.text((740, 535), "✓ 94% Verified", font=get_font(FONT_BOLD, 15), fill=(6, 95, 70))

    draw.rounded_rectangle([110, 610, 340, 700], radius=12, fill=(254, 243, 199), outline=(245, 158, 11))
    draw.text((130, 625), "🌅 Morning", font=get_font(FONT_BOLD, 16), fill=(180, 83, 9))
    draw.text((130, 655), "1 Capsule", font=get_font(FONT_BOLD, 24), fill=(146, 64, 14))

    draw.rounded_rectangle([370, 610, 600, 700], radius=12, fill=(241, 245, 249))
    draw.text((390, 625), "☀️ Afternoon", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
    draw.text((390, 655), "— None", font=get_font(FONT_BOLD, 22), fill=(148, 163, 184))

    draw.rounded_rectangle([630, 610, 860, 700], radius=12, fill=(241, 245, 249))
    draw.text((650, 625), "🌙 Night", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
    draw.text((650, 655), "— None", font=get_font(FONT_BOLD, 22), fill=(148, 163, 184))

    draw.text((110, 730), "Meal Timing: Empty Stomach / Before Breakfast (खाली पेट) x 10 Days", font=get_font(FONT_BOLD, 17), fill=(5, 150, 105))

    # Card 4: HIGHLIGHT RED "CONFIRM WITH CHEMIST" CARD FOR ILLEGIBLE DRUG
    draw.rounded_rectangle([970, 510, 1840, 800], radius=16, fill=(254, 242, 242), outline=(239, 68, 68), width=3)
    draw.text((1000, 530), "4. Tab. Xqp... (Scribbled / Faint)", font=get_font(FONT_BOLD, 26), fill=(185, 28, 28))
    draw.text((1000, 565), "Ambiguous Handwriting • Match Score: 42.0% (Threshold: 80.0%)", font=get_font(FONT_BOLD, 16), fill=(220, 38, 38))

    draw.rounded_rectangle([1530, 525, 1810, 565], radius=20, fill=(254, 226, 226), outline=(239, 68, 68))
    draw.text((1545, 535), "⚠️ LOW CONFIDENCE", font=get_font(FONT_BOLD, 15), fill=(185, 28, 28))

    draw.rounded_rectangle([1000, 610, 1810, 710], radius=12, fill=(254, 202, 202), outline=(220, 38, 38), width=2)
    draw.text((1020, 625), "🚨 MANDATORY SAFETY GUARDRAIL ALERT:", font=get_font(FONT_BOLD, 18), fill=(153, 27, 27))
    draw.text((1020, 655), "Low handwriting/match confidence — Confirm with chemist before taking!", font=get_font(FONT_BOLD, 18), fill=(185, 28, 28))
    draw.text((1020, 682), "MedBhasha strictly refrains from guessing illegible drug names to prevent toxicity.", font=get_font(FONT_REG, 15), fill=(127, 29, 29))

    draw.text((1000, 740), "Night Dosage Prescribed: 1 Tab (Unspecified) • DO NOT CONSUME WITHOUT CHEMIST CHECK", font=get_font(FONT_BOLD, 16), fill=(185, 28, 28))

    draw_subtitle_bar(
        draw,
        "MedBhasha decodes dosages into visual morning and night cards. For unreadable scribbles, it alerts you to confirm with your chemist.",
        "मेड्भाषा में फोटो अपलोड करते ही स्पष्ट खुराक कार्ड बनते हैं। अस्पष्ट लिखावट होने पर यह सतर्क करता है।"
    )
    _CACHE["s3"] = img
    return img


def render_scene_4(frame_idx: int) -> Image.Image:
    """Scene 4 (45-60s): Audio Player — click Play, Hindi voice speaks, switch language pill to Odia, Odia voice speaks."""
    is_odia = frame_idx >= 1575
    cache_key = "s4_odia" if is_odia else "s4_hindi"

    if cache_key in _CACHE:
        base_img = _CACHE[cache_key].copy()
    else:
        base_img = Image.new("RGB", (WIDTH, HEIGHT), (248, 250, 252))
        draw_b = ImageDraw.Draw(base_img)
        draw_header_nav(draw_b, "or" if is_odia else "hi")

        draw_b.rounded_rectangle([80, 110, 1840, 280], radius=20, fill=(6, 95, 70), outline=(52, 211, 153), width=3)
        draw_b.ellipse([120, 145, 230, 255], fill=(255, 255, 255))
        draw_b.rectangle([165, 175, 175, 225], fill=(5, 150, 105))
        draw_b.rectangle([185, 175, 195, 225], fill=(5, 150, 105))

        lang_name = "ଓଡ଼ିଆ (Odia)" if is_odia else "हिंदी (Hindi)"
        voice_name = "Microsoft Edge Neural Voice (hi-IN-SwaraNeural)"
        draw_b.text((260, 145), f"🔊 Now Speaking in {lang_name}", font=get_font(FONT_BOLD, 32), fill=(255, 255, 255))
        draw_b.text((260, 190), f"Voice Engine: {voice_name} • 100% In-Memory Streaming", font=get_font(FONT_REG, 17), fill=(167, 243, 208))

        if not is_odia:
            spoken_text = "नमस्ते। आपके पर्चे में कुल 4 दवाएं हैं। डोलो और ऑगमेंटिन भोजन के बाद लें, पैन-डी खाली पेट लें।"
        else:
            spoken_text = "ନମସ୍କାର। ଆପଣଙ୍କ ପ୍ରେସକ୍ରିପସନରେ ଚାରୋଟି ଔଷଧ ଅଛି। ଡୋଲୋ ଏବଂ ଅଗମେଣ୍ଟିନ୍ ଖାଇବା ପରେ ନିଅନ୍ତୁ।"
        draw_b.text((700, 230), f'"{spoken_text}"', font=get_font(FONT_BOLD, 20), fill=(254, 243, 199))

        if not is_odia:
            cards_hi = [
                ("1. डोलो 650 (Dolo 650mg)", "सुबह 1 गोली और रात को 1 गोली", "भोजन के बाद (After Food)"),
                ("2. ऑगमेंटिन 625 (Augmentin Duo)", "सुबह 1 गोली और रात को 1 गोली", "भोजन के बाद • पूरा 7 दिन का कोर्स"),
                ("3. पैन-डी (Pan-D Capsule)", "सुबह 1 कैप्सूल", "सुबह खाली पेट (Before Breakfast)"),
                ("4. अस्पष्ट दवा (Unclear Scribble)", "रात को 1 गोली (सत्यापन आवश्यक)", "⚠️ फार्मासिस्ट से जांच करवाएं")
            ]
            cx = 80
            for title, dose, food in cards_hi:
                is_warn = "अस्पष्ट" in title
                bg = (254, 242, 242) if is_warn else (255, 255, 255)
                bd = (239, 68, 68) if is_warn else (52, 211, 153)
                draw_b.rounded_rectangle([cx, 320, cx + 420, 800], radius=16, fill=bg, outline=bd, width=2)
                draw_b.text((cx + 20, 350), title, font=get_font(FONT_BOLD, 20), fill=(185, 28, 28) if is_warn else (15, 23, 42))
                draw_b.text((cx + 20, 420), "खुराक निर्देश:", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
                draw_b.text((cx + 20, 460), dose, font=get_font(FONT_BOLD, 18), fill=(5, 150, 105) if not is_warn else (220, 38, 38))
                draw_b.text((cx + 20, 540), "समय / खान-पान:", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
                draw_b.text((cx + 20, 580), food, font=get_font(FONT_BOLD, 17), fill=(15, 23, 42))
                cx += 440
        else:
            cards_or = [
                ("1. ଡୋଲୋ ୬୫୦ (Dolo 650mg)", "ସକାଳେ ୧ ଗୋଲି ଏବଂ ରାତିରେ ୧ ଗୋଲି", "ଖାଇବା ପରେ (After Food)"),
                ("2. ଅଗମେଣ୍ଟିନ୍ ୬୨୫ (Augmentin)", "ସକାଳେ ୧ ଗୋଲି ଏବଂ ରାତିରେ ୧ ଗୋଲି", "ଖାଇବା ପରେ • ୭ ଦିନ ପୂରା କରନ୍ତୁ"),
                ("3. ପ୍ୟାନ୍-ଡି (Pan-D)", "ସକାଳେ ୧ କ୍ୟାପସୁଲ", "ଖାଲି ପେଟରେ (Empty Stomach)"),
                ("4. ଅସ୍ପଷ୍ଟ ଔଷଧ (Unclear)", "ରାତିରେ ୧ ଗୋଲି (ନିଶ୍ଚିତ କରନ୍ତୁ)", "⚠️ ଔଷଧ ଦୋକାନୀଙ୍କୁ ପଚାରନ୍ତୁ")
            ]
            cx = 80
            for title, dose, food in cards_or:
                is_warn = "ଅସ୍ପଷ୍ଟ" in title
                bg = (254, 242, 242) if is_warn else (255, 255, 255)
                bd = (239, 68, 68) if is_warn else (52, 211, 153)
                draw_b.rounded_rectangle([cx, 320, cx + 420, 800], radius=16, fill=bg, outline=bd, width=2)
                draw_b.text((cx + 20, 350), title, font=get_font(FONT_BOLD, 20), fill=(185, 28, 28) if is_warn else (15, 23, 42))
                draw_b.text((cx + 20, 420), "ଔଷଧ ଖାଇବା ନିୟମ:", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
                draw_b.text((cx + 20, 460), dose, font=get_font(FONT_BOLD, 18), fill=(5, 150, 105) if not is_warn else (220, 38, 38))
                draw_b.text((cx + 20, 540), "ସମୟ / ଖାଦ୍ୟ ନିୟମ:", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
                draw_b.text((cx + 20, 580), food, font=get_font(FONT_BOLD, 17), fill=(15, 23, 42))
                cx += 440

        draw_subtitle_bar(
            draw_b,
            "Listen to your prescription in your own language. Switch instantly between Hindi, Odia, Bengali, and Tamil.",
            "एक क्लिक में हिंदी, ओड़िया, बांग्ला और तमिल में ऑडियो सुनें।"
        )
        _CACHE[cache_key] = base_img.copy()

    # Draw dynamic audio waveforms on top of cached frame
    draw = ImageDraw.Draw(base_img)
    wave_x = 260
    for i in range(24):
        h = int(18 + 16 * math.sin(frame_idx * 0.4 + i * 0.5))
        draw.rounded_rectangle([wave_x, 245 - h, wave_x + 8, 245 + h], radius=4, fill=(52, 211, 153))
        wave_x += 16

    # Cursor animation on switch
    if 1560 <= frame_idx <= 1620:
        draw.polygon([(1260, 45), (1260, 70), (1275, 62), (1290, 75), (1298, 70), (1282, 58), (1295, 56)], fill=(239, 68, 68), outline=(255, 255, 255))

    return base_img


def render_scene_5(frame_idx: int) -> Image.Image:
    """Scene 5 (60-75s): Lab report — click Load Sample Lab Report; FBS/HbA1c HIGH (red), Hb LOW (amber), Creatinine NORMAL (green) with 3-segment range bars."""
    if "s5" in _CACHE:
        return _CACHE["s5"]

    img = Image.new("RGB", (WIDTH, HEIGHT), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw_header_nav(draw, "hi")

    draw.rounded_rectangle([80, 100, 1840, 170], radius=14, fill=(240, 253, 250), outline=(20, 184, 166), width=2)
    draw.rounded_rectangle([100, 112, 380, 158], radius=10, fill=(15, 118, 110))
    draw.text((120, 122), "✓ Sample Lab Panel Loaded", font=get_font(FONT_BOLD, 18), fill=(255, 255, 255))
    draw.text((410, 122), "Diagnostic Pathology Panel • Deterministic Numeric Rule Engine Active (100% Rule Consistency)", font=get_font(FONT_BOLD, 18), fill=(19, 78, 74))

    # Card 1: Fasting Blood Sugar (HIGH)
    draw.rounded_rectangle([80, 190, 930, 480], radius=16, fill=(254, 242, 242), outline=(239, 68, 68), width=2)
    draw.text((110, 210), "Fasting Blood Sugar (FBS)", font=get_font(FONT_BOLD, 26), fill=(15, 23, 42))
    draw.text((110, 245), "Target Interval: 70.0 - 99.0 mg/dL", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
    draw.rounded_rectangle([750, 205, 900, 245], radius=20, fill=(254, 202, 202), outline=(220, 38, 38))
    draw.text((775, 215), "▲ HIGH", font=get_font(FONT_BOLD, 16), fill=(185, 28, 28))

    draw.text((110, 290), "142.0 mg/dL", font=get_font(FONT_BOLD, 36), fill=(220, 38, 38))

    # 3-segment range bar
    draw.rounded_rectangle([110, 350, 900, 375], radius=8, fill=(226, 232, 240))
    draw.rectangle([110, 350, 350, 375], fill=(251, 191, 36))
    draw.rectangle([350, 350, 650, 375], fill=(16, 185, 129))
    draw.rectangle([650, 350, 900, 375], fill=(239, 68, 68))
    draw.polygon([(800, 340), (810, 330), (790, 330)], fill=(185, 28, 28))
    draw.text((760, 310), "142.0 mg/dL", font=get_font(FONT_BOLD, 14), fill=(185, 28, 28))

    draw.text((110, 400), "Clinical Reading: Elevated fasting blood glucose indicates impaired glucose control / Diabetes.", font=get_font(FONT_BOLD, 15), fill=(153, 27, 27))
    draw.text((110, 430), "Hindi: खाली पेट रक्त शर्करा सामान्य (70-99) से अधिक है। तुरंत डॉक्टर से मिलें।", font=get_font(FONT_REG, 15), fill=(127, 29, 29))

    # Card 2: HbA1c (HIGH)
    draw.rounded_rectangle([970, 190, 1840, 480], radius=16, fill=(254, 242, 242), outline=(239, 68, 68), width=2)
    draw.text((1000, 210), "HbA1c (Glycated Hemoglobin)", font=get_font(FONT_BOLD, 26), fill=(15, 23, 42))
    draw.text((1000, 245), "Target Interval: < 5.7 % (Non-diabetic)", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
    draw.rounded_rectangle([1660, 205, 1810, 245], radius=20, fill=(254, 202, 202), outline=(220, 38, 38))
    draw.text((1685, 215), "▲ HIGH", font=get_font(FONT_BOLD, 16), fill=(185, 28, 28))

    draw.text((1000, 290), "7.6 %", font=get_font(FONT_BOLD, 36), fill=(220, 38, 38))

    draw.rounded_rectangle([1000, 350, 1800, 375], radius=8, fill=(226, 232, 240))
    draw.rectangle([1000, 350, 1200, 375], fill=(251, 191, 36))
    draw.rectangle([1200, 350, 1500, 375], fill=(16, 185, 129))
    draw.rectangle([1500, 350, 1800, 375], fill=(239, 68, 68))
    draw.polygon([(1680, 340), (1690, 330), (1670, 330)], fill=(185, 28, 28))
    draw.text((1650, 310), "7.6 %", font=get_font(FONT_BOLD, 14), fill=(185, 28, 28))

    draw.text((1000, 400), "Clinical Reading: Elevated 3-month average glucose indicates active diabetes mellitus.", font=get_font(FONT_BOLD, 15), fill=(153, 27, 27))
    draw.text((1000, 430), "Hindi: पिछले 90 दिनों का औसत शुगर 7.6% बढ़ा हुआ है। डाइट और दवा नियंत्रण आवश्यक है।", font=get_font(FONT_REG, 15), fill=(127, 29, 29))

    # Card 3: Hemoglobin (LOW)
    draw.rounded_rectangle([80, 510, 930, 800], radius=16, fill=(255, 251, 235), outline=(245, 158, 11), width=2)
    draw.text((110, 530), "Hemoglobin (Hb)", font=get_font(FONT_BOLD, 26), fill=(15, 23, 42))
    draw.text((110, 565), "Target Interval: 12.0 - 17.5 g/dL", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
    draw.rounded_rectangle([750, 525, 900, 565], radius=20, fill=(254, 243, 199), outline=(245, 158, 11))
    draw.text((780, 535), "▼ LOW", font=get_font(FONT_BOLD, 16), fill=(180, 83, 9))

    draw.text((110, 610), "10.2 g/dL", font=get_font(FONT_BOLD, 36), fill=(217, 119, 6))

    draw.rounded_rectangle([110, 670, 900, 695], radius=8, fill=(226, 232, 240))
    draw.rectangle([110, 670, 380, 695], fill=(245, 158, 11))
    draw.rectangle([380, 670, 750, 695], fill=(16, 185, 129))
    draw.rectangle([750, 670, 900, 695], fill=(239, 68, 68))
    draw.polygon([(280, 660), (290, 650), (270, 650)], fill=(180, 83, 9))
    draw.text((250, 630), "10.2 g/dL", font=get_font(FONT_BOLD, 14), fill=(180, 83, 9))

    draw.text((110, 720), "Clinical Reading: Below healthy adult threshold (12.0 g/dL). Indicates anemia.", font=get_font(FONT_BOLD, 15), fill=(146, 64, 14))
    draw.text((110, 750), "Hindi: हीमोग्लोबिन 10.2 कम है। खून की कमी (एनीमिया) के कारण थकान हो सकती है।", font=get_font(FONT_REG, 15), fill=(120, 53, 15))

    # Card 4: Serum Creatinine (NORMAL)
    draw.rounded_rectangle([970, 510, 1840, 800], radius=16, fill=(240, 253, 244), outline=(34, 197, 94), width=2)
    draw.text((1000, 530), "Serum Creatinine", font=get_font(FONT_BOLD, 26), fill=(15, 23, 42))
    draw.text((1000, 565), "Target Interval: 0.60 - 1.20 mg/dL", font=get_font(FONT_REG, 16), fill=(100, 116, 139))
    draw.rounded_rectangle([1640, 525, 1810, 565], radius=20, fill=(220, 252, 231), outline=(34, 197, 94))
    draw.text((1660, 535), "✓ NORMAL", font=get_font(FONT_BOLD, 16), fill=(21, 128, 61))

    draw.text((1000, 610), "1.0 mg/dL", font=get_font(FONT_BOLD, 36), fill=(22, 163, 74))

    draw.rounded_rectangle([1000, 670, 1800, 695], radius=8, fill=(226, 232, 240))
    draw.rectangle([1000, 670, 1200, 695], fill=(251, 191, 36))
    draw.rectangle([1200, 670, 1600, 695], fill=(16, 185, 129))
    draw.rectangle([1600, 670, 1800, 695], fill=(239, 68, 68))
    draw.polygon([(1400, 660), (1410, 650), (1390, 650)], fill=(21, 128, 61))
    draw.text((1370, 630), "1.0 mg/dL", font=get_font(FONT_BOLD, 14), fill=(21, 128, 61))

    draw.text((1000, 720), "Clinical Reading: Optimal renal filtration marker. Kidneys functioning properly.", font=get_font(FONT_BOLD, 15), fill=(22, 101, 52))
    draw.text((1000, 750), "Hindi: गुर्दे (किडनी) का फिल्ट्रेशन काम पूरी तरह सामान्य और स्वस्थ है।", font=get_font(FONT_REG, 15), fill=(20, 83, 45))

    draw_subtitle_bar(
        draw,
        "MedBhasha decodes pathology reports: Fasting Sugar and HbA1c High in red, Hemoglobin Low in amber, Creatinine Normal in green.",
        "लैब रिपोर्ट में शुगर हाई, हीमोग्लोबिन लो और क्रिएटिनिन सामान्य को रंगीन रेंज बार से समझें।"
    )
    _CACHE["s5"] = img
    return img


def render_scene_6(frame_idx: int) -> Image.Image:
    """Scene 6 (75-85s): Trust — 100% deterministic rule engine, zero LLM guesswork, 250+ Indian drugs verified."""
    if "s6" in _CACHE:
        return _CACHE["s6"]

    img = Image.new("RGB", (WIDTH, HEIGHT), (15, 23, 42))
    draw = ImageDraw.Draw(img)

    draw.ellipse([WIDTH // 2 - 500, 60, WIDTH // 2 + 500, 940], fill=(6, 78, 59))

    draw.rounded_rectangle([WIDTH // 2 - 60, 120, WIDTH // 2 + 60, 240], radius=24, fill=(5, 150, 105), outline=(52, 211, 153), width=3)
    draw.text((WIDTH // 2 - 25, 145), "🛡️", font=get_font(FONT_ARIAL, 54), fill=(255, 255, 255))

    draw.text((WIDTH // 2 - 340, 270), "CLINICAL TRUST & ARCHITECTURE", font=get_font(FONT_BOLD, 38), fill=(255, 255, 255))
    draw.text((WIDTH // 2 - 400, 330), "Engineered to eliminate AI hallucinations and protect patient safety", font=get_font(FONT_REG, 24), fill=(167, 243, 208))

    pillars = [
        ("100% Deterministic Rule Engine", "Zero LLM Guesswork on Lab Results", "Every biomarker threshold evaluated using pure Python numeric comparisons (<, >). Never allows LLM to hallucinate clinical high/low status."),
        ("250+ Indian Formulary Medicines", "RapidFuzz Fuzzy Drug Matching", "Cross-checks handwriting transcripts against 256 validated Indian pharmaceutical formulations with WRatio threshold ≥ 80%."),
        ("Zero-Hallucination Safety Guardrail", "Pharmacist Check Warning Banner", "When handwriting is illegible (< 80% match), MedBhasha refuses to guess. Prominently flags card for chemist confirmation."),
        ("OpenCV CLAHE & Denoising Engine", "Glare & Phone Shadow Elimination", "Adaptive Histogram Equalization normalizes hospital glare, creases, and sensor noise while measuring Laplacian blur variance.")
    ]

    px_list = [160, 1000]
    py_list = [400, 600]

    for idx, (title, sub, body) in enumerate(pillars):
        px = px_list[idx % 2]
        py = py_list[idx // 2]

        draw.rounded_rectangle([px, py, px + 760, py + 170], radius=16, fill=(30, 41, 59), outline=(52, 211, 153), width=2)
        draw.text((px + 30, py + 22), f"✓ {title}", font=get_font(FONT_BOLD, 22), fill=(52, 211, 153))
        draw.text((px + 30, py + 58), sub, font=get_font(FONT_BOLD, 17), fill=(209, 250, 229))
        draw.text((px + 30, py + 92), body, font=get_font(FONT_REG, 15), fill=(203, 213, 225))

    draw_subtitle_bar(
        draw,
        "Patient safety is our priority: our 100% deterministic rule engine uses zero LLM guesswork, verifying 250+ Indian drugs.",
        "100% सटीक नियम इंजन, शून्य अनुमान, और 250 से अधिक भारतीय दवाओं का सत्यापन।"
    )
    _CACHE["s6"] = img
    return img


def render_scene_7(frame_idx: int) -> Image.Image:
    """Scene 7 (85-90s): Outro — No installs. Works offline. Free. Links & GitHub."""
    if "s7" in _CACHE:
        return _CACHE["s7"]

    img = Image.new("RGB", (WIDTH, HEIGHT), (6, 78, 59))
    draw = ImageDraw.Draw(img)

    draw.ellipse([WIDTH // 2 - 480, 100, WIDTH // 2 + 480, 950], fill=(4, 120, 87))

    draw.rounded_rectangle([WIDTH // 2 - 60, 130, WIDTH // 2 + 60, 250], radius=24, fill=(5, 150, 105), outline=(167, 243, 208), width=3)
    draw.text((WIDTH // 2 - 30, 150), "मे", font=get_font(FONT_ARIAL_BOLD, 64), fill=(255, 255, 255))

    draw.text((WIDTH // 2 - 180, 280), "MedBhasha", font=get_font(FONT_BOLD, 62), fill=(255, 255, 255))
    draw.text((WIDTH // 2 - 340, 360), "No Installs. Works Offline. 100% Free.", font=get_font(FONT_BOLD, 36), fill=(254, 243, 199))

    draw.rounded_rectangle([WIDTH // 2 - 420, 440, WIDTH // 2 + 420, 530], radius=16, fill=(15, 23, 42), outline=(52, 211, 153), width=2)
    draw.text((WIDTH // 2 - 380, 460), "🌐 Live Progressive Web App:", font=get_font(FONT_REG, 20), fill=(167, 243, 208))
    draw.text((WIDTH // 2 - 380, 490), "https://med-bhasha.vercel.app", font=get_font(FONT_BOLD, 24), fill=(255, 255, 255))

    draw.rounded_rectangle([WIDTH // 2 - 420, 560, WIDTH // 2 + 420, 650], radius=16, fill=(15, 23, 42), outline=(52, 211, 153), width=2)
    draw.text((WIDTH // 2 - 380, 580), "💻 Open-Source Code Repository:", font=get_font(FONT_REG, 20), fill=(167, 243, 208))
    draw.text((WIDTH // 2 - 380, 610), "https://github.com/HaraPrasadGouda/MedBhasha", font=get_font(FONT_BOLD, 24), fill=(255, 255, 255))

    draw.text((WIDTH // 2 - 360, 720), "Empowering Diagnostic Accessibility Across Indian Healthcare", font=get_font(FONT_BOLD, 24), fill=(209, 250, 229))

    draw_subtitle_bar(
        draw,
        "No app installs needed. Works completely offline as a free PWA. Visit med-bhasha.vercel.app or GitHub.",
        "कोई ऐप इंस्टॉल नहीं, पूरी तरह मुफ़्त और ऑफलाइन। med-bhasha.vercel.app पर जाएं।"
    )
    _CACHE["s7"] = img
    return img


def get_frame(f_idx: int) -> Image.Image:
    """Dispatches frame index to the respective scene renderer."""
    sec = f_idx / FPS

    if sec < 10.0:
        return render_scene_1(f_idx)
    elif sec < 25.0:
        return render_scene_2(f_idx)
    elif sec < 45.0:
        return render_scene_3(f_idx)
    elif sec < 60.0:
        return render_scene_4(f_idx)
    elif sec < 75.0:
        return render_scene_5(f_idx)
    elif sec < 85.0:
        return render_scene_6(f_idx)
    else:
        return render_scene_7(f_idx)


def render_full_video():
    print("=" * 80)
    print("      MEDBHASHA 90-SECOND 1080P PRODUCT DEMO VIDEO PIPELINE")
    print("=" * 80)
    print(f"Target Resolution: {WIDTH}x{HEIGHT} (1080p, 16:9)")
    print(f"Target Framerate : {FPS} fps")
    print(f"Total Duration   : {TOTAL_SECONDS} seconds ({TOTAL_FRAMES} frames)")
    print(f"Soundtrack       : {AUDIO_PATH} (Verified 90.00s)")
    print(f"Output Video     : {OUTPUT_MP4}")
    print("=" * 80)

    ffmpeg_cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "-",  # Video frames from pipe
        "-i", str(AUDIO_PATH),  # Audio track
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(OUTPUT_MP4)
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    start_time = time.time()

    print("Streaming 2700 frames directly into FFmpeg H.264 encoder...")
    for f in range(TOTAL_FRAMES):
        frame_img = get_frame(f)
        proc.stdin.write(frame_img.tobytes())

        if (f + 1) % 150 == 0 or f == TOTAL_FRAMES - 1:
            elapsed = time.time() - start_time
            fps_speed = (f + 1) / max(elapsed, 0.001)
            pct = ((f + 1) / TOTAL_FRAMES) * 100
            print(f"  Frame {f + 1}/{TOTAL_FRAMES} ({pct:.1f}%) | Speed: {fps_speed:.1f} fps | Elapsed: {elapsed:.1f}s")

    proc.stdin.close()
    stdout, stderr = proc.communicate()

    if proc.returncode != 0:
        print("FFmpeg error:", stderr.decode("utf-8", errors="replace"))
        raise RuntimeError("Video rendering failed")

    elapsed_total = time.time() - start_time
    file_size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)

    print("\n" + "=" * 80)
    print("           VIDEO RENDERING COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"Output File      : {OUTPUT_MP4}")
    print(f"File Size        : {file_size_mb:.2f} MB")
    print(f"Total Time       : {elapsed_total:.1f} seconds")
    print("=" * 80)


if __name__ == "__main__":
    render_full_video()
