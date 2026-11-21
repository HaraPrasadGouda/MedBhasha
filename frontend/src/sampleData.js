/**
 * MedBhasha Sample Demo Prescriptions and Lab Reports
 * Allows instant testing of the complete decoding and vernacular TTS pipeline.
 */

// SVG Data URI for realistic Sample Prescription pad
export const SAMPLE_PRESCRIPTION_IMAGE = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1000" viewBox="0 0 800 1000" style="background:%23fbf9f4;">
  <rect width="800" height="1000" fill="%23fdfbf7"/>
  <rect x="25" y="25" width="750" height="950" rx="12" fill="none" stroke="%23cbd5e1" stroke-width="2"/>
  
  <!-- Header -->
  <rect x="25" y="25" width="750" height="120" rx="12" fill="%23065f46"/>
  <text x="60" y="70" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="%23ffffff">APOLLO CLINIC &amp; HEALTHCARE</text>
  <text x="60" y="95" font-family="Arial, sans-serif" font-size="14" fill="%23a7f3d0">Dr. Rajesh Sharma, MD (Internal Medicine), Reg No: MCI-48291</text>
  <text x="60" y="118" font-family="Arial, sans-serif" font-size="12" fill="%23d1fae5">12 Ring Road, Connaught Place, New Delhi • Ph: +91 11 2345 6789</text>
  
  <!-- Patient Info -->
  <line x1="40" y1="180" x2="760" y2="180" stroke="%2394a3b8" stroke-dasharray="4,4"/>
  <text x="60" y="165" font-family="Arial, sans-serif" font-size="15" fill="%23334155">Patient: Ramesh Gupta | Age: 48 M | Date: 20-Nov-2026 | BP: 130/84 mmHg</text>
  
  <!-- Rx Symbol -->
  <text x="60" y="240" font-family="Georgia, serif" font-size="44" font-weight="bold" fill="%23047857">℞</text>
  
  <!-- Prescription Items with doctor-like handwriting styling -->
  <text x="140" y="290" font-family="'Courier New', monospace" font-size="20" font-weight="bold" fill="%230f172a">1. Tab. DOLO 650 mg</text>
  <text x="170" y="325" font-family="'Courier New', monospace" font-size="16" fill="%23334155">1 - 0 - 1  (Morning &amp; Night) [After Food] x 5 days</text>
  <text x="170" y="348" font-family="Arial, sans-serif" font-size="13" fill="%2364748b">Purpose: For viral fever &amp; severe body ache</text>
  
  <text x="140" y="410" font-family="'Courier New', monospace" font-size="20" font-weight="bold" fill="%230f172a">2. Tab. AUGMENTIN 625 DUO</text>
  <text x="170" y="445" font-family="'Courier New', monospace" font-size="16" fill="%23334155">1 - 0 - 1  (Twice daily) [After Food] x 7 days</text>
  <text x="170" y="468" font-family="Arial, sans-serif" font-size="13" fill="%2364748b">Purpose: Antibiotic for lower respiratory tract infection</text>
  
  <text x="140" y="530" font-family="'Courier New', monospace" font-size="20" font-weight="bold" fill="%230f172a">3. Cap. PAN - D</text>
  <text x="170" y="565" font-family="'Courier New', monospace" font-size="16" fill="%23334155">1 - 0 - 0  (Morning) [Empty Stomach / Before Breakfast] x 10 days</text>
  <text x="170" y="588" font-family="Arial, sans-serif" font-size="13" fill="%2364748b">Purpose: Gastric acid reducer &amp; anti-emetic</text>
  
  <text x="140" y="650" font-family="'Courier New', monospace" font-size="20" font-weight="bold" fill="%23991b1b">4. Tab. Xqp... (Scribbled / Faint)</text>
  <text x="170" y="685" font-family="'Courier New', monospace" font-size="16" fill="%23334155">0 - 0 - 1  (At Bedtime) [Unspecified]</text>
  <text x="170" y="708" font-family="Arial, sans-serif" font-size="13" fill="%23b91c1c">⚠ Handwriting partially illegible - Verify with chemist</text>

  <!-- Instructions -->
  <rect x="50" y="760" width="700" height="100" rx="8" fill="%23f1f5f9"/>
  <text x="70" y="790" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="%231e293b">Advice &amp; Follow-up:</text>
  <text x="70" y="815" font-family="Arial, sans-serif" font-size="14" fill="%23475569">• Drink 3-4 liters of boiled water daily. Steam inhalation twice a day.</text>
  <text x="70" y="838" font-family="Arial, sans-serif" font-size="14" fill="%23475569">• Review in OPD after 5 days with repeat CBC report.</text>
  
  <!-- Stamp / Signature -->
  <text x="560" y="910" font-family="'Brush Script MT', cursive, sans-serif" font-size="24" fill="%231e3a8a">R. Sharma, MD</text>
  <line x1="530" y1="920" x2="720" y2="920" stroke="%23334155"/>
  <text x="560" y="938" font-family="Arial, sans-serif" font-size="12" fill="%2364748b">Doctor Signature &amp; Stamp</text>
</svg>`;

// SVG Data URI for realistic Sample Lab Report
export const SAMPLE_LAB_REPORT_IMAGE = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1000" viewBox="0 0 800 1000" style="background:%23ffffff;">
  <rect width="800" height="1000" fill="%23ffffff"/>
  <rect x="25" y="25" width="750" height="950" rx="8" fill="none" stroke="%23e2e8f0" stroke-width="2"/>
  
  <!-- Lab Header -->
  <rect x="25" y="25" width="750" height="100" fill="%230f766e"/>
  <text x="50" y="65" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="%23ffffff">THYROCARE DIAGNOSTICS &amp; PATHOLOGY</text>
  <text x="50" y="90" font-family="Arial, sans-serif" font-size="13" fill="%23ccfbf1">NABL Accredited • ISO 15189:2012 Certified Central Reference Lab</text>
  
  <!-- Patient Bar -->
  <rect x="25" y="125" width="750" height="70" fill="%23f8fafc"/>
  <text x="50" y="152" font-family="Arial, sans-serif" font-size="14" fill="%231e293b">Patient: Suresh Patel | Age: 52 Y / M | Ref By: Dr. A. K. Verma</text>
  <text x="50" y="176" font-family="Arial, sans-serif" font-size="13" fill="%2364748b">Sample Collected: Fasting Serum | Report Date: 20-Nov-2026</text>
  
  <!-- Table Header -->
  <rect x="40" y="215" width="720" height="40" fill="%23f1f5f9"/>
  <text x="60" y="240" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="%231e293b">Test Investigation Name</text>
  <text x="340" y="240" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="%231e293b">Result</text>
  <text x="460" y="240" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="%231e293b">Units</text>
  <text x="580" y="240" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="%231e293b">Reference Range</text>
  
  <!-- Test 1: Fasting Blood Sugar (High) -->
  <line x1="40" y1="310" x2="760" y2="310" stroke="%23e2e8f0"/>
  <text x="60" y="290" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="%230f172a">Fasting Blood Sugar (FBS)</text>
  <text x="340" y="290" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="%23dc2626">142.0  ▲ HIGH</text>
  <text x="460" y="290" font-family="Arial, sans-serif" font-size="14" fill="%23475569">mg/dL</text>
  <text x="580" y="290" font-family="Arial, sans-serif" font-size="14" fill="%2364748b">70.0 - 99.0</text>
  
  <!-- Test 2: HbA1c (High) -->
  <line x1="40" y1="375" x2="760" y2="375" stroke="%23e2e8f0"/>
  <text x="60" y="355" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="%230f172a">HbA1c (Glycated Hemoglobin)</text>
  <text x="340" y="355" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="%23dc2626">7.6  ▲ HIGH</text>
  <text x="460" y="355" font-family="Arial, sans-serif" font-size="14" fill="%23475569">%</text>
  <text x="580" y="355" font-family="Arial, sans-serif" font-size="14" fill="%2364748b">&lt; 5.7 (Non-diabetic)</text>
  
  <!-- Test 3: Hemoglobin (Low) -->
  <line x1="40" y1="440" x2="760" y2="440" stroke="%23e2e8f0"/>
  <text x="60" y="420" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="%230f172a">Hemoglobin (Hb)</text>
  <text x="340" y="420" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="%23d97706">10.2  ▼ LOW</text>
  <text x="460" y="420" font-family="Arial, sans-serif" font-size="14" fill="%23475569">g/dL</text>
  <text x="580" y="420" font-family="Arial, sans-serif" font-size="14" fill="%2364748b">12.0 - 17.5</text>
  
  <!-- Test 4: Serum Creatinine (Normal) -->
  <line x1="40" y1="505" x2="760" y2="505" stroke="%23e2e8f0"/>
  <text x="60" y="485" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="%230f172a">Serum Creatinine</text>
  <text x="340" y="485" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="%2316a34a">1.0  ✓ NORMAL</text>
  <text x="460" y="485" font-family="Arial, sans-serif" font-size="14" fill="%23475569">mg/dL</text>
  <text x="580" y="485" font-family="Arial, sans-serif" font-size="14" fill="%2364748b">0.6 - 1.2</text>
  
  <!-- Test 5: Serum TSH (High) -->
  <line x1="40" y1="570" x2="760" y2="570" stroke="%23e2e8f0"/>
  <text x="60" y="550" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="%230f172a">Serum TSH (Thyroid)</text>
  <text x="340" y="550" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="%23dc2626">6.8  ▲ HIGH</text>
  <text x="460" y="550" font-family="Arial, sans-serif" font-size="14" fill="%23475569">uIU/mL</text>
  <text x="580" y="550" font-family="Arial, sans-serif" font-size="14" fill="%2364748b">0.4 - 4.5</text>

  <!-- Notes & Disclaimer -->
  <rect x="40" y="620" width="720" height="150" fill="%23f8fafc" rx="8"/>
  <text x="60" y="650" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="%23334155">Clinical Interpretation Note:</text>
  <text x="60" y="675" font-family="Arial, sans-serif" font-size="13" fill="%23475569">1. Both Fasting Sugar (142 mg/dL) and HbA1c (7.6%) indicate uncontrolled diabetes.</text>
  <text x="60" y="700" font-family="Arial, sans-serif" font-size="13" fill="%23475569">2. Elevated TSH indicates subclinical or primary hypothyroidism. Correlate with free T4.</text>
  <text x="60" y="725" font-family="Arial, sans-serif" font-size="13" fill="%23475569">3. Mild anemia detected (Hb 10.2 g/dL). Recommend iron studies or peripheral smear.</text>
  
  <text x="540" y="850" font-family="'Brush Script MT', cursive, sans-serif" font-size="22" fill="%230f766e">Dr. P. Sen, MD Pathologist</text>
  <text x="540" y="870" font-family="Arial, sans-serif" font-size="12" fill="%2364748b">Consultant Pathologist</text>
</svg>`;

// Complete Mock Analysis Payloads for Prescription Demo
export function getSamplePrescriptionData(language = 'hi') {
  const languageNames = {
    hi: 'हिंदी (Hindi)',
    en: 'English',
    or: 'ଓଡ଼ିଆ (Odia)',
    bn: 'বাংলা (Bengali)',
    ta: 'தமிழ் (Tamil)',
  };

  const spokenScripts = {
    hi: 'नमस्ते। आपके पर्चे में कुल 4 दवाएं दर्ज हैं। डोलो और ऑगमेंटिन खाना खाने के बाद लेनी हैं, और पैन-डी सुबह खाली पेट लें। चौथी दवा की लिखावट अस्पष्ट है, इसलिए कोई भी गोली लेने से पहले कृपया मेडिकल स्टोर या फार्मासिस्ट से जरूर पुष्टि करें।',
    en: 'Hello. Your prescription has 4 recorded medicines. Take Dolo and Augmentin after meals, and Pan-D in the morning before food. The fourth medicine name is partially illegible, so please confirm with your pharmacist before taking it.',
    or: 'ନମସ୍କାର। ଆପଣଙ୍କ ପ୍ରେସକ୍ରିପସନରେ ୪ଟି ଔଷଧ ଲେଖାଯାଇଛି। ଡୋଲୋ ଏବଂ ଅଗମେଣ୍ଟିନ୍ ଖାଇବା ପରେ ନିଅନ୍ତୁ, ଏବଂ ପ୍ୟାନ୍-ଡି ସକାଳେ ଖାଲି ପେଟରେ ନିଅନ୍ତୁ। ଚତୁର୍ଥ ଔଷଧର ଲେଖା ସ୍ପଷ୍ଟ ନୁହେଁ, ଦୟାକରି ଔଷଧ ଦୋକାନୀଙ୍କ ସହ ନିଶ୍ଚିତ କରନ୍ତୁ।',
    bn: 'নমস্কার। আপনার প্রেসক্রিপশনে মোট ৪টি ওষুধ রয়েছে। ডলো এবং অগমেন্টিন খাওয়ার পরে নিন, এবং প্যান-ডি সকালে খালি পেটে খান। চতুর্থ ওষুধের হাতের লেখা অস্পষ্ট, তাই ওষুধ খাওয়ার আগে অবশ্যই ফার্মাসিস্টের সাথে কথা বলুন।',
    ta: 'வணக்கம். உங்கள் மருந்துச் சீட்டில் மொத்தம் 4 மருந்துகள் உள்ளன. டோலோ மற்றும் ஆக்மென்டின் உணவுக்குப் பிறகு உட்கொள்ள வேண்டும், பான்-டி காலையில் வெறும் வயிற்றில் சாப்பிடவும். நான்காவது மருந்தின் பெயர் தெளிவாக இல்லை, தயவுசெய்து மருந்தாளரிடம் சரிபார்க்கவும்.',
  };

  const disclaimers = {
    hi: 'महत्वपूर्ण सुरक्षा सूचना: यह AI व्याख्या केवल आपकी समझ और सुविधा के लिए है। किसी भी दवा, खुराक या जांच रिपोर्ट के संबंध में हमेशा अपने डॉक्टर या योग्य फार्मासिस्ट से परामर्श अवश्य लें।',
    en: 'Important Safety Notice: This AI explanation is strictly for educational comprehension. Always verify prescription medicines, schedules, and lab test results with your treating doctor or registered pharmacist before taking any medication.',
    or: 'ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ ସୁରକ୍ଷା ସୂଚନା: ଏହି AI ବ୍ୟାଖ୍ୟା କେବଳ ଆପଣଙ୍କ ବୁଝିବା ସୁବିଧା ପାଇଁ। କୌଣସି ଔଷଧ ସେବନ ପୂର୍ବରୁ ସର୍ବଦା ଆପଣଙ୍କ ଚିକିତ୍ସକ ଡାକ୍ତର କିମ୍ବା ଫାର୍ମାସିଷ୍ଟଙ୍କ ସହିତ ପରାମର୍ଶ କରନ୍ତୁ।',
    bn: 'জরুরি সুরক্ষা সতর্কতা: এই এআই ব্যাখ্যা শুধুমাত্র আপনার তথ্য এবং স্পষ্ট ধারণার জন্য। ওষুধ সেবন বা যেকোনো পরিবর্তনের পূর্বে সর্বদা আপনার রেজিস্টার্ড ডাক্তার বা ফার্মাসিস্টের পরামর্শ গ্রহণ করুন।',
    ta: 'முக்கிய பாதுகாப்பு அறிவிப்பு: இந்த AI விளக்கம் உங்கள் புரிதலுக்காக மட்டுமே வழங்கப்படுகிறது. எந்தவொரு மருந்தையும் உட்கொள்வதற்கு முன், எப்போதும் உங்கள் மருத்துவர் அல்லது அங்கீகரிக்கப்பட்ட மருந்தாளரிடம் சரிபார்த்துக் கொள்ளுங்கள்.',
  };

  return {
    success: true,
    filename: 'Sample_Dr_Sharma_Prescription.png',
    language: language,
    quality_metrics: {
      blur_variance: 165.4,
      brightness_score: 182.3,
      is_blurry: false,
      is_too_dark: false,
      is_too_bright: false,
      quality_status: 'good',
      warnings: [],
    },
    dimensions: {
      original_width: 800,
      original_height: 1000,
      processed_width: 800,
      processed_height: 1000,
    },
    preview_base64: SAMPLE_PRESCRIPTION_IMAGE,
    raw_extraction: {
      document_type: 'prescription',
      patient_instructions: [
        'Drink 3-4 liters of boiled water daily',
        'Steam inhalation twice a day',
        'Review in OPD after 5 days with repeat CBC report'
      ]
    },
    verification: {
      document_type: 'prescription',
      patient_instructions: [
        'Drink 3-4 liters of boiled water daily',
        'Steam inhalation twice a day',
        'Review in OPD after 5 days with repeat CBC report'
      ],
      total_medicines: 4,
      verified_medicines_count: 3,
      low_confidence_medicines_count: 1,
      flagged_biomarkers_count: 0,
      medicines: [
        {
          raw_name: 'Tab. DOLO 650 mg',
          dosage: '650mg',
          frequency_code: '1-0-1',
          morning_count: 1.0,
          afternoon_count: 0.0,
          night_count: 1.0,
          meal_timing: 'after_food',
          duration_days: 5,
          general_purpose: 'Fever and body pain relief',
          matched_name: 'Dolo 650',
          generic_composition: 'Paracetamol 650mg',
          category: 'Analgesic / Antipyretic',
          confidence_score: 95.0,
          verification_status: 'verified',
          warning: null
        },
        {
          raw_name: 'Tab. AUGMENTIN 625 DUO',
          dosage: '625mg',
          frequency_code: '1-0-1',
          morning_count: 1.0,
          afternoon_count: 0.0,
          night_count: 1.0,
          meal_timing: 'after_food',
          duration_days: 7,
          general_purpose: 'Antibiotic for lower respiratory tract infection',
          matched_name: 'Augmentin 625 Duo',
          generic_composition: 'Amoxicillin 500mg + Clavulanic Acid 125mg',
          category: 'Antibiotic',
          confidence_score: 100.0,
          verification_status: 'verified',
          warning: null
        },
        {
          raw_name: 'Cap. PAN - D',
          dosage: '40mg',
          frequency_code: '1-0-0',
          morning_count: 1.0,
          afternoon_count: 0.0,
          night_count: 0.0,
          meal_timing: 'before_food',
          duration_days: 10,
          general_purpose: 'Gastric acid reducer & anti-emetic',
          matched_name: 'Pan-D',
          generic_composition: 'Pantoprazole 40mg + Domperidone 30mg',
          category: 'Gastrointestinal',
          confidence_score: 94.0,
          verification_status: 'verified',
          warning: null
        },
        {
          raw_name: 'Tab. Xqp... (Scribbled / Faint)',
          dosage: 'Unspecified',
          frequency_code: '0-0-1',
          morning_count: 0.0,
          afternoon_count: 0.0,
          night_count: 1.0,
          meal_timing: 'unspecified',
          duration_days: null,
          general_purpose: 'Unknown / Illegible handwriting',
          matched_name: null,
          generic_composition: null,
          category: null,
          confidence_score: 42.0,
          verification_status: 'low_confidence',
          warning: 'Low handwriting/match confidence — confirm with pharmacist before taking'
        }
      ],
      biomarkers: [],
      drug_interactions: [
        {
          severity: 'info',
          alert_type: 'food_or_lifestyle',
          medicines_involved: ['Pan-D', 'Augmentin 625 Duo'],
          title: 'Timing Optimization: Antibiotic & Antacid Absorption',
          description: 'Take Pan-D strictly 30 minutes before breakfast on an empty stomach. Take Augmentin 625 Duo after food to minimize gastric discomfort.',
          action_recommendation: 'Maintain a 60-minute interval between your empty-stomach antacid and antibiotic dose for optimal bioavailability.'
        }
      ]
    },
    localized_guidance: {
      language: language,
      language_name: languageNames[language] || 'Hindi',
      spoken_summary_script: spokenScripts[language] || spokenScripts['hi'],
      medicine_schedules: [
        {
          medicine_name: 'Dolo 650 (Paracetamol 650mg)',
          schedule_text: language === 'hi' ? 'सुबह 1 गोली और रात को 1 गोली' : '1 tablet in the morning and 1 tablet at night',
          food_instruction: language === 'hi' ? 'भोजन के बाद (After Food)' : 'After meals',
          special_instructions: 'For fever and body pain'
        },
        {
          medicine_name: 'Augmentin 625 Duo (Amoxicillin + Clavulanic Acid)',
          schedule_text: language === 'hi' ? 'सुबह 1 गोली और रात को 1 गोली (पूरा 7 दिन का कोर्स करें)' : '1 tablet morning and 1 at night (Complete 7-day course)',
          food_instruction: language === 'hi' ? 'भोजन के बाद (After Food)' : 'After meals',
          special_instructions: 'Antibiotic - do not stop early'
        },
        {
          medicine_name: 'Pan-D (Pantoprazole + Domperidone)',
          schedule_text: language === 'hi' ? 'सुबह 1 कैप्सूल (खाली पेट)' : '1 capsule in the morning (Empty stomach)',
          food_instruction: language === 'hi' ? 'नाश्ते से आधा घंटा पहले (Before Food)' : '30 mins before breakfast',
          special_instructions: 'For acidity and nausea prevention'
        },
        {
          medicine_name: 'Unclear Scribbled Drug (अस्पष्ट दवा)',
          schedule_text: language === 'hi' ? 'रात को 1 गोली (सत्यापन आवश्यक)' : '1 tablet at bedtime (Verification required)',
          food_instruction: language === 'hi' ? 'फार्मासिस्ट से पुष्टि करें' : 'Confirm with pharmacist',
          special_instructions: 'Low match confidence — do not take without chemist confirmation'
        }
      ],
      biomarker_explanations: [],
      doctor_questions: [
        'Should I continue Dolo 650 once the fever subsides?',
        'Can I take Pan-D with lukewarm water?',
        'What is the fourth medicine prescribed for the night?'
      ],
      safety_disclaimer: disclaimers[language] || disclaimers['hi']
    },
    spoken_summary_script: spokenScripts[language] || spokenScripts['hi']
  };
}

// Complete Mock Analysis Payloads for Lab Report Demo
export function getSampleLabReportData(language = 'hi') {
  const languageNames = {
    hi: 'हिंदी (Hindi)',
    en: 'English',
    or: 'ଓଡ଼ିଆ (Odia)',
    bn: 'বাংলা (Bengali)',
    ta: 'தமிழ் (Tamil)',
  };

  const spokenScripts = {
    hi: 'नमस्ते। आपकी लैब रिपोर्ट में 5 मुख्य जांचें शामिल हैं। आपका खाली पेट शुगर 142 और एचबीए1सी 7.6 प्रतिशत है, जो शुगर का स्तर अधिक होना दर्शाता है। आपका हीमोग्लोबिन 10.2 कम है और थायरॉइड टीएसएच 6.8 बढ़ा हुआ है। कृपया इस रिपोर्ट के साथ अपने डॉक्टर से परामर्श अवश्य करें।',
    en: 'Hello. Your diagnostic panel includes 5 key biomarkers. Fasting blood sugar at 142 and HbA1c at 7.6% are both high, indicating elevated glycemic levels. Hemoglobin is low at 10.2, and TSH is elevated at 6.8. Please review these findings with your doctor.',
    or: 'ନମସ୍କାର। ଆପଣଙ୍କ ଲ୍ୟାବ୍ ରିପୋର୍ଟରେ ୫ଟି ପରୀକ୍ଷା ରହିଛି। ଆପଣଙ୍କ ଫାଷ୍ଟିଙ୍ଗ୍ ବ୍ଲଡ୍ ସୁଗାର ୧୪୨ ଏବଂ ଏଚବିଏ୧ସି ୭.୬% ରହିଛି, ଯାହା ମଧୁମେହ ସ୍ତର ବୃଦ୍ଧି ଦର୍ଶାଉଛି। ହିମୋଗ୍ଲୋବିନ୍ ୧୦.୨ କମ ରହିଛି। ଦୟାକରି ତୁରନ୍ତ ଡାକ୍ତରଙ୍କ ସହିତ ପରାମର୍ଶ କରନ୍ତୁ।',
    bn: 'নমস্কার। আপনার ল্যাব রিপোর্টে ৫টি প্রধান পরীক্ষা রয়েছে। আপনার খালি পেটে সুগার ১৪২ এবং এইচবিএওয়ানসি ৭.৬ শতাংশ, যা ডায়াবেটিস বৃদ্ধি নির্দেশ করে। হিমোগ্লোবিন ১০.২ কম এবং থাইরয়েড টিএসএইচ ৬.৮ বেশি রয়েছে। অনুগ্রহ করে আপনার ডাক্তারের সাথে আলোচনা করুন।',
    ta: 'வணக்கம். உங்கள் ஆய்வக அறிக்கையில் 5 சோதனைகள் உள்ளன. வெறும் வயிற்று சர்க்கரை 142 மற்றும் HbA1c 7.6% அதிகமாக உள்ளது, இது சர்க்கரை அளவைக் காட்டுகிறது. ஹீமோகுளோபின் 10.2 குறைவாக உள்ளது மற்றும் தைராய்டு TSH 6.8 அதிகமாக உள்ளது. மருத்துவரிடம் ஆலோசனை பெறவும்.',
  };

  const disclaimers = {
    hi: 'महत्वपूर्ण सुरक्षा सूचना: यह AI व्याख्या केवल आपकी समझ और सुविधा के लिए है। किसी भी दवा, खुराक या जांच रिपोर्ट के संबंध में हमेशा अपने डॉक्टर या योग्य फार्मासिस्ट से परामर्श अवश्य लें।',
    en: 'Important Safety Notice: This AI explanation is strictly for educational comprehension. Always verify prescription medicines, schedules, and lab test results with your treating doctor or registered pharmacist before taking any medication.',
    or: 'ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ ସୁରକ୍ଷା ସୂଚନା: ଏହି AI ବ୍ୟାଖ୍ୟା କେବଳ ଆପଣଙ୍କ ବୁଝିବା ସୁବିଧା ପାଇଁ। କୌଣସି ଔଷଧ ସେବନ ପୂର୍ବରୁ ସର୍ବଦା ଆପଣଙ୍କ ଚିକିତ୍ସକ ଡାକ୍ତର କିମ୍ବା ଫାର୍ମାସିଷ୍ଟଙ୍କ ସହିତ ପରାମର୍ଶ କରନ୍ତୁ।',
    bn: 'জরুরি সুরক্ষা সতর্কতা: এই এআই ব্যাখ্যা শুধুমাত্র আপনার তথ্য এবং স্পষ্ট ধারণার জন্য। ওষুধ সেবন বা যেকোনো পরিবর্তনের পূর্বে সর্বদা আপনার রেজিস্টার্ড ডাক্তার বা ফার্মাসিস্টের পরামর্শ গ্রহণ করুন।',
    ta: 'முக்கிய பாதுகாப்பு அறிவிப்பு: இந்த AI விளக்கம் உங்கள் புரிதலுக்காக மட்டுமே வழங்கப்படுகிறது. எந்தவொரு மருந்தையும் உட்கொள்வதற்கு முன், எப்போதும் உங்கள் மருத்துவர் அல்லது அங்கீகரிக்கப்பட்ட மருந்தாளரிடம் சரிபார்த்துக் கொள்ளுங்கள்.',
  };

  return {
    success: true,
    filename: 'Sample_Thyrocare_Lab_Panel.png',
    language: language,
    quality_metrics: {
      blur_variance: 240.2,
      brightness_score: 215.8,
      is_blurry: false,
      is_too_dark: false,
      is_too_bright: false,
      quality_status: 'good',
      warnings: [],
    },
    dimensions: {
      original_width: 800,
      original_height: 1000,
      processed_width: 800,
      processed_height: 1000,
    },
    preview_base64: SAMPLE_LAB_REPORT_IMAGE,
    raw_extraction: {
      document_type: 'lab_report',
      patient_instructions: [
        'Fasting Blood Sugar and HbA1c both elevated',
        'Correlate thyroid TSH with Free T4',
        'Check iron profile for mild anemia'
      ]
    },
    verification: {
      document_type: 'lab_report',
      patient_instructions: [
        'Fasting Blood Sugar and HbA1c both elevated',
        'Correlate thyroid TSH with Free T4',
        'Check iron profile for mild anemia'
      ],
      total_medicines: 0,
      verified_medicines_count: 0,
      low_confidence_medicines_count: 0,
      flagged_biomarkers_count: 4,
      medicines: [],
      biomarkers: [
        {
          test_name: 'Fasting Blood Sugar (FBS)',
          value: 142.0,
          raw_value_text: '142.0 mg/dL',
          unit: 'mg/dL',
          printed_reference_range: '70.0 - 99.0',
          normalized_test_name: 'Fasting Blood Sugar',
          standard_range: '70.0 - 99.0 mg/dL',
          status: 'high',
          interpretation: 'Elevated fasting blood sugar (> 99 mg/dL). Impaired fasting glucose or diabetes.'
        },
        {
          test_name: 'HbA1c (Glycated Hemoglobin)',
          value: 7.6,
          raw_value_text: '7.6%',
          unit: '%',
          printed_reference_range: '< 5.7',
          normalized_test_name: 'HbA1c',
          standard_range: '4.0 - 5.6 % (Non-diabetic)',
          status: 'high',
          interpretation: 'Elevated HbA1c (≥ 5.7%). Indicates prediabetes or diabetes mellitus.'
        },
        {
          test_name: 'Hemoglobin (Hb)',
          value: 10.2,
          raw_value_text: '10.2 g/dL',
          unit: 'g/dL',
          printed_reference_range: '12.0 - 17.5',
          normalized_test_name: 'Hemoglobin',
          standard_range: '12.0 - 17.5 g/dL',
          status: 'low',
          interpretation: 'Low hemoglobin (< 12.0 g/dL). Indicates anemia.'
        },
        {
          test_name: 'Serum Creatinine',
          value: 1.0,
          raw_value_text: '1.0 mg/dL',
          unit: 'mg/dL',
          printed_reference_range: '0.6 - 1.2',
          normalized_test_name: 'Creatinine',
          standard_range: '0.60 - 1.20 mg/dL',
          status: 'normal',
          interpretation: 'Normal kidney filtration marker.'
        },
        {
          test_name: 'Serum TSH (Thyroid)',
          value: 6.8,
          raw_value_text: '6.8 uIU/mL',
          unit: 'uIU/mL',
          printed_reference_range: '0.4 - 4.5',
          normalized_test_name: 'TSH',
          standard_range: '0.40 - 4.50 uIU/mL',
          status: 'high',
          interpretation: 'Elevated TSH (> 4.50 uIU/mL). Suggests primary hypothyroidism.'
        }
      ],
      drug_interactions: []
    },
    localized_guidance: {
      language: language,
      language_name: languageNames[language] || 'Hindi',
      spoken_summary_script: spokenScripts[language] || spokenScripts['hi'],
      medicine_schedules: [],
      biomarker_explanations: [
        {
          test_name: 'Fasting Blood Sugar (खाली पेट शुगर)',
          value_summary: '142.0 mg/dL (सामान्य मानक: 70 - 99 mg/dL)',
          status_in_plain_language: language === 'hi' ? 'उच्च स्तर (HIGH)' : 'Elevated (HIGH)',
          meaning_and_advice: language === 'hi' ? 'खाली पेट रक्त शर्करा सामान्य से अधिक है। यह डायबिटीज की संभावना का संकेत देता है।' : 'Blood sugar level after overnight fasting is above target.'
        },
        {
          test_name: 'HbA1c (3 महीने का औसत शुगर)',
          value_summary: '7.6% (सामान्य मानक: < 5.7%)',
          status_in_plain_language: language === 'hi' ? 'उच्च स्तर (HIGH)' : 'Elevated (HIGH)',
          meaning_and_advice: language === 'hi' ? 'यह पिछले 90 दिनों का औसत शुगर स्तर दर्शाता है। 7.6% अनियंत्रित शुगर को दर्शाता है।' : 'Reflects 3-month average blood glucose. 7.6% suggests active diabetes.'
        },
        {
          test_name: 'Hemoglobin (रक्त में हीमोग्लोबिन)',
          value_summary: '10.2 g/dL (सामान्य मानक: 12.0 - 17.5 g/dL)',
          status_in_plain_language: language === 'hi' ? 'कम स्तर (LOW)' : 'Below Normal (LOW)',
          meaning_and_advice: language === 'hi' ? 'हीमोग्लोबिन कम होने से खून की कमी (एनीमिया) हो सकती है। थकान या कमजोरी महसूस हो सकती है।' : 'Mild anemia. Patient may experience fatigue or reduced stamina.'
        },
        {
          test_name: 'Serum Creatinine (किडनी स्वास्थ्य मार्कर)',
          value_summary: '1.0 mg/dL (सामान्य मानक: 0.6 - 1.2 mg/dL)',
          status_in_plain_language: language === 'hi' ? 'सामान्य (NORMAL)' : 'Healthy Normal (NORMAL)',
          meaning_and_advice: language === 'hi' ? 'गुर्दे (किडनी) का फिल्ट्रेशन काम सामान्य और स्वस्थ सीमा में है।' : 'Kidneys are effectively filtering metabolic waste.'
        },
        {
          test_name: 'TSH (थायरॉइड उत्तेजक हार्मोन)',
          value_summary: '6.8 uIU/mL (सामान्य मानक: 0.4 - 4.5 uIU/mL)',
          status_in_plain_language: language === 'hi' ? 'उच्च स्तर (HIGH)' : 'Elevated (HIGH)',
          meaning_and_advice: language === 'hi' ? 'थायरॉइड ग्रंथि सुस्त हो सकती है (हाइपोथायरायडिज्म)। वजन बढ़ना या ठंड लगना संभव है।' : 'Indicates underactive thyroid (hypothyroidism). Doctor may advise thyroid supplement.'
        }
      ],
      doctor_questions: [
        'Do I need to start blood sugar medication or insulin based on HbA1c 7.6%?',
        'Should I take an iron supplement for hemoglobin 10.2 g/dL?',
        'Do I need a Free T4 or T3 test for the elevated TSH level?'
      ],
      safety_disclaimer: disclaimers[language] || disclaimers['hi']
    },
    spoken_summary_script: spokenScripts[language] || spokenScripts['hi']
  };
}

