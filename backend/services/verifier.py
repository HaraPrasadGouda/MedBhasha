"""
MedBhasha Deterministic Verifier & Clinical Rule Engine
1. Medicine Verification: Fuzzy matching with RapidFuzz against the Indian Formulary (indian_medicines.csv).
2. Lab Rule Engine: Strict pure-Python numeric threshold evaluations against biological reference intervals.
"""

from __future__ import annotations

import csv
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import rapidfuzz
from rapidfuzz import fuzz, process

from backend.schemas import (
    DocumentExtraction,
    DrugInteractionAlert,
    EvaluatedBiomarker,
    ExtractedBiomarker,
    ExtractedMedicine,
    VerifiedDocumentResult,
    VerifiedMedicine,
)

logger = logging.getLogger("medbhasha.verifier")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "indian_medicines.csv"

# Global cache for formulary database
_FORMULARY_CACHE: Optional[List[Dict[str, str]]] = None
_FORMULARY_NAMES: Optional[List[str]] = None


def load_formulary() -> Tuple[List[Dict[str, str]], List[str]]:
    """Loads and caches the Indian medicines CSV database into memory."""
    global _FORMULARY_CACHE, _FORMULARY_NAMES
    if _FORMULARY_CACHE is not None and _FORMULARY_NAMES is not None:
        return _FORMULARY_CACHE, _FORMULARY_NAMES

    records: List[Dict[str, str]] = []
    names: List[str] = []

    if not CSV_PATH.exists():
        logger.error(f"Formulary CSV not found at {CSV_PATH}")
        return records, names

    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                "brand_or_generic_name": row.get("brand_or_generic_name", "").strip(),
                "generic_composition": row.get("generic_composition", "").strip(),
                "category": row.get("category", "").strip(),
            })
            names.append(row.get("brand_or_generic_name", "").strip())

    _FORMULARY_CACHE = records
    _FORMULARY_NAMES = names
    return _FORMULARY_CACHE, _FORMULARY_NAMES


# ============================================================================
# 1. RapidFuzz Medicine Verification Engine
# ============================================================================

def verify_medicines(medicines: List[ExtractedMedicine]) -> List[VerifiedMedicine]:
    """
    Fuzzy-matches extracted prescription medicine names against the Indian Formulary.
    If confidence_score >= 80, marks verification_status = 'verified'.
    If confidence_score < 80, marks verification_status = 'low_confidence' and attaches a warning.
    """
    records, names = load_formulary()
    verified_list: List[VerifiedMedicine] = []

    if not records or not names:
        for med in medicines:
            verified_list.append(
                VerifiedMedicine(
                    **med.model_dump(),
                    matched_name=None,
                    generic_composition=None,
                    category=None,
                    confidence_score=0.0,
                    verification_status="low_confidence",
                    warning="Formulary database unavailable for verification.",
                )
            )
        return verified_list

    for med in medicines:
        raw_query = med.raw_name.strip()
        dosage = (med.dosage or "").strip()

        def _clean(text: str) -> str:
            text = re.sub(r"(?i)\b(tab|tabs|tablet|cap|caps|capsule|syp|syrup|syr|inj|injection|oint|drops|susp|suspension)\.?\b", " ", text)
            text = re.sub(r"[-_/]+", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text

        candidates = []
        for q in (raw_query, _clean(raw_query)):
            if q and q not in candidates:
                candidates.append(q)
        if dosage and dosage.lower() not in ("unspecified", ""):
            for q in (raw_query, _clean(raw_query)):
                combo = f"{q} {dosage}".strip()
                if combo not in candidates:
                    candidates.append(combo)
                combo2 = f"{q} {re.sub(r'[^0-9.]', '', dosage)}".strip()
                if combo2 not in candidates and re.search(r"\d", combo2):
                    candidates.append(combo2)

        def _shared_token(a: str, b: str) -> bool:
            ta = set(re.findall(r"[A-Za-z]{3,}", (a or "").lower()))
            tb = set(re.findall(r"[A-Za-z]{3,}", (b or "").lower()))
            return bool(ta & tb)

        best_match = None
        for q in candidates:
            m = process.extractOne(q, names, scorer=fuzz.WRatio)
            if not m:
                continue
            # Guard against dosage-driven false positives: a candidate that only
            # matches because of a shared numeric token (e.g. '100') must share
            # an alphabetic token with the original drug name.
            is_combo = q not in (raw_query, _clean(raw_query))
            if is_combo and not _shared_token(raw_query, m[0]):
                continue
            if best_match is None or m[1] > best_match[1]:
                best_match = m
        if best_match:
            best_match_name, score, index = best_match
            matched_record = records[index]
            score_rounded = round(float(score), 1)

            if score_rounded >= 80.0:
                v_status = "verified"
                warning = None
            else:
                v_status = "low_confidence"
                warning = "Low handwriting/match confidence — confirm with pharmacist before taking"

            verified_list.append(
                VerifiedMedicine(
                    **med.model_dump(),
                    matched_name=matched_record["brand_or_generic_name"],
                    generic_composition=matched_record["generic_composition"],
                    category=matched_record["category"],
                    confidence_score=score_rounded,
                    verification_status=v_status,
                    warning=warning,
                )
            )
        else:
            verified_list.append(
                VerifiedMedicine(
                    **med.model_dump(),
                    matched_name=None,
                    generic_composition=None,
                    category=None,
                    confidence_score=0.0,
                    verification_status="low_confidence",
                    warning="Low handwriting/match confidence — confirm with pharmacist before taking",
                )
            )

    return verified_list


# ============================================================================
# 2. Deterministic Clinical Lab Rule Engine
# ============================================================================

LAB_REFERENCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "HbA1c": {
        "unit": "%",
        "low_cutoff": 4.0,
        "high_cutoff": 5.7,  # > 5.7 is elevated (prediabetes: 5.7-6.4, diabetes >= 6.5)
        "range_str": "4.0 - 5.6 % (Non-diabetic)",
        "interp_low": "Below expected baseline (< 4.0%).",
        "interp_normal": "Normal non-diabetic range (< 5.7%). Good 3-month glycemic control.",
        "interp_high": "Elevated HbA1c (≥ 5.7%). Indicates prediabetes or diabetes mellitus.",
    },
    "Fasting Blood Sugar": {
        "unit": "mg/dL",
        "low_cutoff": 70.0,
        "high_cutoff": 99.0,  # 70 - 99 normal; 100-125 impaired; >= 126 diabetes
        "range_str": "70.0 - 99.0 mg/dL",
        "interp_low": "Hypoglycemia (< 70 mg/dL). Risk of dizziness/weakness.",
        "interp_normal": "Normal fasting blood sugar level.",
        "interp_high": "Elevated fasting blood sugar (> 99 mg/dL). Impaired fasting glucose or diabetes.",
    },
    "Postprandial Blood Sugar": {
        "unit": "mg/dL",
        "low_cutoff": 70.0,
        "high_cutoff": 140.0,  # < 140 normal; 140-199 impaired; >= 200 diabetes
        "range_str": "70.0 - 140.0 mg/dL",
        "interp_low": "Low postprandial glucose (< 70 mg/dL).",
        "interp_normal": "Normal post-meal glycemic response (< 140 mg/dL).",
        "interp_high": "Elevated post-meal blood sugar (> 140 mg/dL). Postprandial hyperglycemia.",
    },
    "Hemoglobin": {
        "unit": "g/dL",
        "low_cutoff": 12.0,
        "high_cutoff": 17.5,
        "range_str": "12.0 - 17.5 g/dL",
        "interp_low": "Low hemoglobin (< 12.0 g/dL). Indicates anemia.",
        "interp_normal": "Optimal hemoglobin level within standard healthy range.",
        "interp_high": "Elevated hemoglobin (> 17.5 g/dL). May indicate polycythemia or dehydration.",
    },
    "TSH": {
        "unit": "uIU/mL",
        "low_cutoff": 0.4,
        "high_cutoff": 4.5,
        "range_str": "0.40 - 4.50 uIU/mL",
        "interp_low": "Suppressed TSH (< 0.40 uIU/mL). Suggests hyperthyroidism.",
        "interp_normal": "Euthyroid (normal thyroid stimulating hormone).",
        "interp_high": "Elevated TSH (> 4.50 uIU/mL). Suggests primary hypothyroidism.",
    },
    "SGOT": {
        "unit": "U/L",
        "low_cutoff": 5.0,
        "high_cutoff": 40.0,
        "range_str": "5.0 - 40.0 U/L",
        "interp_low": "Low AST/SGOT level.",
        "interp_normal": "Normal liver enzyme (AST/SGOT) level.",
        "interp_high": "Elevated SGOT (> 40 U/L). Potential liver or cardiac tissue strain.",
    },
    "SGPT": {
        "unit": "U/L",
        "low_cutoff": 7.0,
        "high_cutoff": 56.0,
        "range_str": "7.0 - 56.0 U/L",
        "interp_low": "Low ALT/SGPT level.",
        "interp_normal": "Normal liver enzyme (ALT/SGPT) level.",
        "interp_high": "Elevated SGPT (> 56 U/L). Indicates hepatic inflammation or fatty liver changes.",
    },
    "Creatinine": {
        "unit": "mg/dL",
        "low_cutoff": 0.6,
        "high_cutoff": 1.2,
        "range_str": "0.60 - 1.20 mg/dL",
        "interp_low": "Low serum creatinine (< 0.60 mg/dL).",
        "interp_normal": "Normal kidney filtration marker.",
        "interp_high": "Elevated creatinine (> 1.20 mg/dL). Indicates reduced renal clearance / kidney strain.",
    },
    "Total Cholesterol": {
        "unit": "mg/dL",
        "low_cutoff": 100.0,
        "high_cutoff": 200.0,
        "range_str": "< 200.0 mg/dL (Desirable)",
        "interp_low": "Hypocholesterolemia (< 100 mg/dL).",
        "interp_normal": "Desirable total cholesterol level (< 200 mg/dL).",
        "interp_high": "Borderline high or elevated cholesterol (≥ 200 mg/dL). Hypercholesterolemia.",
    },
    "LDL": {
        "unit": "mg/dL",
        "low_cutoff": 50.0,
        "high_cutoff": 100.0,
        "range_str": "< 100.0 mg/dL (Optimal)",
        "interp_low": "Very low LDL level.",
        "interp_normal": "Optimal low-density lipoprotein (LDL) cholesterol.",
        "interp_high": "Elevated bad cholesterol (LDL ≥ 100 mg/dL). Increased cardiovascular risk.",
    },
    "HDL": {
        "unit": "mg/dL",
        "low_cutoff": 40.0,
        "high_cutoff": 100.0,
        "range_str": "> 40.0 mg/dL (Protective)",
        "interp_low": "Low good cholesterol (HDL < 40 mg/dL). Reduced cardioprotection.",
        "interp_normal": "Protective high-density lipoprotein (HDL) cholesterol level.",
        "interp_high": "Elevated HDL (> 100 mg/dL).",
    },
    "Triglycerides": {
        "unit": "mg/dL",
        "low_cutoff": 50.0,
        "high_cutoff": 150.0,
        "range_str": "< 150.0 mg/dL (Normal)",
        "interp_low": "Low serum triglycerides.",
        "interp_normal": "Normal serum triglyceride level.",
        "interp_high": "Elevated triglycerides (≥ 150 mg/dL). Hypertriglyceridemia.",
    },
    "Vitamin D": {
        "unit": "ng/mL",
        "low_cutoff": 30.0,
        "high_cutoff": 100.0,
        "range_str": "30.0 - 100.0 ng/mL",
        "interp_low": "Vitamin D insufficiency or deficiency (< 30 ng/mL).",
        "interp_normal": "Sufficient 25-hydroxy vitamin D level.",
        "interp_high": "Excessive vitamin D level (> 100 ng/mL).",
    },
    "Vitamin B12": {
        "unit": "pg/mL",
        "low_cutoff": 200.0,
        "high_cutoff": 900.0,
        "range_str": "200.0 - 900.0 pg/mL",
        "interp_low": "Vitamin B12 deficiency (< 200 pg/mL). Risk of neuropathy and fatigue.",
        "interp_normal": "Normal serum vitamin B12 concentration.",
        "interp_high": "Elevated serum vitamin B12 (> 900 pg/mL).",
    },
    "Platelet Count": {
        "unit": "cells/cumm",
        "low_cutoff": 150000.0,
        "high_cutoff": 450000.0,
        "range_str": "150,000 - 450,000 /cumm",
        "interp_low": "Thrombocytopenia (low platelets < 150,000/cumm). Bleeding precaution.",
        "interp_normal": "Platelet count within normal physiological limits.",
        "interp_high": "Thrombocytosis (high platelets > 450,000/cumm).",
    },
    "WBC": {
        "unit": "cells/cumm",
        "low_cutoff": 4000.0,
        "high_cutoff": 11000.0,
        "range_str": "4,000 - 11,000 /cumm",
        "interp_low": "Leukopenia (low WBC < 4,000/cumm). Immunological vulnerability.",
        "interp_normal": "Total leukocyte count (TLC) within normal limits.",
        "interp_high": "Leukocytosis (elevated WBC > 11,000/cumm). Suggests active infection or inflammation.",
    },
}

TEST_ALIASES: Dict[str, str] = {
    # HbA1c
    "hba1c": "HbA1c",
    "hb a1c": "HbA1c",
    "a1c": "HbA1c",
    "glycated hemoglobin": "HbA1c",
    "glycosylated hemoglobin": "HbA1c",
    "hemoglobin a1c": "HbA1c",
    # Fasting Blood Sugar
    "fbs": "Fasting Blood Sugar",
    "fasting blood sugar": "Fasting Blood Sugar",
    "fasting glucose": "Fasting Blood Sugar",
    "fasting blood glucose": "Fasting Blood Sugar",
    "blood sugar fasting": "Fasting Blood Sugar",
    "glucose fasting": "Fasting Blood Sugar",
    # Postprandial Blood Sugar
    "ppbs": "Postprandial Blood Sugar",
    "postprandial blood sugar": "Postprandial Blood Sugar",
    "post prandial blood sugar": "Postprandial Blood Sugar",
    "pp blood sugar": "Postprandial Blood Sugar",
    "post prandial glucose": "Postprandial Blood Sugar",
    "glucose post prandial": "Postprandial Blood Sugar",
    # Hemoglobin
    "hemoglobin": "Hemoglobin",
    "hb": "Hemoglobin",
    "hgb": "Hemoglobin",
    "haemoglobin": "Hemoglobin",
    # TSH
    "tsh": "TSH",
    "thyroid stimulating hormone": "TSH",
    "s.tsh": "TSH",
    "serum tsh": "TSH",
    "tsh ultrasensitive": "TSH",
    # SGOT
    "sgot": "SGOT",
    "ast": "SGOT",
    "aspartate aminotransferase": "SGOT",
    "sgot / ast": "SGOT",
    "aspartate transaminase": "SGOT",
    # SGPT
    "sgpt": "SGPT",
    "alt": "SGPT",
    "alanine aminotransferase": "SGPT",
    "sgpt / alt": "SGPT",
    "alanine transaminase": "SGPT",
    # Creatinine
    "creatinine": "Creatinine",
    "serum creatinine": "Creatinine",
    "s.creatinine": "Creatinine",
    "s creatinine": "Creatinine",
    # Total Cholesterol
    "total cholesterol": "Total Cholesterol",
    "cholesterol": "Total Cholesterol",
    "s.cholesterol": "Total Cholesterol",
    "serum cholesterol": "Total Cholesterol",
    # LDL
    "ldl": "LDL",
    "ldl cholesterol": "LDL",
    "low density lipoprotein": "LDL",
    "ldl-c": "LDL",
    # HDL
    "hdl": "HDL",
    "hdl cholesterol": "HDL",
    "high density lipoprotein": "HDL",
    "hdl-c": "HDL",
    # Triglycerides
    "triglycerides": "Triglycerides",
    "serum triglycerides": "Triglycerides",
    "s.triglycerides": "Triglycerides",
    "tgl": "Triglycerides",
    # Vitamin D
    "vitamin d": "Vitamin D",
    "vitamin d3": "Vitamin D",
    "25-oh vitamin d": "Vitamin D",
    "25-hydroxy vitamin d": "Vitamin D",
    "vit d": "Vitamin D",
    "vit d3": "Vitamin D",
    # Vitamin B12
    "vitamin b12": "Vitamin B12",
    "vit b12": "Vitamin B12",
    "b12": "Vitamin B12",
    "cobalamin": "Vitamin B12",
    "cyanocobalamin": "Vitamin B12",
    # Platelet Count
    "platelet count": "Platelet Count",
    "platelets": "Platelet Count",
    "total platelet count": "Platelet Count",
    "plt": "Platelet Count",
    # WBC
    "wbc": "WBC",
    "total leukocyte count": "WBC",
    "tlc": "WBC",
    "white blood cells": "WBC",
    "wbc count": "WBC",
    "total wbc count": "WBC",
}


def normalize_test_name(raw_name: str) -> Optional[str]:
    """Resolves raw lab test name or acronym to a canonical registered test name."""
    import re as _re

    clean = _re.sub(r"[^a-z0-9]+", " ", (raw_name or "").lower()).strip()
    clean = _re.sub(r"\s+", " ", clean)

    if clean in TEST_ALIASES:
        return TEST_ALIASES[clean]

    # Prefer the longest matching alias to avoid partial collisions (e.g. 'hdl' vs 'ldl').
    best_alias = None
    for alias in TEST_ALIASES:
        norm_alias = _re.sub(r"\s+", " ", alias)
        if _re.search(r"(?<![a-z0-9])" + _re.escape(norm_alias) + r"(?![a-z0-9])", clean):
            if best_alias is None or len(norm_alias) > len(best_alias):
                best_alias = norm_alias
    if best_alias is not None:
        return TEST_ALIASES[best_alias]

    return None


def evaluate_biomarkers(biomarkers: List[ExtractedBiomarker]) -> List[EvaluatedBiomarker]:
    """
    Evaluates lab biomarker values strictly using pure Python numeric comparisons (<, >).
    Never permits the LLM to hallucinate or invent high/low clinical determinations.
    """
    evaluated_list: List[EvaluatedBiomarker] = []

    for bio in biomarkers:
        canonical_name = normalize_test_name(bio.test_name)

        if not canonical_name or canonical_name not in LAB_REFERENCE_REGISTRY or bio.value is None:
            evaluated_list.append(
                EvaluatedBiomarker(
                    **bio.model_dump(),
                    normalized_test_name=canonical_name or bio.test_name,
                    standard_range=bio.printed_reference_range,
                    status="unverified_range",
                    interpretation="Reference range not in standard registry; refer to printed report interval.",
                )
            )
            continue

        ref = LAB_REFERENCE_REGISTRY[canonical_name]
        val = float(bio.value)
        low_cut = ref["low_cutoff"]
        high_cut = ref["high_cutoff"]

        if val < low_cut:
            status = "low"
            interpretation = ref["interp_low"]
        elif val > high_cut:
            status = "high"
            interpretation = ref["interp_high"]
        else:
            status = "normal"
            interpretation = ref["interp_normal"]

        evaluated_list.append(
            EvaluatedBiomarker(
                **bio.model_dump(),
                normalized_test_name=canonical_name,
                standard_range=ref["range_str"],
                status=status,
                interpretation=interpretation,
            )
        )

    return evaluated_list


# ============================================================================
# 3. Drug-Drug Interaction (DDI) & Active Ingredient Duplicate Safety Engine
# ============================================================================

def check_drug_interactions(medicines: List[VerifiedMedicine]) -> List[DrugInteractionAlert]:
    """
    Evaluates verified medications for clinical safety interactions:
    1. Dangerous Drug-Drug Interactions (e.g. Blood Thinner + NSAID).
    2. Active Ingredient Duplication (e.g. accidental Paracetamol toxicity from multi-brand intake).
    3. Renal & Cardioprotective Alerts (e.g. ACEi/ARB + NSAID, Omeprazole + Clopidogrel).
    """
    alerts: List[DrugInteractionAlert] = []
    if not medicines:
        return alerts

    # Helper to check text matches in brand or generic
    def has_any(med: VerifiedMedicine, keywords: List[str]) -> bool:
        haystack = f"{med.matched_name or ''} {med.raw_name or ''} {med.generic_composition or ''}".lower()
        return any(re.search(rf"\b{re.escape(k.lower())}\b", haystack) for k in keywords)

    # 1. Check for Duplicate Paracetamol / Acetaminophen (Hepatotoxicity Guardrail)
    paracetamol_meds: List[str] = []
    for med in medicines:
        if has_any(med, ["paracetamol", "acetaminophen", "dolo", "crocin", "calpol", "combiflam", "sumo", "pyricool"]):
            label = med.matched_name or med.raw_name
            if label not in paracetamol_meds:
                paracetamol_meds.append(label)

    if len(paracetamol_meds) >= 2:
        alerts.append(
            DrugInteractionAlert(
                severity="warning",
                alert_type="duplicate_ingredient",
                medicines_involved=paracetamol_meds,
                title="Accidental Overdose Warning: Duplicate Paracetamol (Acetaminophen)",
                description=(
                    f"Multiple prescribed medicines ({', '.join(paracetamol_meds)}) contain Paracetamol. "
                    "Cumulative daily intake exceeding 2000-4000 mg can cause acute drug-induced liver injury."
                ),
                action_recommendation="Confirm the combined daily dosage with your pharmacist before taking both products together.",
            )
        )

    # 2. Blood Thinner (Antiplatelet / Anticoagulant) + NSAID (Bleeding Hazard)
    thinners = ["aspirin", "ecosprin", "clopidogrel", "warfarin", "apixaban", "rivaroxaban", "dabigatran", "prasugrel", "ticagrelor"]
    nsaids = ["ibuprofen", "combiflam", "diclofenac", "aceclofenac", "naproxen", "ketorolac", "piroxicam", "nimesulide", "mefenamic", "etoricoxib"]

    thinner_matches = [m.matched_name or m.raw_name for m in medicines if has_any(m, thinners)]
    nsaid_matches = [m.matched_name or m.raw_name for m in medicines if has_any(m, nsaids)]

    if thinner_matches and nsaid_matches:
        alerts.append(
            DrugInteractionAlert(
                severity="danger",
                alert_type="drug_interaction",
                medicines_involved=list(set(thinner_matches + nsaid_matches)),
                title="Critical Bleeding Risk: Blood Thinner + NSAID Painkiller",
                description=(
                    f"Taking blood thinners ({', '.join(thinner_matches)}) together with NSAID painkillers "
                    f"({', '.join(nsaid_matches)}) sharply elevates the risk of stomach ulcers and internal bleeding."
                ),
                action_recommendation="Consult your prescribing doctor immediately. Plain Paracetamol is usually recommended as a safer analgesic on blood thinners.",
            )
        )

    # 3. ACE Inhibitor / ARB + NSAID (Renal Triple Whammy / Kidney Risk)
    ace_arbs = ["telmisartan", "losartan", "olmesartan", "valsartan", "ramipril", "enalapril", "lisinopril"]
    ace_arb_matches = [m.matched_name or m.raw_name for m in medicines if has_any(m, ace_arbs)]

    if ace_arb_matches and nsaid_matches:
        alerts.append(
            DrugInteractionAlert(
                severity="warning",
                alert_type="drug_interaction",
                medicines_involved=list(set(ace_arb_matches + nsaid_matches)),
                title="Kidney Strain Warning: Blood Pressure Medicine (ACEi/ARB) + NSAID",
                description=(
                    f"Combining blood pressure medicines ({', '.join(ace_arb_matches)}) with NSAIDs "
                    f"({', '.join(nsaid_matches)}) can reduce kidney filtration and blunt blood pressure control."
                ),
                action_recommendation="Limit NSAID painkiller use to minimum effective duration and monitor blood pressure and hydration.",
            )
        )

    # 4. Omeprazole / Esomeprazole + Clopidogrel (CYP2C19 Inhibition)
    omeprazole_matches = [m.matched_name or m.raw_name for m in medicines if has_any(m, ["omeprazole", "esomeprazole"])]
    clopidogrel_matches = [m.matched_name or m.raw_name for m in medicines if has_any(m, ["clopidogrel", "clopilet", "plavix"])]

    if omeprazole_matches and clopidogrel_matches:
        alerts.append(
            DrugInteractionAlert(
                severity="warning",
                alert_type="drug_interaction",
                medicines_involved=list(set(omeprazole_matches + clopidogrel_matches)),
                title="Efficacy Reduction Alert: Omeprazole + Clopidogrel",
                description=(
                    "Omeprazole inhibits the liver CYP2C19 enzyme needed to activate Clopidogrel, potentially lowering its blood-thinning protection."
                ),
                action_recommendation="Ask your doctor or pharmacist if switching to Pantoprazole (which does not inhibit CYP2C19) is appropriate.",
            )
        )

    # 5. Dual Antidiabetic Hypoglycemia Vigilance
    secretagogues = ["glimepiride", "gliclazide", "glibenclamide", "glipizide", "amaryl"]
    insulin_terms = ["insulin", "lantus", "humalog", "novorapid", "mixtard"]
    sec_matches = [m.matched_name or m.raw_name for m in medicines if has_any(m, secretagogues)]
    ins_matches = [m.matched_name or m.raw_name for m in medicines if has_any(m, insulin_terms)]

    if (sec_matches and ins_matches) or len(sec_matches) >= 2:
        alerts.append(
            DrugInteractionAlert(
                severity="warning",
                alert_type="drug_interaction",
                medicines_involved=list(set(sec_matches + ins_matches)),
                title="Hypoglycemia (Low Blood Sugar) Vigilance Alert",
                description=(
                    f"Combining potent insulin secretagogues ({', '.join(sec_matches + ins_matches)}) "
                    "significantly increases the frequency of acute hypoglycemia (dizziness, sweating, tremors)."
                ),
                action_recommendation="Keep glucose tablets or sweet fruit juice handy and never skip meals while on this medication regimen.",
            )
        )

    return alerts


# ============================================================================
# 4. Dosing Safety Guardrail (Daily-Dose Limit & Duplicate Active Salt)
# ============================================================================

# Conservative maximum recommended daily dose (in mg) for common oral actives.
# Applied ONLY when the prescription strength is explicitly numeric in mg, so
# combination products and unspecified strengths are never falsely flagged.
MAX_DAILY_DOSE_MG: Dict[str, float] = {
    "paracetamol": 4000.0,
    "acetaminophen": 4000.0,
    "ibuprofen": 2400.0,
    "diclofenac": 150.0,
    "aceclofenac": 200.0,
    "naproxen": 1000.0,
    "aspirin": 4000.0,
    "nimesulide": 200.0,
    "mefenamic": 1000.0,
    "etoricoxib": 120.0,
}

# Active salts that are dangerous to duplicate across brands. Paracetamol is
# intentionally excluded here because the dedicated brand-keyword guardrail in
# check_drug_interactions() already covers every paracetamol product via its
# generic composition, avoiding a duplicate alert for the same pair.
DUPLICATE_ACTIVE_KEYWORDS: List[str] = [
    "ibuprofen", "aspirin", "diclofenac", "aceclofenac", "naproxen",
    "nimesulide", "metformin", "glimepiride", "gliclazide", "glibenclamide",
    "telmisartan", "amlodipine", "atorvastatin", "pantoprazole", "domperidone",
    "omeprazole", "levothyroxine", "thyroxine",
]


def _parse_strength_mg(dosage: str) -> Optional[float]:
    """Parses a numeric strength in milligrams from a dosage string."""
    if not dosage:
        return None
    text = str(dosage).strip().lower().replace(" ", "")
    match = re.match(r"^(\d+(?:\.\d+)?)mg$", text)
    if match:
        return float(match.group(1))
    match = re.match(r"^(\d+(?:\.\d+)?)$", text)
    if match:
        return float(match.group(1))
    return None


def _actives_in_text(text: str, keywords: List[str]) -> List[str]:
    """Returns recognized active salts mentioned in a drug name/composition."""
    if not text:
        return []
    low = text.lower()
    return [
        active
        for active in keywords
        if re.search(r"(?<![a-z])" + re.escape(active) + r"(?![a-z])", low)
    ]


def check_dosing_safety(medicines: List[VerifiedMedicine]) -> List[DrugInteractionAlert]:
    """
    Deterministic dosing guardrails:
    1. Maximum daily dose exceedance for common actives (hepatotoxicity / NSAID burden).
    2. Duplicate active salt across different brands (accidental double dosing).
    3. Implausibly high per-dose tablet counts (likely handwriting misread).
    """
    alerts: List[DrugInteractionAlert] = []
    if not medicines:
        return alerts

    # 1. Maximum daily dose evaluation
    for med in medicines:
        composition = med.generic_composition or ""
        name_text = f"{med.matched_name or ''} {med.raw_name or ''}"
        dose_keywords = list(MAX_DAILY_DOSE_MG.keys())
        actives = _actives_in_text(composition, dose_keywords) or _actives_in_text(name_text, dose_keywords)
        strength = _parse_strength_mg(med.dosage)
        daily_count = (med.morning_count or 0) + (med.afternoon_count or 0) + (med.night_count or 0)
        if not actives or strength is None or daily_count <= 0:
            continue
        daily_dose = strength * daily_count
        for active in actives:
            limit = MAX_DAILY_DOSE_MG.get(active)
            if limit and daily_dose > limit:
                alerts.append(
                    DrugInteractionAlert(
                        severity="danger",
                        alert_type="clinical_caution",
                        medicines_involved=[med.matched_name or med.raw_name],
                        title=(
                            f"Maximum Daily Dose Exceeded: {active.title()} "
                            f"(~{daily_dose:.0f} mg/day)"
                        ),
                        description=(
                            f"{med.matched_name or med.raw_name} provides about {daily_dose:.0f} mg of "
                            f"{active.title()} per day, above the commonly recommended maximum of "
                            f"{limit:.0f} mg/day. Excess dosing increases the risk of liver, kidney, or "
                            "gastrointestinal toxicity."
                        ),
                        action_recommendation=(
                            "Do not take this dose without explicit confirmation from your prescribing "
                            "doctor or pharmacist."
                        ),
                    )
                )
                break

    # 2. Duplicate active salt across different brands
    seen_actives: Dict[str, List[str]] = {}
    for med in medicines:
        composition = med.generic_composition or ""
        label = med.matched_name or med.raw_name
        for active in _actives_in_text(composition, DUPLICATE_ACTIVE_KEYWORDS):
            bucket = seen_actives.setdefault(active, [])
            if label not in bucket:
                bucket.append(label)
    for active, labels in seen_actives.items():
        if len(labels) >= 2:
            alerts.append(
                DrugInteractionAlert(
                    severity="warning",
                    alert_type="duplicate_ingredient",
                    medicines_involved=labels,
                    title=f"Duplicate Active Salt: {active.title()} prescribed twice",
                    description=(
                        f"Two or more prescribed products ({', '.join(labels)}) contain {active.title()}. "
                        "Taking them together can unintentionally double the dose and increase toxicity risk."
                    ),
                    action_recommendation=(
                        "Ask your pharmacist whether both products are required, or whether one should be stopped."
                    ),
                )
            )

    # 3. Implausibly high per-dose tablet count
    for med in medicines:
        counts = [med.morning_count or 0, med.afternoon_count or 0, med.night_count or 0]
        if any(count > 4 for count in counts):
            alerts.append(
                DrugInteractionAlert(
                    severity="warning",
                    alert_type="clinical_caution",
                    medicines_involved=[med.matched_name or med.raw_name],
                    title=f"Unusually High Per-Dose Count: {med.matched_name or med.raw_name}",
                    description=(
                        f"A single dose lists {max(counts):.0f} units, which is atypical for this medicine. "
                        "This may be a misread of the prescription handwriting."
                    ),
                    action_recommendation=(
                        "Confirm the exact number of tablets per dose with your pharmacist before taking it."
                    ),
                )
            )

    return alerts


def _dedupe_alerts(alerts: List[DrugInteractionAlert]) -> List[DrugInteractionAlert]:
    """Removes exact duplicate alerts while preserving severity ordering."""
    seen = set()
    deduped: List[DrugInteractionAlert] = []
    for alert in alerts:
        key = (alert.alert_type, alert.severity, alert.title, tuple(sorted(set(alert.medicines_involved))))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(alert)
    return deduped


def verify_document_extraction(extraction: DocumentExtraction) -> VerifiedDocumentResult:
    """
    Executes the hybrid verification pipeline on extracted medical document data:
    1. Verifies medicines against the Indian Formulary via RapidFuzz.
    2. Deterministically evaluates lab biomarkers via pure Python numeric logic.
    3. Checks for dangerous Drug-Drug Interactions and duplicate active ingredients.
    4. Applies dosing guardrails (daily-dose limits, duplicate salts, per-dose counts).
    5. Produces audit metrics and clinical safety warnings.
    """
    verified_meds = verify_medicines(extraction.medicines)
    evaluated_bios = evaluate_biomarkers(extraction.biomarkers)
    ddi_alerts = _dedupe_alerts(
        check_drug_interactions(verified_meds) + check_dosing_safety(verified_meds)
    )

    total_meds = len(verified_meds)
    verified_count = sum(1 for m in verified_meds if m.verification_status == "verified")
    low_conf_count = sum(1 for m in verified_meds if m.verification_status == "low_confidence")
    flagged_bios = sum(1 for b in evaluated_bios if b.status in ("low", "high"))

    return VerifiedDocumentResult(
        document_type=extraction.document_type,
        patient_instructions=extraction.patient_instructions,
        medicines=verified_meds,
        biomarkers=evaluated_bios,
        total_medicines=total_meds,
        verified_medicines_count=verified_count,
        low_confidence_medicines_count=low_conf_count,
        flagged_biomarkers_count=flagged_bios,
        drug_interactions=ddi_alerts,
    )
