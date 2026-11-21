"""
MedBhasha Evaluation & Safety Benchmark
Evaluates 10 synthetic noisy prescription and diagnostic lab scenarios:
1. Formulary verification accuracy on misspelled/noisy drug names (RapidFuzz WRatio).
2. Hallucination and ambiguity catch rate on non-existent / severely corrupted drug names.
3. Deterministic lab rule classification accuracy (100% pure-Python numeric logic).

Run via:
    python backend/benchmark/run_benchmark.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.schemas import (
    DocumentExtraction,
    ExtractedBiomarker,
    ExtractedMedicine,
)
from backend.services.verifier import (
    check_drug_interactions,
    evaluate_biomarkers,
    load_formulary,
    verify_document_extraction,
    verify_medicines,
)

# 10 Rigorous Test Cases simulating real-world noisy clinic captures
BENCHMARK_CASES: List[Dict[str, Any]] = [
    {
        "id": "TC-01",
        "description": "Faint handwriting with minor spelling typo on antipyretic",
        "type": "medicine",
        "input_med": ExtractedMedicine(
            raw_name="Dolo-650 mg tab",
            dosage="650mg",
            frequency_code="1-0-1",
            morning_count=1.0,
            afternoon_count=0.0,
            night_count=1.0,
            meal_timing="after_food",
            duration_days=5,
            general_purpose="Fever and body pain",
        ),
        "expected_matched_name": "Dolo 650",
        "expected_status": "verified",
        "min_confidence": 85.0,
    },
    {
        "id": "TC-02",
        "description": "Truncated antibiotic brand with missing vowels",
        "type": "medicine",
        "input_med": ExtractedMedicine(
            raw_name="Augmntin 625 Duo",
            dosage="625mg",
            frequency_code="BD",
            morning_count=1.0,
            afternoon_count=0.0,
            night_count=1.0,
            meal_timing="after_food",
            duration_days=7,
            general_purpose="Bacterial chest infection",
        ),
        "expected_matched_name": "Augmentin 625 Duo",
        "expected_status": "verified",
        "min_confidence": 85.0,
    },
    {
        "id": "TC-03",
        "description": "PPI Antacid abbreviation with dosage suffix",
        "type": "medicine",
        "input_med": ExtractedMedicine(
            raw_name="Pan D cap",
            dosage="40mg",
            frequency_code="1-0-0",
            morning_count=1.0,
            afternoon_count=0.0,
            night_count=0.0,
            meal_timing="before_food",
            duration_days=10,
            general_purpose="Gastric acidity and reflux",
        ),
        "expected_matched_name": "Pan",
        "expected_status": "verified",
        "min_confidence": 80.0,
    },
    {
        "id": "TC-04",
        "description": "Metformin generic abbreviation with salt name missing",
        "type": "medicine",
        "input_med": ExtractedMedicine(
            raw_name="Glycomet 500mg",
            dosage="500mg",
            frequency_code="1-0-1",
            morning_count=1.0,
            afternoon_count=0.0,
            night_count=1.0,
            meal_timing="after_food",
            duration_days=30,
            general_purpose="Type-2 Diabetes glycemic control",
        ),
        "expected_matched_name": "Glycomet 500",
        "expected_status": "verified",
        "min_confidence": 85.0,
    },
    {
        "id": "TC-05",
        "description": "Hallucination Catch: Completely non-existent drug name",
        "type": "medicine_adversarial",
        "input_med": ExtractedMedicine(
            raw_name="XyloCure99 MegaMax",
            dosage="100mg",
            frequency_code="1-0-1",
            morning_count=1.0,
            afternoon_count=0.0,
            night_count=1.0,
            meal_timing="unspecified",
            duration_days=5,
            general_purpose="Unknown fictitious compound",
        ),
        "expected_status": "low_confidence",
        "must_catch_hallucination": True,
    },
    {
        "id": "TC-06",
        "description": "Hallucination Catch: Illegible handwriting scribble",
        "type": "medicine_adversarial",
        "input_med": ExtractedMedicine(
            raw_name="ZzzAbcQrt Scribble-Illegible",
            dosage="5mg",
            frequency_code="0-0-1",
            morning_count=0.0,
            afternoon_count=0.0,
            night_count=1.0,
            meal_timing="unspecified",
            duration_days=None,
            general_purpose="Unclear",
        ),
        "expected_status": "low_confidence",
        "must_catch_hallucination": True,
    },
    {
        "id": "TC-07",
        "description": "Biomarker: Severely elevated Fasting Blood Sugar (Diabetes threshold)",
        "type": "biomarker",
        "input_bio": ExtractedBiomarker(
            test_name="Fasting Blood Glucose (FBS)",
            value=142.0,
            raw_value_text="142.0 mg/dL",
            unit="mg/dL",
            printed_reference_range="70 - 99",
        ),
        "expected_status": "high",
        "expected_norm_name": "Fasting Blood Sugar",
    },
    {
        "id": "TC-08",
        "description": "Biomarker: Elevated 3-month glycemic control (HbA1c)",
        "type": "biomarker",
        "input_bio": ExtractedBiomarker(
            test_name="HbA1c Glycated Hemoglobin",
            value=7.6,
            raw_value_text="7.6%",
            unit="%",
            printed_reference_range="< 5.7",
        ),
        "expected_status": "high",
        "expected_norm_name": "HbA1c",
    },
    {
        "id": "TC-09",
        "description": "Biomarker: Anemic low hemoglobin reading",
        "type": "biomarker",
        "input_bio": ExtractedBiomarker(
            test_name="Hemoglobin (Hb)",
            value=10.2,
            raw_value_text="10.2 g/dL",
            unit="g/dL",
            printed_reference_range="12.0 - 17.5",
        ),
        "expected_status": "low",
        "expected_norm_name": "Hemoglobin",
    },
    {
        "id": "TC-10",
        "description": "Biomarker: Thyroid dysfunction (High TSH Hypothyroidism)",
        "type": "biomarker",
        "input_bio": ExtractedBiomarker(
            test_name="Serum TSH (Thyroid Stimulating Hormone)",
            value=6.8,
            raw_value_text="6.8 uIU/mL",
            unit="uIU/mL",
            printed_reference_range="0.4 - 4.5",
        ),
        "expected_status": "high",
        "expected_norm_name": "TSH",
    },
    {
        "id": "TC-11",
        "description": "Clinical DDI: Blood Thinner (Aspirin) + NSAID (Combiflam) severe bleeding risk",
        "type": "ddi",
        "input_meds": [
            ExtractedMedicine(
                raw_name="Ecosprin 75",
                dosage="75mg",
                frequency_code="1-0-0",
                meal_timing="after_food",
                general_purpose="Cardiovascular blood thinner",
            ),
            ExtractedMedicine(
                raw_name="Combiflam tab",
                dosage="400mg",
                frequency_code="1-0-1",
                meal_timing="after_food",
                general_purpose="Severe joint pain relief",
            ),
        ],
        "expected_severity": "danger",
        "expected_alert_type": "drug_interaction",
    },
    {
        "id": "TC-12",
        "description": "Safety Guardrail: Duplicate Paracetamol (Dolo 650 + Combiflam) hepatotoxicity check",
        "type": "ddi",
        "input_meds": [
            ExtractedMedicine(
                raw_name="Dolo 650 mg",
                dosage="650mg",
                frequency_code="1-0-1",
                meal_timing="after_food",
                general_purpose="Fever",
            ),
            ExtractedMedicine(
                raw_name="Combiflam tab",
                dosage="400mg",
                frequency_code="1-0-1",
                meal_timing="after_food",
                general_purpose="Pain",
            ),
        ],
        "expected_severity": "warning",
        "expected_alert_type": "duplicate_ingredient",
    },
]


def run_benchmark_suite() -> Dict[str, Any]:
    start_time = time.time()
    records, names = load_formulary()

    results: List[Dict[str, Any]] = []

    med_tests_passed = 0
    total_med_tests = 0

    hallucination_tests_passed = 0
    total_hallucination_tests = 0

    lab_tests_passed = 0
    total_lab_tests = 0

    ddi_tests_passed = 0
    total_ddi_tests = 0

    for tc in BENCHMARK_CASES:
        tc_id = tc["id"]
        tc_type = tc["type"]

        if tc_type == "medicine":
            total_med_tests += 1
            input_med = tc["input_med"]
            verified = verify_medicines([input_med])[0]

            score = verified.confidence_score
            status = verified.verification_status
            matched = verified.matched_name or ""

            passed = (
                status == tc["expected_status"]
                and score >= tc["min_confidence"]
                and (tc["expected_matched_name"].lower() in matched.lower() or matched.lower() in tc["expected_matched_name"].lower())
            )

            if passed:
                med_tests_passed += 1

            results.append({
                "id": tc_id,
                "category": "Prescription Match",
                "input": input_med.raw_name,
                "output": f"{matched} ({score:.1f}%)",
                "expected": f"{tc['expected_matched_name']} (≥{tc['min_confidence']}%)",
                "verdict": "PASS" if passed else "FAIL",
                "notes": f"Matched generic: {verified.generic_composition}",
            })

        elif tc_type == "medicine_adversarial":
            total_hallucination_tests += 1
            input_med = tc["input_med"]
            verified = verify_medicines([input_med])[0]

            score = verified.confidence_score
            status = verified.verification_status

            # Adversarial test PASSES if the engine correctly flags low_confidence (< 80)
            passed = (status == "low_confidence") and (verified.warning is not None)
            if passed:
                hallucination_tests_passed += 1

            results.append({
                "id": tc_id,
                "category": "Hallucination Defense",
                "input": input_med.raw_name,
                "output": f"Score {score:.1f}% -> {status}",
                "expected": "low_confidence (< 80%)",
                "verdict": "PASS" if passed else "FAIL",
                "notes": "Flagged with pharmacist check warning",
            })

        elif tc_type == "biomarker":
            total_lab_tests += 1
            input_bio = tc["input_bio"]
            evaluated = evaluate_biomarkers([input_bio])[0]

            status = evaluated.status
            norm_name = evaluated.normalized_test_name

            passed = (
                status == tc["expected_status"]
                and norm_name == tc["expected_norm_name"]
            )
            if passed:
                lab_tests_passed += 1

            results.append({
                "id": tc_id,
                "category": "Lab Numeric Rule",
                "input": f"{input_bio.test_name}: {input_bio.raw_value_text}",
                "output": f"{norm_name} -> {status.upper()}",
                "expected": f"{tc['expected_norm_name']} -> {tc['expected_status'].upper()}",
                "verdict": "PASS" if passed else "FAIL",
                "notes": f"Range: {evaluated.standard_range}",
            })

        elif tc_type == "ddi":
            total_ddi_tests += 1
            input_meds = tc["input_meds"]
            verified_meds = verify_medicines(input_meds)
            ddi_alerts = check_drug_interactions(verified_meds)

            match = next((a for a in ddi_alerts if a.alert_type == tc["expected_alert_type"]), None)
            passed = (match is not None) and (match.severity == tc["expected_severity"])
            if passed:
                ddi_tests_passed += 1

            med_names = " + ".join(m.raw_name for m in input_meds)
            alert_desc = f"{match.severity.upper()}: {match.title}" if match else "No Alert"
            results.append({
                "id": tc_id,
                "category": "DDI & Duplicate Guard",
                "input": med_names,
                "output": alert_desc,
                "expected": f"{tc['expected_severity'].upper()} ({tc['expected_alert_type']})",
                "verdict": "PASS" if passed else "FAIL",
                "notes": match.description[:55] + "..." if match else "No safety alert triggered",
            })

    total_passed = med_tests_passed + hallucination_tests_passed + lab_tests_passed + ddi_tests_passed
    total_tests = len(BENCHMARK_CASES)
    elapsed = time.time() - start_time

    # Output Markdown Report
    print("\n" + "=" * 90)
    print("           MEDBHASHA CLINICAL SAFETY & VERIFICATION BENCHMARK REPORT")
    print("=" * 90)
    print(f"Formulary Drug Records Loaded : {len(records)} active Indian pharmaceutical products")
    print(f"Total Benchmark Cases         : {total_tests}")
    print(f"Overall Pass Rate             : {total_passed}/{total_tests} ({(total_passed / total_tests) * 100:.1f}%)")
    print(f"Execution Latency             : {elapsed * 1000:.2f} ms")
    print("=" * 90 + "\n")

    print("| ID | Category | Input Entity | Evaluated Output | Expected Target | Verdict | Details |")
    print("|---|---|---|---|---|:---:|---|")
    for r in results:
        v_icon = "✅ PASS" if r["verdict"] == "PASS" else "❌ FAIL"
        print(f"| {r['id']} | {r['category']} | `{r['input']}` | {r['output']} | {r['expected']} | {v_icon} | {r['notes']} |")

    print("\n### Executive Evaluation Summary:")
    print(f"- **Prescription Typo & Fuzzy Matching Accuracy**: {med_tests_passed}/{total_med_tests} ({(med_tests_passed / total_med_tests) * 100:.1f}%)")
    print(f"- **Hallucination & Ambiguity Defense Catch Rate**: {hallucination_tests_passed}/{total_hallucination_tests} ({(hallucination_tests_passed / total_hallucination_tests) * 100:.1f}%)")
    print(f"- **Deterministic Lab Rule Precision**: {lab_tests_passed}/{total_lab_tests} ({(lab_tests_passed / total_lab_tests) * 100:.1f}%) [100% Rule Consistency - Zero LLM Guesswork]")
    print(f"- **DDI & Active Ingredient Safety Guardrail**: {ddi_tests_passed}/{total_ddi_tests} ({(ddi_tests_passed / total_ddi_tests) * 100:.1f}%) [Critical Drug Interactions & Duplicate Toxicity]")
    print("=" * 90 + "\n")

    return {
        "total_tests": total_tests,
        "total_passed": total_passed,
        "pass_rate_pct": (total_passed / total_tests) * 100,
        "results": results,
    }


if __name__ == "__main__":
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    run_benchmark_suite()
