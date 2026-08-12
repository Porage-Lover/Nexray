"""
Clinical prompt templates for HealthGPT-Pro.
Provides structured, narrative, and combined prompt generation as well as output parsing.
"""
import re
from typing import Dict, List, Tuple


MODALITIES = [
    "X-ray", "MRI", "CT Scan", "Fundus Photography", "Dermoscopy",
    "Ultrasound", "Mammography", "PET Scan"
]


def build_structured_prompt(modality: str, clinical_context: str = "", patient_info: str = "") -> str:
    """
    Builds a detailed clinical prompt that instructs the model to output a structured report.

    Args:
        modality: The imaging modality (e.g., "X-ray", "MRI").
        clinical_context: Optional clinical context provided by the clinician.
        patient_info: Optional patient information string.

    Returns:
        A formatted prompt string for structured clinical analysis.
    """
    prompt = (
        f"You are a board-certified radiologist assistant AI analyzing a medical image. "
        f"Modality: {modality}\n"
    )
    if patient_info:
        prompt += f"Patient Information: {patient_info}\n"
    if clinical_context:
        prompt += f"Clinical Context: {clinical_context}\n"

    prompt += (
        "\nAnalyze the provided image thoroughly but concisely. "
        "Produce your output in the following EXACT format, including the exact section headers:\n\n"
        "## FINDINGS\n"
        "[List each finding with confidence score 0-100%]\n\n"
        "## DIFFERENTIAL DIAGNOSIS\n"
        "[Ranked list with severity: CRITICAL/HIGH/MODERATE/LOW]\n\n"
        "## RECOMMENDED ACTIONS\n"
        "[Numbered list of follow-up recommendations]\n\n"
        "## CLINICAL NOTES\n"
        "[Additional observations and context]"
    )
    return prompt


def build_narrative_prompt(modality: str, clinical_context: str = "", patient_info: str = "") -> str:
    """
    Builds a prompt for free-form radiologist-style dictation.

    Args:
        modality: The imaging modality (e.g., "X-ray", "MRI").
        clinical_context: Optional clinical context provided by the clinician.
        patient_info: Optional patient information string.

    Returns:
        A formatted prompt string for narrative clinical dictation.
    """
    prompt = (
        f"You are a board-certified radiologist dictating a clinical narrative for a {modality} study. "
    )
    if patient_info:
        prompt += f"\nPatient Information: {patient_info}"
    if clinical_context:
        prompt += f"\nClinical Context: {clinical_context}"

    prompt += (
        "\n\nWrite a natural language clinical narrative exactly as a professional radiologist "
        "would dictate a report. Be precise, professional, and thorough."
    )
    return prompt


def build_combined_prompt(modality: str, clinical_context: str = "", patient_info: str = "") -> str:
    """
    Combines both structured and narrative prompts into a single prompt.

    The model should output the structured report FIRST, then a separator line '---',
    then the free-form narrative dictation. This allows a single inference call
    to produce both outputs.

    Args:
        modality: The imaging modality (e.g., "X-ray", "MRI").
        clinical_context: Optional clinical context provided by the clinician.
        patient_info: Optional patient information string.

    Returns:
        A combined prompt string for both structured and narrative output.
    """
    structured_part = build_structured_prompt(modality, clinical_context, patient_info)
    prompt = structured_part + (
        "\n\nAfter outputting the structured report exactly as specified above, "
        "add a separator line consisting exactly of '---'.\n"
        "Following the separator, write a free-form natural language clinical narrative "
        "dictation exactly as a professional radiologist would dictate it, based on the same findings."
    )
    return prompt


def parse_model_output(raw_output: str) -> Dict[str, str]:
    """
    Parses the raw model output into a dictionary with extracted sections.

    Splits the output into structured sections (Findings, Differential Diagnosis,
    Recommended Actions, Clinical Notes) and a free-form narrative using regex.

    Args:
        raw_output: The raw text output from HealthGPT-Pro.

    Returns:
        A dictionary with keys: findings, differential_diagnosis, recommended_actions,
        clinical_notes, narrative, and raw.
    """
    result = {
        "findings": "",
        "differential_diagnosis": "",
        "recommended_actions": "",
        "clinical_notes": "",
        "narrative": "",
        "raw": raw_output,
    }

    # Split into structured and narrative parts if combined
    parts = raw_output.split("---")
    structured_text = parts[0]
    narrative_text = parts[1].strip() if len(parts) > 1 else ""

    result["narrative"] = narrative_text

    # Extract sections using regex
    findings_match = re.search(
        r"## FINDINGS\s*(.*?)(?=## DIFFERENTIAL DIAGNOSIS|## RECOMMENDED ACTIONS|## CLINICAL NOTES|$)",
        structured_text,
        re.IGNORECASE | re.DOTALL,
    )
    if findings_match:
        result["findings"] = findings_match.group(1).strip()

    diff_diag_match = re.search(
        r"## DIFFERENTIAL DIAGNOSIS\s*(.*?)(?=## RECOMMENDED ACTIONS|## CLINICAL NOTES|$)",
        structured_text,
        re.IGNORECASE | re.DOTALL,
    )
    if diff_diag_match:
        result["differential_diagnosis"] = diff_diag_match.group(1).strip()

    rec_actions_match = re.search(
        r"## RECOMMENDED ACTIONS\s*(.*?)(?=## CLINICAL NOTES|$)",
        structured_text,
        re.IGNORECASE | re.DOTALL,
    )
    if rec_actions_match:
        result["recommended_actions"] = rec_actions_match.group(1).strip()

    clin_notes_match = re.search(
        r"## CLINICAL NOTES\s*(.*?)$",
        structured_text,
        re.IGNORECASE | re.DOTALL,
    )
    if clin_notes_match:
        result["clinical_notes"] = clin_notes_match.group(1).strip()

    return result


def parse_diagnosis_items(raw_text: str) -> List[Tuple[str, str]]:
    """
    Parses the differential diagnosis text into individual items with severity badges.

    Extracts severity labels (CRITICAL, HIGH, MODERATE, LOW) and the associated
    diagnosis text. Returns a list of (severity, diagnosis_text) tuples.

    Args:
        raw_text: Raw text from the differential_diagnosis section.

    Returns:
        A list of (severity, text) tuples. Severity is one of:
        'CRITICAL', 'HIGH', 'MODERATE', 'LOW', or 'LOW' as default.
    """
    if not raw_text:
        return []

    items = []
    lines = raw_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove list markers (-, *, 1., etc.)
        line = re.sub(r"^[\-\*•]\s*", "", line)
        line = re.sub(r"^\d+[\.\)]\s*", "", line)
        if not line:
            continue

        # Extract severity
        severity = "LOW"
        severity_match = re.search(
            r"\b(CRITICAL|HIGH|MODERATE|LOW)\b", line, re.IGNORECASE
        )
        if severity_match:
            severity = severity_match.group(1).upper()

        # Clean the text — remove severity label artifacts
        clean_text = re.sub(
            r"\s*[\(\[]*\s*(CRITICAL|HIGH|MODERATE|LOW)\s*[\)\]]*\s*[:\-–—]*\s*",
            " ",
            line,
            flags=re.IGNORECASE,
        ).strip()
        # Remove leading/trailing separators
        clean_text = re.sub(r"^[\-–—:]+\s*", "", clean_text).strip()

        if clean_text:
            items.append((severity, clean_text))

    return items


def format_list_items(raw_text: str) -> List[str]:
    """
    Splits raw text into clean list items for rendering.

    Handles bullet points (-, *, •), numbered lists (1., 2)), and plain lines.

    Args:
        raw_text: Raw text with potential list formatting.

    Returns:
        A list of cleaned text strings, one per item.
    """
    if not raw_text:
        return []

    items = []
    lines = raw_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove list markers
        line = re.sub(r"^[\-\*•]\s*", "", line)
        line = re.sub(r"^\d+[\.\)]\s*", "", line)
        line = line.strip()
        if line:
            items.append(line)

    return items
