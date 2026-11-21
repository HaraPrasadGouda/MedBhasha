"""
MedBhasha Vernacular Localizer Service
Localizes verified medicines and rule-checked lab biomarkers into Indian regional languages:
- en (English)
- hi (Hindi - हिंदी)
- or (Odia - ଓଡ଼ିଆ)
- bn (Bengali - বাংলা)
- ta (Tamil - தமிழ்)
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.services.gemini_models import generate_content

from backend.schemas import (
    LocalizedBiomarkerExplanation,
    LocalizedGuidance,
    LocalizedMedicineSchedule,
    VerifiedDocumentResult,
)

load_dotenv()
logger = logging.getLogger("medbhasha.localizer")

SUPPORTED_LANGUAGES: Dict[str, Dict[str, str]] = {
    "en": {"name": "English", "native": "English"},
    "hi": {"name": "Hindi", "native": "हिंदी"},
    "or": {"name": "Odia", "native": "ଓଡ଼ିଆ"},
    "bn": {"name": "Bengali", "native": "বাংলা"},
    "ta": {"name": "Tamil", "native": "தமிழ்"},
}

MANDATORY_DISCLAIMERS: Dict[str, str] = {
    "en": "Important Safety Notice: This AI explanation is strictly for educational comprehension. Always verify prescription medicines, schedules, and lab test results with your treating doctor or registered pharmacist before taking any medication.",
    "hi": "महत्वपूर्ण सुरक्षा सूचना: यह AI व्याख्या केवल आपकी समझ और सुविधा के लिए है। किसी भी दवा, खुराक या जांच रिपोर्ट के संबंध में हमेशा अपने डॉक्टर या योग्य फार्मासिस्ट से परामर्श अवश्य लें।",
    "or": "ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ ସୁରକ୍ଷା ସୂଚନା: ଏହି AI ବ୍ୟାଖ୍ୟା କେବଳ ଆପଣଙ୍କ ବୁଝିବା ସୁବିଧା ପାଇଁ। କୌଣସି ଔଷଧ ସେବନ ପୂର୍ବରୁ ସର୍ବଦା ଆପଣଙ୍କ ଚିକିତ୍ସକ ଡାକ୍ତର କିମ୍ବା ଫାର୍ମାସିଷ୍ଟଙ୍କ ସହିତ ପରାମର୍ଶ କରନ୍ତୁ।",
    "bn": "জরুরি সুরক্ষা সতর্কতা: এই এআই ব্যাখ্যা শুধুমাত্র আপনার তথ্য এবং স্পষ্ট ধারণার জন্য। ওষুধ সেবন বা যেকোনো পরিবর্তনের পূর্বে সর্বদা আপনার রেজিস্টার্ড ডাক্তার বা ফার্মাসিস্টের পরামর্শ গ্রহণ করুন।",
    "ta": "முக்கிய பாதுகாப்பு அறிவிப்பு: இந்த AI விளக்கம் உங்கள் புரிதலுக்காக மட்டுமே வழங்கப்படுகிறது. எந்தவொரு மருந்தையும் உட்கொள்வதற்கு முன், எப்போதும் உங்கள் மருத்துவர் அல்லது அங்கீகரிக்கப்பட்ட மருந்தாளரிடம் சரிபார்த்துக் கொள்ளுங்கள்.",
}

LOCALIZATION_SYSTEM_PROMPT = """
You are MedBhasha's compassionate vernacular medical counselor.
Your role is to translate verified prescription schedules and deterministic lab results
into simple, crystal-clear, respectful language for Indian patients and their families.

STRICT TRANSLATION RULES:
1. RESPECT CLINICAL ACCURACY: Never alter the verified medicine names, dosage numbers, or deterministic lab status ('normal', 'high', 'low').
2. EVERYDAY CLARITY: Explain timing clearly (e.g. morning, afternoon, night, before/after meals) using everyday vocabulary.
3. SPOKEN SCRIPT REQUIREMENT:
   Generate a spoken_summary_script of EXACTLY 3 to 4 sentences in the target language.
   It must read naturally when spoken aloud via text-to-speech, greeting the patient, summarizing the total medicines, key lab flags, and reminding them to consult their doctor.
4. DOCTOR QUESTIONS: Provide 2 to 4 practical, polite questions the patient can ask their doctor during their next visit.
5. SAFETY DISCLAIMER: Output the mandatory safety disclaimer in the target language.
"""


class VernacularLocalizer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key and self.api_key != "your-gemini-api-key-here":
            self.client = genai.Client(
                api_key=self.api_key, http_options={"timeout": 90000}
            )
        else:
            self.client = None

    def _fallback_localization(
        self,
        verified_doc: VerifiedDocumentResult,
        language: str = "hi"
    ) -> LocalizedGuidance:
        """
        Deterministic, offline fallback localization when Gemini API is unconfigured or unreachable.
        Ensures the system never crashes and provides helpful vernacular schedules.
        """
        lang_info = SUPPORTED_LANGUAGES.get(language, SUPPORTED_LANGUAGES["en"])
        disclaimer = MANDATORY_DISCLAIMERS.get(language, MANDATORY_DISCLAIMERS["en"])

        # Vernacular lookup tables (offline-safe, no LLM required).
        TIMING_LABELS = {
            "en": ("Morning", "Afternoon", "Night"),
            "hi": ("सुबह", "दोपहर", "रात"),
            "or": ("ସକାଳ", "ଦିନରେ", "ରାତିରେ"),
            "bn": ("সকাল", "দুপুর", "রাত"),
            "ta": ("காலை", "மதியம்", "இரவு"),
        }
        FOOD_LABELS = {
            "en": {"before_food": "Before food", "after_food": "After food", "with_food": "With food", "unspecified": "As directed"},
            "hi": {"before_food": "खाली पेट (भोजन से पहले)", "after_food": "भोजन के बाद", "with_food": "भोजन के साथ", "unspecified": "निर्देशानुसार"},
            "or": {"before_food": "ଖାଇବା ପୂର୍ବରୁ", "after_food": "ଖାଇବା ପରେ", "with_food": "ଖାଇବା ସହିତ", "unspecified": "ନିର୍ଦ୍ଦେଶ ଅନୁସାରେ"},
            "bn": {"before_food": "খাবারের আগে", "after_food": "খাবারের পরে", "with_food": "খাবারের সাথে", "unspecified": "নির্দেশ অনুযায়ী"},
            "ta": {"before_food": "உணவுக்கு முன்", "after_food": "உணவுக்குப் பிறகு", "with_food": "உணவுடன்", "unspecified": "அறிவுறுத்தலின்படி"},
        }
        STATUS_LABELS = {
            "en": {"low": "LOW", "normal": "NORMAL", "high": "HIGH", "unverified_range": "UNVERIFIED"},
            "hi": {"low": "कम", "normal": "सामान्य", "high": "अधिक", "unverified_range": "असत्यापित"},
            "or": {"low": "କମ", "normal": "ସାମାନ୍ୟ", "high": "ବେଶି", "unverified_range": "ଅସତ୍ୟାପିତ"},
            "bn": {"low": "কম", "normal": "স্বাভাবিক", "high": "বেশি", "unverified_range": "অসত্যায়িত"},
            "ta": {"low": "குறைவு", "normal": "சாதாரண", "high": "அதிகம்", "unverified_range": "சரிபார்க்கப்படாத"},
        }
        MEASURED_LABEL = {
            "en": "Measured", "hi": "मापा गया", "or": "ମାପିତ", "bn": "পরিমাপ", "ta": "அளவிட்டது",
        }
        STANDARD_LABEL = {
            "en": "Standard range", "hi": "सामान्य मानक", "or": "ସାମାନ୍ୟ ମାନକ", "bn": "স্বাভাবিক মান", "ta": "சாதாரண வரம்பு",
        }
        QUESTIONS = {
            "en": [
                "Are there any specific dietary restrictions while taking these medicines?",
                "What should I do if I accidentally miss a dose?",
                "When should I come back for a follow-up review or repeat lab tests?",
            ],
            "hi": [
                "इन दवाओं के साथ कोई विशेष खान-पान प्रतिबंध है?",
                "यदि एक खुराक छूट जाए तो मुझे क्या करना चाहिए?",
                "फॉलो-अप या दोबारा जांच कब करानी चाहिए?",
            ],
            "or": [
                "ଏହି ଔଷଧ ସହିତ କୌଣସି ବିଶେଷ ଖାଦ୍ୟ ନିୟମ ଅଛି କି?",
                "ଯଦି ଗୋଟିଏ ଡୋଜ୍ ମିସ୍ ହୁଏ ତେବେ କ'ଣ କରିବା ଉଚିତ?",
                "ପରବର୍ତ୍ତୀ ଚେକଅପ୍ କେବେ କରିବା ଉଚିତ?",
            ],
            "bn": [
                "এই ওষুধগুলোর সাথে কি কোনো বিশেষ খাদ্য নিয়ম আছে?",
                "যদি একটি ডোজ বাদ পড়ে তবে কী করব?",
                "পরবর্তী ফলো-আপ বা পুনরায় পরীক্ষা কবে করাব?",
            ],
            "ta": [
                "இந்த மருந்துகளுடன் சிறப்பு உணவு கட்டுப்பாடு உள்ளதா?",
                "ஒரு டோஸ் தவறினால் என்ன செய்ய வேண்டும்?",
                "அடுத்த பின்தொடர்வு அல்லது மீண்டும் பரிசோதனை எப்போது செய்ய வேண்டும்?",
            ],
        }

        labels = TIMING_LABELS.get(language, TIMING_LABELS["en"])
        food_map = FOOD_LABELS.get(language, FOOD_LABELS["en"])
        status_map = STATUS_LABELS.get(language, STATUS_LABELS["en"])

        schedules = []
        for med in verified_doc.medicines:
            med_name = med.matched_name or med.raw_name
            timing_parts = []
            if med.morning_count > 0:
                timing_parts.append(f"{labels[0]}: {med.morning_count}")
            if med.afternoon_count > 0:
                timing_parts.append(f"{labels[1]}: {med.afternoon_count}")
            if med.night_count > 0:
                timing_parts.append(f"{labels[2]}: {med.night_count}")
            timing_str = ", ".join(timing_parts) if timing_parts else med.frequency_code
            schedule_text = f"{timing_str} ({med.frequency_code})"

            special = med.warning if med.warning else None

            schedules.append(
                LocalizedMedicineSchedule(
                    medicine_name=f"{med_name} ({med.dosage})",
                    schedule_text=schedule_text,
                    food_instruction=food_map.get(med.meal_timing, food_map["unspecified"]),
                    special_instructions=special,
                )
            )

        bio_explanations = []
        for bio in verified_doc.biomarkers:
            status_word = status_map.get(bio.status, bio.status.upper())
            status_plain = {
                "en": f"Result is {status_word}",
                "hi": f"परिणाम {status_word} है",
                "or": f"ଫଳାଫଳ {status_word}",
                "bn": f"ফলাফল {status_word}",
                "ta": f"முடிவு {status_word}",
            }.get(language, f"Result is {status_word}")
            meaning = bio.interpretation
            # Translate the generic deterministic interpretation into a vernacular line.
            if language != "en":
                meaning = {
                    "low": {
                        "en": "Value is below the normal range.",
                        "hi": "मान सामान्य सीमा से कम है। डॉक्टर से चर्चा करें।",
                        "or": "ମୂଲ୍ୟ ସାମାନ୍ୟ ସୀମାଠାରୁ କମ୍। ଡାକ୍ତରଙ୍କ ସହ ଆଲୋଚନା କରନ୍ତୁ।",
                        "bn": "মান স্বাভাবিক সীমার নিচে। ডাক্তারের সাথে আলোচনা করুন।",
                        "ta": "மதிப்பு சாதாரண வரம்பிற்கு கீழே உள்ளது. மருத்துவரிடம் ஆலோசிக்கவும்.",
                    },
                    "high": {
                        "en": "Value is above the normal range.",
                        "hi": "मान सामान्य सीमा से अधिक है। डॉक्टर से चर्चा करें।",
                        "or": "ମୂଲ୍ୟ ସାମାନ୍ୟ ସୀମାଠାରୁ ବେଶି। ଡାକ୍ତରଙ୍କ ସହ ଆଲୋଚନା କରନ୍ତୁ।",
                        "bn": "মান স্বাভাবিক সীমার উপরে। ডাক্তারের সাথে আলোচনা করুন।",
                        "ta": "மதிப்பு சாதாரண வரம்பிற்கு மேலே உள்ளது. மருத்துவரிடம் ஆலோசிக்கவும்.",
                    },
                    "normal": {
                        "en": "Value is within the normal range.",
                        "hi": "मान सामान्य सीमा में है।",
                        "or": "ମୂଲ୍ୟ ସାମାନ୍ୟ ସୀମାରେ ଅଛି।",
                        "bn": "মান স্বাভাবিক সীমার মধ্যে আছে।",
                        "ta": "மதிப்பு சாதாரண வரம்பில் உள்ளது.",
                    },
                    "unverified_range": {
                        "en": "Reference range not in standard registry; refer to printed report interval.",
                        "hi": "मानक रेफरेंस रेंज उपलब्ध नहीं; प्रिंटेड रिपोर्ट देखें।",
                        "or": "ମାନକ ରେଫରେନ୍ସ ରେଞ୍ଜ ଉପଲବ୍ଧ ନାହିଁ; ରିପୋର୍ଟ ଦେଖନ୍ତୁ।",
                        "bn": "স্ট্যান্ডার্ড রেফারেন্স রেঞ্জ নেই; প্রিন্টেড রিপোর্ট দেখুন।",
                        "ta": "நிலையான வரம்பு இல்லை; அச்சிடப்பட்ட அறிக்கையை பார்க்கவும்.",
                    },
                }.get(bio.status, {}).get(language, bio.interpretation)
            bio_explanations.append(
                LocalizedBiomarkerExplanation(
                    test_name=bio.normalized_test_name,
                    value_summary=f"{MEASURED_LABEL.get(language, 'Measured')}: {bio.raw_value_text} ({STANDARD_LABEL.get(language, 'Standard range')}: {bio.standard_range or 'N/A'})",
                    status_in_plain_language=status_plain,
                    meaning_and_advice=meaning,
                )
            )

        flagged = verified_doc.flagged_biomarkers_count
        if verified_doc.total_medicines > 0 and verified_doc.biomarkers:
            script = {
                "en": f"Hello. Your prescription contains {verified_doc.total_medicines} medicines and {len(verified_doc.biomarkers)} lab tests. {flagged} of these are out of range. Please follow the schedule and discuss results with your doctor.",
                "hi": f"नमस्ते। आपके पर्चे में {verified_doc.total_medicines} दवाएं और {len(verified_doc.biomarkers)} जांचें हैं। {flagged} जांच सामान्य सीमा से बाहर हैं। कृपया दवा समय पर लें और डॉक्टर से चर्चा करें।",
                "or": f"ନମସ୍କାର। ଆପଣଙ୍କ ପ୍ରେସକ୍ରିପସନରେ {verified_doc.total_medicines} ଟି ଔଷଧ ଏବଂ {len(verified_doc.biomarkers)} ଟି ଜାଞ୍ଚ ଅଛି। {flagged} ଟି ସାମାନ୍ୟ ସୀମାରୁ ବାହାର। ଦୟାକରି ସମୟାନୁଯାୟୀ ଔଷଧ ସେବନ କରନ୍ତୁ ଏବଂ ଡାକ୍ତରଙ୍କ ସହ ଆଲୋଚନା କରନ୍ତୁ।",
                "bn": f"নমস্কার। আপনার প্রেসক্রিপশনে {verified_doc.total_medicines}টি ওষুধ এবং {len(verified_doc.biomarkers)}টি পরীক্ষা রয়েছে। {flagged}টি স্বাভাবিক সীমার বাইরে। দয়া করে নিয়মিত ওষুধ খান এবং ডাক্তারের সাথে আলোচনা করুন।",
                "ta": f"வணக்கம். உங்கள் மருந்துச் சீட்டில் {verified_doc.total_medicines} மருந்துகள் மற்றும் {len(verified_doc.biomarkers)} பரிசோதனைகள் உள்ளன. {flagged} சாதாரண வரம்பிற்கு வெளியே உள்ளன. மருந்துகளை நேரத்தில் உட்கொள்ளுங்கள் மற்றும் மருத்துவரிடம் ஆலோசிக்கவும்.",
            }.get(language, f"Hello. Your prescription contains {verified_doc.total_medicines} medicines and {len(verified_doc.biomarkers)} lab tests. {flagged} are out of range.")
        elif verified_doc.total_medicines > 0:
            script = {
                "en": f"Hello. Your prescription contains {verified_doc.total_medicines} verified medicines. Please follow the schedule and meal timings. Always consult your doctor or pharmacist.",
                "hi": f"नमस्ते। आपके पर्चे में {verified_doc.total_medicines} दवाएं दर्ज हैं। कृपया समय पर दवा लें और खान-पान का ध्यान रखें। असुविधा होने पर डॉक्टर या फार्मासिस्ट से संपर्क करें।",
                "or": f"ନମସ୍କାର। ଆପଣଙ୍କ ପ୍ରେସକ୍ରିପସନରେ {verified_doc.total_medicines} ଟି ଔଷଧ ଲେଖାଯାଇଛି। ଦୟାକରି ସମୟ ଅନୁଯାୟୀ ଔଷଧ ସେବନ କରନ୍ତୁ। କୌଣସି ପ୍ରଶ୍ନ ପାଇଁ ଡାକ୍ତରଙ୍କ ସହ ଆଲୋଚନା କରନ୍ତୁ।",
                "bn": f"নমস্কার। আপনার প্রেসক্রিপশনে {verified_doc.total_medicines}টি ওষুধ লেখা রয়েছে। দয়া করে নিয়মিত ওষুধ খান। যেকোনো প্রশ্নে ডাক্তারের সাথে পরামর্শ করুন।",
                "ta": f"வணக்கம். உங்கள் மருந்துச் சீட்டில் {verified_doc.total_medicines} மருந்துகள் உள்ளன. தயவுசெய்து நேரத்தில் உட்கொள்ளுங்கள். கேள்விகளுக்கு மருத்துவரிடம் ஆலோசிக்கவும்.",
            }.get(language, f"Hello. Your prescription contains {verified_doc.total_medicines} verified medicines.")
        elif verified_doc.biomarkers:
            script = {
                "en": f"Hello. Your lab report contains {len(verified_doc.biomarkers)} tests, {flagged} of which are out of range. Please review with your doctor.",
                "hi": f"नमस्ते। आपकी लैब रिपोर्ट में {len(verified_doc.biomarkers)} जांचें हैं, जिनमें से {flagged} सामान्य सीमा से बाहर हैं। डॉक्टर से चर्चा करें।",
                "or": f"ନମସ୍କାର। ଆପଣଙ୍କ ଲ୍ୟାବ୍ ରିପୋର୍ଟରେ {len(verified_doc.biomarkers)} ଟି ଜାଞ୍ଚ ଅଛି, ଯେଉଁଥିରୁ {flagged} ଟି ସାମାନ୍ୟ ସୀମାରୁ ବାହାର। ଡାକ୍ତରଙ୍କ ସହ ଆଲୋଚନା କରନ୍ତୁ।",
                "bn": f"নমস্কার। আপনার ল্যাব রিপোর্টে {len(verified_doc.biomarkers)}টি পরীক্ষা রয়েছে, যার মধ্যে {flagged}টি স্বাভাবিক সীমার বাইরে। ডাক্তারের সাথে আলোচনা করুন।",
                "ta": f"வணக்கம். உங்கள் ஆய்வக அறிக்கையில் {len(verified_doc.biomarkers)} பரிசோதனைகள் உள்ளன, அவற்றில் {flagged} சாதாரண வரம்பிற்கு வெளியே உள்ளன. மருத்துவரிடம் ஆலோசிக்கவும்.",
            }.get(language, f"Hello. Your lab report contains {len(verified_doc.biomarkers)} tests, {flagged} out of range.")
        else:
            script = {
                "en": "Hello. No medicines or lab tests were detected in this document. Please consult your doctor.",
                "hi": "नमस्ते। इस दस्तावेज़ में कोई दवा या जांच नहीं मिली। कृपया डॉक्टर से संपर्क करें।",
                "or": "ନମସ୍କାର। ଏହି ଦସ୍ତାବେଜରେ କୌଣସି ଔଷଧ କିମ୍ବା ଜାଞ୍ଚ ମିଳିଲା ନାହିଁ। ଡାକ୍ତରଙ୍କ ସହ ଆଲୋଚନା କରନ୍ତୁ।",
                "bn": "নমস্কার। এই নথিতে কোনো ওষুধ বা পরীক্ষা পাওয়া যায়নি। ডাক্তারের সাথে পরামর্শ করুন।",
                "ta": "வணக்கம். இந்த ஆவணத்தில் மருந்துகள் அல்லது பரிசோதனைகள் எதுவும் இல்லை. மருத்துவரிடம் ஆலோசிக்கவும்.",
            }.get(language, "Hello. No medicines or lab tests were detected. Please consult your doctor.")

        spoken_script = script

        questions = QUESTIONS.get(language, QUESTIONS["en"])

        return LocalizedGuidance(
            language=language,
            language_name=lang_info["native"],
            spoken_summary_script=spoken_script,
            medicine_schedules=schedules,
            biomarker_explanations=bio_explanations,
            doctor_questions=questions,
            safety_disclaimer=disclaimer,
        )

    def generate_vernacular_guidance(
        self,
        verified_doc: VerifiedDocumentResult,
        language: str = "hi"
    ) -> LocalizedGuidance:
        """
        Translates verified prescription schedule and deterministic lab evaluations
        into patient-friendly guidance using Gemini 2.5 Flash Structured Outputs.
        """
        clean_lang = language.lower().strip()
        if clean_lang not in SUPPORTED_LANGUAGES:
            clean_lang = "hi"

        lang_meta = SUPPORTED_LANGUAGES[clean_lang]

        # If client is not available, use the robust deterministic fallback
        if not self.client:
            logger.info("Gemini API not configured, using deterministic fallback localizer.")
            return self._fallback_localization(verified_doc, clean_lang)

        prompt = f"""
        Translate and localize the following verified medical data into {lang_meta['name']} ({lang_meta['native']}).

        VERIFIED MEDICAL DATA (JSON):
        {verified_doc.model_dump_json(indent=2)}

        MANDATORY TARGET DISCLAIMER TO USE:
        "{MANDATORY_DISCLAIMERS.get(clean_lang, MANDATORY_DISCLAIMERS['en'])}"

        REQUIREMENTS:
        1. language must be "{clean_lang}" and language_name must be "{lang_meta['native']}".
        2. spoken_summary_script MUST be exactly 3 to 4 natural sentences in {lang_meta['name']} ({lang_meta['native']}) crafted for clear speech synthesis.
        3. Translate medicine schedule instructions and food timings into simple vernacular words.
        4. Explain biomarker status and meaning clearly without altering whether it was flagged as normal, high, or low.
        5. Provide 2-4 respectful questions for the patient to ask their doctor.
        6. Set safety_disclaimer to the mandatory target disclaimer provided above.
        """

        try:
            config = types.GenerateContentConfig(
                system_instruction=LOCALIZATION_SYSTEM_PROMPT,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=LocalizedGuidance,
            )

            response = generate_content(
                self.client,
                contents=[prompt],
                config=config,
                operation="vernacular localization",
            )

            if hasattr(response, "parsed") and response.parsed:
                return response.parsed

            if response.text:
                return LocalizedGuidance.model_validate_json(response.text)

        except Exception as exc:
            logger.warning(f"Gemini localization call failed: {exc}. Falling back to deterministic localizer.")

        return self._fallback_localization(verified_doc, clean_lang)


# Global singleton instance
vernacular_localizer = VernacularLocalizer()

