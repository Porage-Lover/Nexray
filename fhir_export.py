"""
FHIR R4 DiagnosticReport export for Nexray.
Generates HL7 FHIR-compliant JSON without external dependencies.
"""
import json
import uuid
import datetime
from typing import Dict, Optional


def generate_fhir_json(
    patient_id: str,
    patient_name: str,
    modality: str,
    clinical_context: str,
    report_data: Dict[str, str],
    inference_time: float = 0.0,
    token_count: int = 0,
) -> str:
    """
    Formats clinical findings into HL7 FHIR R4 DiagnosticReport JSON.

    Args:
        patient_id: Patient identifier.
        patient_name: Patient name.
        modality: Imaging modality.
        clinical_context: Clinical context.
        report_data: Dict with findings, differential_diagnosis, etc.
        inference_time: Inference time in seconds.
        token_count: Token count.

    Returns:
        Pretty-printed FHIR R4 JSON string.
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report_id = str(uuid.uuid4())
    patient_ref_id = str(uuid.uuid4())

    # Map modality to LOINC code
    modality_loinc = {
        "X-ray": {"code": "36643-5", "display": "XR Radiology"},
        "CT Scan": {"code": "24727-0", "display": "CT Radiology"},
        "MRI": {"code": "24590-2", "display": "MR Radiology"},
        "Ultrasound": {"code": "55111-9", "display": "US Radiology"},
        "Mammography": {"code": "24606-6", "display": "MG Radiology"},
        "Fundus Photography": {"code": "79890-9", "display": "Ophthalmology"},
        "Dermoscopy": {"code": "76498-4", "display": "Dermatology"},
        "PET Scan": {"code": "44136-0", "display": "PET Radiology"},
    }
    loinc = modality_loinc.get(modality, {"code": "18748-4", "display": "Diagnostic imaging study"})

    # Build conclusion from findings
    findings = report_data.get("findings", "")
    diff_dx = report_data.get("differential_diagnosis", "")
    actions = report_data.get("recommended_actions", "")
    notes = report_data.get("clinical_notes", "")
    narrative = report_data.get("narrative", "")

    conclusion_parts = []
    if findings:
        conclusion_parts.append(f"FINDINGS: {findings}")
    if diff_dx:
        conclusion_parts.append(f"DIFFERENTIAL DIAGNOSIS: {diff_dx}")
    if actions:
        conclusion_parts.append(f"RECOMMENDED ACTIONS: {actions}")
    if notes:
        conclusion_parts.append(f"CLINICAL NOTES: {notes}")
    conclusion = "\n\n".join(conclusion_parts)

    # Split patient name
    name_parts = patient_name.split() if patient_name and patient_name != "N/A" else ["Unknown"]
    family = name_parts[-1] if len(name_parts) > 1 else name_parts[0]
    given = name_parts[:-1] if len(name_parts) > 1 else []

    fhir_bundle = {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "document",
        "timestamp": now,
        "entry": [
            {
                "fullUrl": f"urn:uuid:{report_id}",
                "resource": {
                    "resourceType": "DiagnosticReport",
                    "id": report_id,
                    "meta": {
                        "profile": ["http://hl7.org/fhir/StructureDefinition/DiagnosticReport"]
                    },
                    "status": "preliminary",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                                    "code": "RAD",
                                    "display": "Radiology",
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": loinc["code"],
                                "display": loinc["display"],
                            }
                        ],
                        "text": f"{modality} Diagnostic Report",
                    },
                    "subject": {"reference": f"Patient/{patient_ref_id}"},
                    "effectiveDateTime": now,
                    "issued": now,
                    "performer": [
                        {
                            "display": "Nexray Sovereign Clinical AI",
                            "type": "Organization",
                        }
                    ],
                    "conclusion": conclusion,
                    "conclusionCode": [],
                    "presentedForm": [
                        {
                            "contentType": "text/plain",
                            "data": None,
                            "title": "AI-Generated Narrative",
                        }
                    ]
                    if narrative
                    else [],
                    "extension": [
                        {
                            "url": "http://nexray.ai/fhir/StructureDefinition/ai-metadata",
                            "extension": [
                                {
                                    "url": "engine",
                                    "valueString": "HealthGPT-Pro-8B (MLX 4-bit)",
                                },
                                {
                                    "url": "inferenceTimeSeconds",
                                    "valueDecimal": round(inference_time, 2),
                                },
                                {
                                    "url": "tokenCount",
                                    "valueInteger": token_count,
                                },
                                {
                                    "url": "executionMode",
                                    "valueString": "offline-sovereign",
                                },
                            ],
                        }
                    ],
                },
            },
            {
                "fullUrl": f"urn:uuid:{patient_ref_id}",
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_ref_id,
                    "identifier": [
                        {
                            "system": "http://nexray.ai/patient-id",
                            "value": patient_id if patient_id and patient_id != "N/A" else "UNKNOWN",
                        }
                    ],
                    "name": [
                        {
                            "use": "official",
                            "family": family,
                            "given": given,
                        }
                    ],
                },
            },
        ],
    }

    return json.dumps(fhir_bundle, indent=2, ensure_ascii=False)
