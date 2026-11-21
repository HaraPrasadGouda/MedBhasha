import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, 
  Upload, 
  AlertTriangle, 
  CheckCircle2, 
  Sparkles, 
  Languages, 
  Eye, 
  Sliders, 
  Activity, 
  ShieldCheck,
  RefreshCw,
  Sun,
  Moon,
  Sunset,
  Camera,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Clock,
  HelpCircle,
  Bookmark,
  Trash2,
  X,
  Check,
  Info,
  ChevronRight,
  ExternalLink,
  Pill,
  FileCheck,
  ArrowRight
} from 'lucide-react';

import { 
  SAMPLE_PRESCRIPTION_IMAGE, 
  SAMPLE_LAB_REPORT_IMAGE,
  getSamplePrescriptionData, 
  getSampleLabReportData 
} from './sampleData.js';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const describeError = (err) => {
  const msg = err?.message || String(err || '');
  if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
    return `Could not reach the MedBhasha backend at ${API_BASE_URL}. Start the FastAPI server (python -m uvicorn backend.main:app) and try again.`;
  }
  return msg;
};

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

const defaultFoodLabel = (mealTiming, language) => {
  const map = {
    before_food: 'Before meals',
    after_food: 'After meals',
    with_food: 'With meals',
    unspecified: 'As directed',
  };
  return map[mealTiming] || 'As directed';
};

const VERNACULAR_LANGUAGES = [
  { code: 'hi', name: 'Hindi', native: 'हिंदी' },
  { code: 'en', name: 'English', native: 'English' },
  { code: 'or', name: 'Odia', native: 'ଓଡ଼ିଆ' },
  { code: 'bn', name: 'Bengali', native: 'বাংলা' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
];

const PROCESSING_STEPS = [
  { id: 1, title: 'Enhancing image contrast', subtitle: 'OpenCV CLAHE & Denoising' },
  { id: 2, title: 'Extracting medical fields', subtitle: 'Gemini 2.5 Flash Structured Vision' },
  { id: 3, title: 'Verifying against drug & lab rules', subtitle: 'RapidFuzz Formulary & Deterministic Rules' },
  { id: 4, title: 'Generating regional guidance', subtitle: 'Vernacular Translation & Edge Neural TTS' },
];

export default function App() {
  const [selectedLanguage, setSelectedLanguage] = useState('hi');
  const [selectedFile, setSelectedFile] = useState(null);
  const [originalPreview, setOriginalPreview] = useState(null);
  const [activeImageTab, setActiveImageTab] = useState('enhanced'); // 'enhanced' | 'original'

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(1);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);
  const [analysisSource, setAnalysisSource] = useState(null);
  const [isRelocalizing, setIsRelocalizing] = useState(false);
  // Audio TTS state
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);
  const audioRef = useRef(null);

  // Offline Saved Scans Drawer state
  const [savedScans, setSavedScans] = useState([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Server health
  const [serverHealth, setServerHealth] = useState({ status: 'checking' });

  // Load saved scans from localStorage on boot
  useEffect(() => {
    try {
      const stored = localStorage.getItem('medbhasha_saved_scans');
      if (stored) {
        setSavedScans(JSON.parse(stored));
      }
    } catch (e) {
      console.warn('Failed to load saved scans from localStorage:', e);
    }
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (res.ok) {
        const data = await res.json();
        setServerHealth({ status: 'online', ...data });
      } else {
        setServerHealth({ status: 'offline' });
      }
    } catch {
      setServerHealth({ status: 'offline' });
    }
  };

  // Save scan to localStorage (strip heavy preview payloads to avoid quota errors)
  const saveScanToLocalStorage = (result, source = 'upload') => {
    try {
      const preview = result?.preview_base64 && result.preview_base64.length <= 250000
        ? result.preview_base64
        : null;
      const { preview_base64, ...rest } = result || {};
      const newEntry = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        title: result?.filename || 'Scanned Document',
        document_type: result?.verification?.document_type || 'prescription',
        language: selectedLanguage,
        source,
        summary: result?.spoken_summary_script || 'Vernacular decoded schedule',
        totalMedicines: result?.verification?.total_medicines || 0,
        flaggedBiomarkers: result?.verification?.flagged_biomarkers_count || 0,
        data: { ...rest, preview_base64: preview },
      };

      setSavedScans((prev) => {
        const updated = [newEntry, ...prev.filter((item) => item.title !== newEntry.title)].slice(0, 10);
        try {
          localStorage.setItem('medbhasha_saved_scans', JSON.stringify(updated));
        } catch (quotaErr) {
          // Trim further on quota errors.
          const trimmed = updated.slice(0, 5);
          try { localStorage.setItem('medbhasha_saved_scans', JSON.stringify(trimmed)); } catch {}
          return trimmed;
        }
        return updated;
      });
    } catch (e) {
      console.warn('Failed to save to localStorage:', e);
    }
  };

  // Process uploaded document with live step progression
  const processUploadedDocument = async (file) => {
    if (!file) return;
    const allowed =
      file.type?.startsWith('image/') || file.type === 'application/pdf';
    if (!allowed) {
      setAnalysisError('Unsupported file type. Please upload an image (JPG/PNG/WEBP) or a PDF.');
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setAnalysisError('File is too large (max 20 MB). Please use a smaller image or PDF.');
      return;
    }

    setAnalysisError(null);
    setSelectedFile(file);
    setIsProcessing(true);
    setProcessingStep(1);
    stopAudio();
    setOriginalPreview(null);
    setAnalysisResult(null);

    if (file.type?.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = () => setOriginalPreview(reader.result);
      reader.readAsDataURL(file);
    }

    try {
      await delay(400);
      setProcessingStep(2);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('language', selectedLanguage);

      const res = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json().catch(() => ({}));

      setProcessingStep(3);
      await delay(300);
      setProcessingStep(4);

      if (!res.ok) {
        throw new Error(data.detail || `Server returned error ${res.status}`);
      }

      setAnalysisResult(data);
      setAnalysisSource('upload');
      saveScanToLocalStorage(data, 'upload');
    } catch (err) {
      console.warn('Backend call failed:', err);
      setAnalysisError(describeError(err));
      setAnalysisResult(null);
    } finally {
      setIsProcessing(false);
    }
  };

  // 1-Click Sample Demo Handlers
  const handleLoadSamplePrescription = async () => {
    setAnalysisError(null);
    setIsProcessing(true);
    setProcessingStep(1);
    stopAudio();
    setSelectedFile({ name: 'Sample_Dr_Sharma_Prescription.png', size: 142000 });
    setOriginalPreview(SAMPLE_PRESCRIPTION_IMAGE);

    for (let step = 1; step <= 4; step++) {
      setProcessingStep(step);
      await delay(400);
    }

    const sample = getSamplePrescriptionData(selectedLanguage);
    setAnalysisResult(sample);
    setAnalysisSource('sample_prescription');
    saveScanToLocalStorage(sample, 'sample_prescription');
    setIsProcessing(false);
  };

  const handleLoadSampleLabReport = async () => {
    setAnalysisError(null);
    setIsProcessing(true);
    setProcessingStep(1);
    stopAudio();
    setSelectedFile({ name: 'Sample_Thyrocare_Lab_Panel.png', size: 184000 });
    setOriginalPreview(SAMPLE_LAB_REPORT_IMAGE);

    for (let step = 1; step <= 4; step++) {
      setProcessingStep(step);
      await delay(400);
    }

    const sample = getSampleLabReportData(selectedLanguage);
    setAnalysisResult(sample);
    setAnalysisSource('sample_lab');
    saveScanToLocalStorage(sample, 'sample_lab');
    setIsProcessing(false);
  };

  // Audio TTS playback handler with window.speechSynthesis fallback
  const handleToggleAudio = async () => {
    if (isPlayingAudio) {
      stopAudio();
      return;
    }

    const textToSpeak = analysisResult?.spoken_summary_script;
    if (!textToSpeak) return;

    setAudioLoading(true);

    try {
      // 1. Try backend Edge Neural TTS
      const res = await fetch(`${API_BASE_URL}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textToSpeak,
          language: selectedLanguage,
        }),
      });

      if (!res.ok) throw new Error('Backend TTS error');

      const blob = await res.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlayingAudio(false);
        URL.revokeObjectURL(audioUrl);
      };
      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        playSpeechSynthesisFallback(textToSpeak);
      };

      await audio.play();
      setIsPlayingAudio(true);
    } catch (err) {
      console.log('Using browser SpeechSynthesis fallback:', err);
      playSpeechSynthesisFallback(textToSpeak);
    } finally {
      setAudioLoading(false);
    }
  };

  const playSpeechSynthesisFallback = (text) => {
    if (!('speechSynthesis' in window)) {
      alert('Audio playback is not supported on this browser.');
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Attempt language matching
    const langMap = { hi: 'hi-IN', bn: 'bn-IN', ta: 'ta-IN', or: 'hi-IN', en: 'en-IN' };
    utterance.lang = langMap[selectedLanguage] || 'hi-IN';
    utterance.rate = 0.95;

    utterance.onstart = () => setIsPlayingAudio(true);
    utterance.onend = () => setIsPlayingAudio(false);
    utterance.onerror = () => setIsPlayingAudio(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlayingAudio(false);
  };

  // Change language dynamically
  const handleLanguageChange = async (langCode) => {
    if (langCode === selectedLanguage) return;
    setSelectedLanguage(langCode);
    stopAudio();
    if (!analysisResult) return;

    if (analysisSource === 'sample_prescription') {
      setAnalysisResult(getSamplePrescriptionData(langCode));
      return;
    }
    if (analysisSource === 'sample_lab') {
      setAnalysisResult(getSampleLabReportData(langCode));
      return;
    }

    // Re-localize a real (uploaded or saved) document on the backend.
    if (!analysisResult.verification) return;
    setIsRelocalizing(true);
    setAnalysisError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/localize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ verification: analysisResult.verification, language: langCode }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `Server returned error ${res.status}`);
      setAnalysisResult((prev) => ({
        ...prev,
        language: langCode,
        localized_guidance: data,
        spoken_summary_script: data.spoken_summary_script,
      }));
    } catch (err) {
      setAnalysisError(describeError(err));
    } finally {
      setIsRelocalizing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      {/* 1. Header with Branding & Language Pills */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 sm:h-20">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="h-11 w-11 rounded-2xl bg-gradient-to-tr from-emerald-700 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-200 font-bold text-2xl">
                मे
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">MedBhasha</h1>
                  <span className="hidden sm:inline-flex items-center text-xs bg-emerald-100 text-emerald-800 font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300">
                    Vernacular AI
                  </span>
                </div>
                <p className="text-xs text-slate-500 hidden sm:block">
                  AI Prescription &amp; Lab Report Decoder for Indian Patients
                </p>
              </div>
            </div>

            {/* Actions: Saved Scans & Connection */}
            <div className="flex items-center gap-2 sm:gap-4">
              <button
                onClick={() => setIsDrawerOpen(true)}
                className="relative inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                title="View Offline Saved Schedules"
              >
                <Bookmark className="h-4 w-4 text-emerald-600" />
                <span className="hidden sm:inline">Saved Scans</span>
                {savedScans.length > 0 && (
                  <span className="bg-emerald-600 text-white text-[11px] font-bold px-1.5 py-0.5 rounded-full">
                    {savedScans.length}
                  </span>
                )}
              </button>

              <div className="hidden md:flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border bg-slate-50 text-slate-600">
                <span className={`h-2 w-2 rounded-full ${serverHealth.status === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'}`} />
                <span className="font-medium">
                  {serverHealth.status === 'online' ? 'FastAPI Connected' : 'Offline Mode'}
                </span>
              </div>
            </div>
          </div>

          {/* High-Contrast Language Selector Pills */}
          <div className="py-2.5 border-t border-slate-100 flex items-center justify-start sm:justify-center gap-2 overflow-x-auto no-scrollbar">
            <span className="text-xs font-bold text-slate-500 flex items-center gap-1.5 shrink-0 mr-1">
              <Languages className="h-3.5 w-3.5 text-emerald-600" /> Language:
            </span>
            {VERNACULAR_LANGUAGES.map((lang) => {
              const isActive = selectedLanguage === lang.code;
              return (
                <button
                  key={lang.code}
                  onClick={() => handleLanguageChange(lang.code)}
                  className={`px-3.5 py-1.5 rounded-full text-xs sm:text-sm font-bold transition-all shrink-0 cursor-pointer ${
                    isActive
                      ? 'bg-emerald-700 text-white shadow-md shadow-emerald-200 ring-2 ring-emerald-500 ring-offset-1'
                      : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-200'
                  }`}
                >
                  {lang.native} <span className="opacity-80 font-normal">({lang.name})</span>
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full space-y-6">
        
        {/* Banner Alert for Vernacular Healthcare */}
        <div className="bg-gradient-to-r from-emerald-800 via-teal-800 to-slate-900 text-white rounded-2xl p-5 sm:p-7 shadow-lg relative overflow-hidden">
          <div className="relative z-10 max-w-2xl">
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-200 border border-emerald-400/30 mb-2">
              <ShieldCheck className="h-3.5 w-3.5" /> 100% Deterministic Rule Engine + Zero Guesswork
            </span>
            <h2 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              Understand Your Prescription in Your Mother Tongue
            </h2>
            <p className="mt-1.5 text-emerald-100 text-xs sm:text-sm leading-relaxed">
              Upload handwritten doctor notes or pathology lab reports. MedBhasha cleans phone camera glare with OpenCV CLAHE, verifies medicines against 150+ Indian formulary drugs, and checks lab values using pure Python numeric rules.
            </p>
          </div>
          <div className="absolute -right-6 -bottom-8 opacity-10 pointer-events-none">
            <Activity className="w-64 h-64 text-white" />
          </div>
        </div>

        {/* 2. Scanner / Upload Zone + 1-Click Sample Demo Buttons */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="font-bold text-slate-900 text-base mb-1 flex items-center gap-2">
            <Camera className="h-5 w-5 text-emerald-600" />
            Scan or Upload Medical Document
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Supports camera photos, JPG, PNG, WEBP, or PDF first page. Images are proportionally scaled to max 1600px width.
          </p>

          {/* Upload Drop Zone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files?.[0];
              if (f) processUploadedDocument(f);
            }}
            onClick={() => document.getElementById('med-file-input')?.click()}
            className="border-2 border-dashed border-slate-300 hover:border-emerald-600 rounded-2xl p-6 sm:p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-slate-50 hover:bg-emerald-50/40 group"
          >
            <div className="h-14 w-14 rounded-2xl bg-emerald-100 flex items-center justify-center text-emerald-700 mb-3 group-hover:scale-105 transition-transform shadow-inner">
              <Upload className="h-7 w-7" />
            </div>
            <p className="text-base font-bold text-slate-800">
              Tap to capture camera photo or browse file
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Handwritten prescription pad, discharge summary, or pathology lab report
            </p>
            <input
              type="file"
              id="med-file-input"
              className="hidden"
              accept="image/*,application/pdf"
              aria-label="Upload medical document"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) processUploadedDocument(f);
                e.target.value = '';
              }}
            />
          </div>

          {/* 1-Click Sample Demo Buttons */}
          <div className="mt-4 pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3">
            <span className="text-xs font-bold text-slate-500 flex items-center gap-1.5 self-start sm:self-center">
              <Sparkles className="h-4 w-4 text-emerald-600" />
              Try with 1-Click Interactive Sample Demos:
            </span>
            <div className="flex flex-wrap gap-2 w-full sm:w-auto">
              <button
                onClick={handleLoadSamplePrescription}
                className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 transition-colors shadow-sm active:scale-95"
              >
                <Pill className="h-4 w-4 text-emerald-600" />
                Load Sample Prescription
              </button>
              <button
                onClick={handleLoadSampleLabReport}
                className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-300 transition-colors shadow-sm active:scale-95"
              >
                <FileCheck className="h-4 w-4 text-teal-600" />
                Load Sample Lab Report
              </button>
            </div>
          </div>
        </div>

        {/* 3. Step-by-Step Processing Indicator */}
        {isProcessing && (
          <div className="bg-white rounded-2xl border border-emerald-200 p-6 shadow-md space-y-4 animate-fade-in">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-600 animate-ping" />
                Processing Medical Document Pipeline
              </span>
              <span className="text-xs font-bold text-slate-500">Step {processingStep} of 4</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              {PROCESSING_STEPS.map((s) => {
                const isComplete = processingStep > s.id;
                const isCurrent = processingStep === s.id;
                return (
                  <div
                    key={s.id}
                    className={`p-3 rounded-xl border transition-all ${
                      isComplete
                        ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                        : isCurrent
                        ? 'bg-teal-50 border-teal-500 text-teal-900 ring-2 ring-teal-400 ring-offset-1'
                        : 'bg-slate-50 border-slate-200 text-slate-400 opacity-60'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      {isComplete ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                      ) : isCurrent ? (
                        <div className="h-4 w-4 border-2 border-teal-600 border-t-transparent rounded-full animate-spin shrink-0" />
                      ) : (
                        <span className="h-4 w-4 rounded-full bg-slate-200 text-slate-600 text-[10px] font-bold flex items-center justify-center shrink-0">
                          {s.id}
                        </span>
                      )}
                      <h4 className="text-xs font-bold truncate">{s.title}</h4>
                    </div>
                    <p className="text-[11px] truncate">{s.subtitle}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Error Banner */}
        {!isProcessing && analysisError && (
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-5 shadow-sm flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <h4 className="font-bold text-rose-800 text-sm mb-0.5">Could not analyze document</h4>
              <p className="text-xs text-rose-700 leading-relaxed break-words">{analysisError}</p>
              <p className="text-[11px] text-rose-600 mt-1.5">
                You can still try the 1-Click Sample Demos below, which run entirely in the browser.
              </p>
            </div>
            <button
              onClick={() => setAnalysisError(null)}
              className="p-1 rounded-lg text-rose-400 hover:text-rose-700"
              aria-label="Dismiss error"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Relocalizing Indicator */}
        {isRelocalizing && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 shadow-sm flex items-center gap-3">
            <div className="h-4 w-4 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin shrink-0" />
            <span className="text-xs font-semibold text-emerald-800">
              Translating guidance to {VERNACULAR_LANGUAGES.find((l) => l.code === selectedLanguage)?.native}...
            </span>
          </div>
        )}

        {/* 4. Verified Results Dashboard */}
        {!isProcessing && analysisResult && (
          <div className="space-y-6">

            {/* A. One-Tap Audio Player Banner */}
            {analysisResult.spoken_summary_script && (
              <div className="bg-gradient-to-r from-emerald-700 to-teal-800 text-white rounded-2xl p-5 sm:p-6 shadow-lg flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <button
                    onClick={handleToggleAudio}
                    disabled={audioLoading}
                    className={`h-14 w-14 rounded-2xl flex items-center justify-center text-emerald-800 bg-white hover:bg-emerald-50 shadow-md transition-all active:scale-95 shrink-0 ${
                      isPlayingAudio ? 'ring-4 ring-emerald-300' : ''
                    }`}
                    title={isPlayingAudio ? 'Pause Spoken Summary' : 'Play Spoken Summary'}
                  >
                    {audioLoading ? (
                      <div className="h-6 w-6 border-[3px] border-emerald-600 border-t-transparent rounded-full animate-spin" />
                    ) : isPlayingAudio ? (
                      <Pause className="h-7 w-7 fill-current" />
                    ) : (
                      <Play className="h-7 w-7 fill-current ml-0.5" />
                    )}
                  </button>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base sm:text-lg font-black">
                        {isPlayingAudio ? 'Speaking in' : 'Listen in'} {VERNACULAR_LANGUAGES.find(l => l.code === selectedLanguage)?.native || 'Selected Language'}
                      </h3>
                      {isPlayingAudio && (
                        <span className="flex items-center gap-1 text-[11px] bg-emerald-500/30 text-emerald-100 px-2 py-0.5 rounded-full border border-emerald-400/40 animate-pulse">
                          <Volume2 className="h-3 w-3" /> Live Audio
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-emerald-100 mt-0.5 line-clamp-2 max-w-2xl">
                      "{analysisResult.spoken_summary_script}"
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={handleToggleAudio}
                    className="px-4 py-2 bg-emerald-900/60 hover:bg-emerald-900/80 rounded-xl text-xs font-bold text-emerald-100 border border-emerald-400/30 transition-colors"
                  >
                    {isPlayingAudio ? 'Pause Speech' : 'Play Audio Summary'}
                  </button>
                </div>
              </div>
            )}

            {/* B. Before/After Image Quality & Preview Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Sliders className="h-5 w-5 text-emerald-600" />
                  <h3 className="font-bold text-slate-900 text-base">Image Enhancement &amp; Quality Check</h3>
                </div>

                {/* Toggle Tabs */}
                <div className="flex bg-slate-100 p-1 rounded-xl text-xs font-bold self-start sm:self-center">
                  <button
                    onClick={() => setActiveImageTab('enhanced')}
                    className={`px-3 py-1.5 rounded-lg transition-all ${
                      activeImageTab === 'enhanced'
                        ? 'bg-white text-emerald-800 shadow-sm'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    OpenCV CLAHE Enhanced
                  </button>
                  <button
                    onClick={() => setActiveImageTab('original')}
                    className={`px-3 py-1.5 rounded-lg transition-all ${
                      activeImageTab === 'original'
                        ? 'bg-white text-emerald-800 shadow-sm'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    Raw Upload
                  </button>
                </div>
              </div>

              {/* Quality Diagnostics Pills */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Sharpness Score</span>
                  <span className="font-black text-slate-800 text-sm">
                    {analysisResult.quality_metrics?.blur_variance ?? '—'}
                  </span>
                  <span className={`text-[10px] block mt-0.5 ${analysisResult.quality_metrics?.is_blurry ? 'text-rose-600' : 'text-emerald-600'}`}>
                    {analysisResult.quality_metrics?.is_blurry ? '⚠ Blurry — retake photo' : '✓ In Sharp Focus'}
                  </span>
                </div>

                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Brightness</span>
                  <span className="font-black text-slate-800 text-sm">
                    {analysisResult.quality_metrics?.brightness_score ?? '—'}{analysisResult.quality_metrics?.brightness_score != null ? ' / 255' : ''}
                  </span>
                  <span className={`text-[10px] block mt-0.5 ${analysisResult.quality_metrics?.is_too_dark || analysisResult.quality_metrics?.is_too_bright ? 'text-amber-600' : 'text-emerald-600'}`}>
                    {analysisResult.quality_metrics?.is_too_dark
                      ? '⚠ Underexposed'
                      : analysisResult.quality_metrics?.is_too_bright
                      ? '⚠ Overexposed'
                      : '✓ Well lit'}
                  </span>
                </div>

                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Verified Medicines</span>
                  <span className="font-black text-emerald-700 text-sm">
                    {analysisResult.verification?.verified_medicines_count || 0} / {analysisResult.verification?.total_medicines || 0}
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">RapidFuzz Matched</span>
                </div>

                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Lab Biomarkers</span>
                  <span className="font-black text-slate-800 text-sm">
                    {analysisResult.verification?.biomarkers?.length || 0} Tested
                  </span>
                  <span className="text-[10px] text-amber-600 block mt-0.5">
                    {analysisResult.verification?.flagged_biomarkers_count || 0} Out-of-Range
                  </span>
                </div>
              </div>

              {/* Quality Warnings */}
              {analysisResult.quality_metrics?.warnings?.length > 0 && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 space-y-1">
                  {analysisResult.quality_metrics.warnings.map((w, i) => (
                    <p key={i} className="flex items-start gap-2">
                      <AlertTriangle className="h-3.5 w-3.5 text-amber-600 shrink-0 mt-0.5" />
                      <span>{w}</span>
                    </p>
                  ))}
                </div>
              )}

              {/* Image Preview Box */}
              <div className="bg-slate-900/5 rounded-xl p-3 flex flex-col items-center justify-center max-h-96 overflow-hidden">
                 {analysisResult.preview_base64 || originalPreview ? (
                  <img
                    src={activeImageTab === 'enhanced' ? (analysisResult.preview_base64 || originalPreview) : (originalPreview || analysisResult.preview_base64)}
                    alt="Medical Document Preview"
                    className="max-h-80 w-auto object-contain rounded-lg shadow-sm border border-slate-200"
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center py-10 text-slate-400">
                    <FileText className="h-12 w-12 mb-2" />
                    <p className="text-xs">Preview unavailable (text-based document)</p>
                  </div>
                )}
                <p className="text-[11px] text-slate-400 mt-2 text-center">
                  {activeImageTab === 'enhanced'
                    ? '✓ Contrast Limited Adaptive Histogram Equalization (CLAHE) & Non-Local Means Denoising'
                    : 'Original camera capture before preprocessing'}
                </p>
              </div>
            </div>

            {/* C. Visual Pill Schedule Cards */}
            {analysisResult.verification?.medicines?.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <Pill className="h-5 w-5 text-emerald-600" />
                    Prescribed Medication Schedule ({analysisResult.verification.medicines.length})
                  </h3>
                  <span className="text-xs bg-emerald-100 text-emerald-800 font-bold px-2.5 py-1 rounded-full">
                    Formulary Verified
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analysisResult.verification.medicines.map((med, idx) => {
                    const isVerified = med.verification_status === 'verified';
                    return (
                      <div
                        key={idx}
                        className={`bg-white rounded-2xl border p-5 shadow-sm space-y-3 transition-all ${
                          isVerified ? 'border-slate-200 hover:border-emerald-300' : 'border-amber-300 bg-amber-50/20'
                        }`}
                      >
                        {/* Title & Status Badge */}
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h4 className="text-base font-bold text-slate-900">
                              {med.matched_name || med.raw_name}
                            </h4>
                            {med.generic_composition && (
                              <p className="text-xs font-semibold text-emerald-700 mt-0.5">
                                Composition: {med.generic_composition}
                              </p>
                            )}
                          </div>

                          <span
                            className={`text-xs font-bold px-2.5 py-1 rounded-full shrink-0 flex items-center gap-1 ${
                              isVerified
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : 'bg-rose-100 text-rose-800 border border-rose-300'
                            }`}
                          >
                            {isVerified ? (
                              <>
                                <Check className="h-3 w-3" /> {med.confidence_score}% Match
                              </>
                            ) : (
                              <>
                                <AlertTriangle className="h-3 w-3" /> Confirm with Chemist
                              </>
                            )}
                          </span>
                        </div>

                        {/* Timing Visual Pills (Morning, Afternoon, Night) */}
                        <div className="grid grid-cols-3 gap-2 pt-1">
                          {/* Morning */}
                          <div className={`p-2.5 rounded-xl text-center border ${med.morning_count > 0 ? 'bg-amber-50 border-amber-200 text-amber-900' : 'bg-slate-50 border-slate-100 text-slate-400'}`}>
                            <div className="flex items-center justify-center gap-1 text-[11px] font-bold mb-0.5">
                              <Sun className={`h-3.5 w-3.5 ${med.morning_count > 0 ? 'text-amber-500' : 'text-slate-300'}`} /> Morning
                            </div>
                            <span className="text-sm font-black">
                              {med.morning_count > 0 ? `${med.morning_count} Tab` : '—'}
                            </span>
                          </div>

                          {/* Afternoon */}
                          <div className={`p-2.5 rounded-xl text-center border ${med.afternoon_count > 0 ? 'bg-orange-50 border-orange-200 text-orange-900' : 'bg-slate-50 border-slate-100 text-slate-400'}`}>
                            <div className="flex items-center justify-center gap-1 text-[11px] font-bold mb-0.5">
                              <Sunset className={`h-3.5 w-3.5 ${med.afternoon_count > 0 ? 'text-orange-500' : 'text-slate-300'}`} /> Afternoon
                            </div>
                            <span className="text-sm font-black">
                              {med.afternoon_count > 0 ? `${med.afternoon_count} Tab` : '—'}
                            </span>
                          </div>

                          {/* Night */}
                          <div className={`p-2.5 rounded-xl text-center border ${med.night_count > 0 ? 'bg-indigo-50 border-indigo-200 text-indigo-900' : 'bg-slate-50 border-slate-100 text-slate-400'}`}>
                            <div className="flex items-center justify-center gap-1 text-[11px] font-bold mb-0.5">
                              <Moon className={`h-3.5 w-3.5 ${med.night_count > 0 ? 'text-indigo-500' : 'text-slate-300'}`} /> Night
                            </div>
                            <span className="text-sm font-black">
                              {med.night_count > 0 ? `${med.night_count} Tab` : '—'}
                            </span>
                          </div>
                        </div>

                        {/* Localized vernacular schedule (if available) */}
                        {(() => {
                          const loc = analysisResult.localized_guidance?.medicine_schedules?.[idx];
                          if (!loc) return null;
                          return (
                            <div className="p-2.5 bg-emerald-50/50 border border-emerald-100 rounded-xl space-y-1">
                              {loc.schedule_text && (
                                <p className="text-xs font-semibold text-emerald-900">{loc.schedule_text}</p>
                              )}
                              {loc.food_instruction && (
                                <p className="text-[11px] text-slate-600">
                                  {loc.food_instruction}
                                </p>
                              )}
                              {loc.special_instructions && (
                                <p className="text-[11px] text-slate-500 italic">{loc.special_instructions}</p>
                              )}
                            </div>
                          );
                        })()}

                        {/* Meal timing badge & Duration */}
                        <div className="flex flex-wrap items-center justify-between text-xs pt-1 border-t border-slate-100 text-slate-600">
                          <span className="inline-flex items-center gap-1 font-semibold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg">
                            <Clock className="h-3 w-3 text-emerald-600" />
                            {med.meal_timing === 'before_food' ? 'Before Meals (खाली पेट)' : med.meal_timing === 'after_food' ? 'After Meals (भोजन के बाद)' : 'With Meals'}
                          </span>
                          {med.duration_days && (
                            <span className="font-bold text-slate-500">
                              Duration: {med.duration_days} Days
                            </span>
                          )}
                        </div>

                        {/* Red warning banner if low confidence */}
                        {!isVerified && (
                          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2">
                            <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
                            <span>{med.warning}</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* D. Lab Biomarker Cards (Deterministic Lab Rule Engine Results) */}
            {analysisResult.verification?.biomarkers?.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <Activity className="h-5 w-5 text-teal-600" />
                    Diagnostic Lab Report Findings ({analysisResult.verification.biomarkers.length})
                  </h3>
                  <span className="text-xs bg-teal-100 text-teal-800 font-bold px-2.5 py-1 rounded-full">
                    Deterministic Clinical Rule Engine
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analysisResult.verification.biomarkers.map((bio, idx) => {
                    const isHigh = bio.status === 'high';
                    const isLow = bio.status === 'low';
                    const isNormal = bio.status === 'normal';

                    return (
                      <div
                        key={idx}
                        className={`bg-white rounded-2xl border p-5 shadow-sm space-y-3 transition-all ${
                          isNormal
                            ? 'border-emerald-200'
                            : isHigh
                            ? 'border-rose-200 bg-rose-50/20'
                            : 'border-amber-200 bg-amber-50/20'
                        }`}
                      >
                        {/* Header: Test Name & Deterministic Status */}
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h4 className="text-base font-bold text-slate-900">
                              {bio.normalized_test_name || bio.test_name}
                            </h4>
                            <span className="text-xs text-slate-400">
                              Standard Range: {bio.standard_range || bio.printed_reference_range || 'N/A'}
                            </span>
                          </div>

                          <span
                            className={`text-xs font-bold px-3 py-1 rounded-full shrink-0 flex items-center gap-1 ${
                              isNormal
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : isHigh
                                ? 'bg-rose-100 text-rose-800 border border-rose-300'
                                : bio.status === 'unverified_range'
                                ? 'bg-slate-100 text-slate-700 border border-slate-300'
                                : 'bg-amber-100 text-amber-800 border border-amber-300'
                            }`}
                          >
                            {isNormal ? '✓ NORMAL' : isHigh ? '▲ HIGH' : isLow ? '▼ LOW' : '— REVIEW'}
                          </span>
                        </div>

                        {/* Numeric Value & Range Bar */}
                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 space-y-2">
                          <div className="flex justify-between items-baseline">
                            <span className="text-xs text-slate-500 font-medium">Measured Value</span>
                            <span className={`text-xl font-black ${isNormal ? 'text-emerald-700' : isHigh ? 'text-rose-700' : 'text-amber-700'}`}>
                              {bio.raw_value_text}
                            </span>
                          </div>

                          {/* Visual 3-segment Reference Range Bar */}
                          <div className="space-y-1">
                            <div className="h-2 w-full bg-slate-200 rounded-full flex overflow-hidden">
                              <div className="w-1/4 bg-amber-400 opacity-80" title="Low Zone" />
                              <div className="w-2/4 bg-emerald-500" title="Normal Target Zone" />
                              <div className="w-1/4 bg-rose-500 opacity-80" title="High Zone" />
                            </div>
                            <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                              <span>Low</span>
                              <span className="font-bold text-emerald-700">Healthy Interval</span>
                              <span>High</span>
                            </div>
                          </div>
                        </div>

                        {/* Plain Language Interpretation */}
                        <p className="text-xs text-slate-700 leading-relaxed bg-slate-50/60 p-2.5 rounded-lg border border-slate-100">
                          <Info className="h-3.5 w-3.5 text-teal-600 inline mr-1 -mt-0.5" />
                          {analysisResult.localized_guidance?.biomarker_explanations?.[idx]?.meaning_and_advice || bio.interpretation}
                        </p>
                        {analysisResult.localized_guidance?.biomarker_explanations?.[idx]?.status_in_plain_language && (
                          <p className="text-[11px] text-teal-700 font-semibold">
                            {analysisResult.localized_guidance.biomarker_explanations[idx].status_in_plain_language}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* E. Suggested Questions to Ask Your Doctor */}
            {analysisResult.localized_guidance?.doctor_questions?.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
                <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                  <HelpCircle className="h-5 w-5 text-emerald-600" />
                  Suggested Questions to Ask Your Doctor
                </h3>
                <p className="text-xs text-slate-500">
                  Take these patient-friendly questions to your next appointment or pharmacy visit:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                  {analysisResult.localized_guidance.doctor_questions.map((q, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-emerald-50/50 border border-emerald-100 rounded-xl text-xs font-semibold text-slate-700 flex items-start gap-2"
                    >
                      <span className="h-5 w-5 rounded-full bg-emerald-200 text-emerald-800 text-xs font-bold flex items-center justify-center shrink-0">
                        {idx + 1}
                      </span>
                      <span>{q}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* F. Mandatory Vernacular Safety Disclaimer */}
            {analysisResult.localized_guidance?.safety_disclaimer && (
              <div className="p-4 bg-slate-100 border border-slate-200 rounded-2xl text-xs text-slate-600 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <h5 className="font-bold text-slate-800 mb-0.5">Mandatory Medical Disclaimer</h5>
                  <p className="leading-relaxed">{analysisResult.localized_guidance.safety_disclaimer}</p>
                </div>
              </div>
            )}

          </div>
        )}

      </main>

      {/* 5. Offline Saved Schedules Slide-Over Drawer */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-sm transition-opacity animate-fade-in">
          <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col p-6 overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-4">
              <div className="flex items-center gap-2">
                <Bookmark className="h-5 w-5 text-emerald-600" />
                <h3 className="font-bold text-slate-900 text-base">Offline Saved Scans</h3>
              </div>
              <button
                onClick={() => setIsDrawerOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
              <span>{savedScans.length} Scans Available Offline</span>
              {savedScans.length > 0 && (
                <button
                  onClick={() => {
                    localStorage.removeItem('medbhasha_saved_scans');
                    setSavedScans([]);
                  }}
                  className="text-rose-600 hover:underline flex items-center gap-1"
                >
                  <Trash2 className="h-3 w-3" /> Clear History
                </button>
              )}
            </div>

            {savedScans.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-400">
                <Bookmark className="h-12 w-12 text-slate-200 mb-2" />
                <p className="font-semibold text-slate-600 text-sm">No Saved Scans Yet</p>
                <p className="text-xs mt-1">Uploaded or demo reports are automatically cached locally so you can review them offline.</p>
              </div>
            ) : (
              <div className="space-y-3 flex-1 overflow-y-auto">
                {savedScans.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => {
                      setAnalysisResult(item.data);
                      setSelectedLanguage(item.language || 'hi');
                      setAnalysisSource(item.source || 'upload');
                      setOriginalPreview(item.data?.preview_base64 || null);
                      setIsDrawerOpen(false);
                    }}
                    className="p-4 rounded-xl border border-slate-200 hover:border-emerald-500 bg-slate-50 hover:bg-emerald-50/20 cursor-pointer transition-all space-y-2 group"
                  >
                    <div className="flex items-start justify-between">
                      <h4 className="font-bold text-sm text-slate-800 group-hover:text-emerald-800 truncate max-w-[240px]">
                        {item.title}
                      </h4>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                        Available Offline
                      </span>
                    </div>

                    <p className="text-xs text-slate-500 line-clamp-2">
                      {item.summary}
                    </p>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-100">
                      <span>{new Date(item.timestamp).toLocaleDateString()}</span>
                      <span className="font-semibold text-emerald-700 flex items-center gap-1">
                        Open Report <ChevronRight className="h-3 w-3" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-slate-400">
          MedBhasha • Vernacular AI Medical Literacy Engine • Empowering Indian Patients
        </div>
      </footer>
    </div>
  );
}
