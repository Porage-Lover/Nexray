"""
NexRay — Advanced Diagnostic Imaging & Reporting
A fully offline medical image analysis system powered by HealthGPT-Pro-8B
running locally on Apple Silicon via MLX.

Entry point: streamlit run app.py
"""
import os
import re
import tempfile
import datetime
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageDraw
import streamlit as st

from styles import macos_hig_css
from prompts import (
    MODALITIES,
    build_combined_prompt,
    parse_model_output,
    parse_diagnosis_items,
    format_list_items,
)
from engine import get_model, analyze_image, chat_followup, get_memory_usage
import json
from database import init_database, save_report, get_all_reports, clear_all_reports
from pdf_export import generate_pdf
from fhir_export import generate_fhir_json
from rag import load_guidelines, retrieve_context


# ── Page Configuration ──────────────────────────────────────
st.set_page_config(
    page_title="NexRay — Diagnostic Imaging",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Custom CSS ───────────────────────────────────────
st.markdown(macos_hig_css, unsafe_allow_html=True)

# ── Constants ───────────────────────────────────────────────
DB_PATH = "./data/reports.db"

# ── Initialize Database ────────────────────────────────────
init_database(DB_PATH)

# ── Initialize Clinical RAG ────────────────────────────────
@st.cache_resource
def get_rag_retriever():
    """Loads and indexes clinical guidelines once per session."""
    return load_guidelines()

rag_retriever = get_rag_retriever()

# ── Session State ───────────────────────────────────────────
defaults = {
    "report_data": None,
    "raw_response": None,
    "inference_time": 0.0,
    "token_count": 0,
    "image_path": None,
    "report_saved": False,
    "chat_history": [],
    "show_bbox": False,
    "img_brightness": 1.0,
    "img_contrast": 1.0,
    "img_invert": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Helper: Apply image adjustments ─────────────────────────
def apply_image_adjustments(img: Image.Image) -> Image.Image:
    """Applies brightness, contrast, and inversion adjustments to the image."""
    adjusted = img.copy()
    if adjusted.mode != "RGB":
        adjusted = adjusted.convert("RGB")

    if st.session_state.img_invert:
        adjusted = ImageOps.invert(adjusted)

    if st.session_state.img_brightness != 1.0:
        enhancer = ImageEnhance.Brightness(adjusted)
        adjusted = enhancer.enhance(st.session_state.img_brightness)

    if st.session_state.img_contrast != 1.0:
        enhancer = ImageEnhance.Contrast(adjusted)
        adjusted = enhancer.enhance(st.session_state.img_contrast)

    return adjusted


def draw_roi_overlay(img: Image.Image) -> Image.Image:
    """Draws a semi-transparent ROI bounding box on the center-right region."""
    overlay = img.copy()
    if overlay.mode != "RGBA":
        overlay = overlay.convert("RGBA")

    w, h = overlay.size
    # Focus on center-right region (common anomaly zone for wrist/chest)
    x1, y1 = int(w * 0.3), int(h * 0.25)
    x2, y2 = int(w * 0.75), int(h * 0.75)

    # Create semi-transparent overlay
    roi_layer = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(roi_layer)

    # Draw filled semi-transparent rectangle
    draw.rectangle([x1, y1, x2, y2], fill=(0, 212, 170, 25), outline=(0, 212, 170, 180), width=2)

    # Draw corner markers
    corner_len = min(w, h) // 12
    corner_color = (0, 212, 170, 220)
    # Top-left
    draw.line([(x1, y1), (x1 + corner_len, y1)], fill=corner_color, width=3)
    draw.line([(x1, y1), (x1, y1 + corner_len)], fill=corner_color, width=3)
    # Top-right
    draw.line([(x2, y1), (x2 - corner_len, y1)], fill=corner_color, width=3)
    draw.line([(x2, y1), (x2, y1 + corner_len)], fill=corner_color, width=3)
    # Bottom-left
    draw.line([(x1, y2), (x1 + corner_len, y2)], fill=corner_color, width=3)
    draw.line([(x1, y2), (x1, y2 - corner_len)], fill=corner_color, width=3)
    # Bottom-right
    draw.line([(x2, y2), (x2 - corner_len, y2)], fill=corner_color, width=3)
    draw.line([(x2, y2), (x2, y2 - corner_len)], fill=corner_color, width=3)

    # Label
    draw.text((x1 + 6, y1 + 6), "ROI", fill=(0, 212, 170, 200))

    result = Image.alpha_composite(overlay, roi_layer)
    return result.convert("RGB")


def render_severity_badge(severity: str) -> str:
    """Returns HTML for a severity pill badge."""
    css_class = f"badge-{severity.lower()}"
    return f'<span class="{css_class}">{severity}</span>'


def render_findings_html(raw_text: str) -> str:
    """Renders findings as styled list items."""
    items = format_list_items(raw_text)
    if not items:
        return f'<p style="color:#c8c8c8; line-height:1.7;">{raw_text}</p>'
    html = ""
    for item in items:
        html += f'<div class="finding-item">{item}</div>'
    return html


def render_diagnosis_html(raw_text: str) -> str:
    """Renders differential diagnoses with severity badges."""
    items = parse_diagnosis_items(raw_text)
    if not items:
        return f'<p style="color:#c8c8c8; line-height:1.7;">{raw_text}</p>'
    html = ""
    for severity, text in items:
        badge = render_severity_badge(severity)
        html += f'<div class="diagnosis-item">{badge}<span class="diagnosis-text">{text}</span></div>'
    return html


def render_actions_html(raw_text: str) -> str:
    """Renders recommended actions as a numbered list."""
    items = format_list_items(raw_text)
    if not items:
        return f'<p style="color:#c8c8c8; line-height:1.7;">{raw_text}</p>'
    html = ""
    for i, item in enumerate(items, 1):
        html += (
            f'<div class="finding-item">'
            f'<span style="color:#00d4aa; font-weight:600; margin-right:6px;">{i}.</span>'
            f'{item}</div>'
        )
    return html


# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    # Logo / Branding
    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="logo-text">🏥 NexRay</div>
            <div class="logo-sub">Sovereign Clinical AI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Status indicator
    st.markdown(
        '',
        unsafe_allow_html=True,
    )

    st.markdown("### Imaging Configuration")

    # Modality selection
    modality = st.selectbox(
        "Modality",
        MODALITIES,
        index=0,
        help="Select the type of medical imaging study.",
    )

    st.markdown("### Patient Information")

    # Patient fields
    patient_id = st.text_input(
        "Patient ID",
        placeholder="e.g., PAT-2026-00142",
    )
    patient_name = st.text_input(
        "Patient Name",
        placeholder="e.g., Jane Doe",
    )

    st.markdown("### Clinical Context")

    # Clinical context
    clinical_context = st.text_area(
        "Notes",
        placeholder="e.g., 65-year-old female, persistent cough for 3 weeks, no fever...",
        height=100,
    )

    st.markdown("### Upload Study")

    # File uploader
    uploaded_file = st.file_uploader(
        "Medical Image",
        type=["png", "jpg", "jpeg", "bmp", "tiff", "dcm"],
        help="Upload a medical image for analysis.",
    )

    st.markdown("---")

    # Analyze button
    analyze_clicked = False
    st.markdown('<div class="analyze-btn">', unsafe_allow_html=True)
    if st.button("⚡  Analyze Image", width="stretch"):
        analyze_clicked = True
    st.markdown("</div>", unsafe_allow_html=True)

    # Report History
    st.markdown("---")
    st.markdown("### Report History")
    past_reports = get_all_reports(DB_PATH)
    
    if past_reports:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All", width="stretch"):
                clear_all_reports(DB_PATH)
                st.rerun()
        with col2:
            st.download_button(
                label="📥 Export JSON",
                data=json.dumps(past_reports, indent=2),
                file_name="hack4health_reports_export.json",
                mime="application/json",
                width="stretch",
            )

        st.markdown(
            f'<p style="color:#555; font-size:0.8rem; margin-top: 0.5rem;">{len(past_reports)} report(s) saved</p>',
            unsafe_allow_html=True,
        )
        for r in past_reports[:5]:
            created = r.get("created_at", "")[:16].replace("T", " ")
            report_hash = r.get("report_hash", "")
            hash_display = f"{report_hash[:4]}…{report_hash[-4:]}" if report_hash and len(report_hash) >= 8 else "—"
            st.markdown(
                f'<p style="color:#888; font-size:0.78rem; margin:2px 0;">'
                f'📋 {r.get("modality", "—")} · {r.get("patient_name", "N/A")[:15]} · {created}'
                f'</p>'
                f'<p style="color:#555; font-size:0.68rem; margin:0 0 6px 0; font-family: monospace;">'
                f'🔐 Hash: {hash_display}'
                f'</p>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<p style="color:#444; font-size:0.8rem;">No reports yet.</p>',
            unsafe_allow_html=True,
        )


# ── Main Content Area ───────────────────────────────────────

# Title
st.markdown(
    '<p class="gradient-title">NexRay</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="subtitle">Advanced Diagnostic Imaging & Reporting</p>',
    unsafe_allow_html=True,
)
st.markdown("---")


# ── Handle Analysis ─────────────────────────────────────────
if analyze_clicked:
    if not uploaded_file:
        st.warning("⚠️ Please upload a medical image before analyzing.")
    else:
        # Save uploaded file to temp location
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        st.session_state.image_path = tmp_path
        st.session_state.report_saved = False
        st.session_state.chat_history = []

        # Build patient info string
        patient_info_str = ""
        if patient_id:
            patient_info_str += f"ID: {patient_id}"
        if patient_name:
            if patient_info_str:
                patient_info_str += ", "
            patient_info_str += f"Name: {patient_name}"

        # Build prompt with RAG context
        rag_context = retrieve_context(
            rag_retriever,
            modality=modality,
            clinical_context=clinical_context,
        )
        prompt = build_combined_prompt(
            modality=modality,
            clinical_context=clinical_context,
            patient_info=patient_info_str,
            rag_context=rag_context,
        )
        rag_active = bool(rag_context)

        # Run inference
        with st.spinner(""):
            st.markdown(
                f"""
                <div class="custom-spinner">
                    <div class="ring"></div>
                </div>
                <p style="text-align:center; color:#555; font-size:0.85rem; margin-top:-1rem;">
                    Processing diagnostic scan...
                    {"<br><span style='color:#00d4aa; font-size:0.75rem;'>📚 Cross-referencing clinical guidelines...</span>" if rag_active else ""}
                </p>
                """,
                unsafe_allow_html=True,
            )

            try:
                model, processor, config = get_model()
                response_text, inf_time, tok_count = analyze_image(
                    model, processor, config, tmp_path, prompt
                )
            except FileNotFoundError as e:
                st.error(f"🚫 Model not found. {str(e)}")
                st.stop()
            except Exception as e:
                st.error(f"🚫 Inference error: {str(e)}")
                st.stop()

        # Parse the response
        parsed = parse_model_output(response_text)
        st.session_state.report_data = parsed
        st.session_state.raw_response = response_text
        st.session_state.inference_time = inf_time
        st.session_state.token_count = tok_count

        # Auto-save to database
        try:
            save_report(
                db_path=DB_PATH,
                patient_id=patient_id or "N/A",
                patient_name=patient_name or "N/A",
                modality=modality,
                clinical_context=clinical_context or "",
                report_data=parsed,
                image_filename=uploaded_file.name,
                inference_time=inf_time,
                token_count=tok_count,
            )
            st.session_state.report_saved = True
        except Exception as e:
            st.warning(f"⚠️ Report generated but could not be saved: {e}")


# ── Display Results ─────────────────────────────────────────
if st.session_state.report_data and uploaded_file:
    report = st.session_state.report_data

    # Side-by-side layout
    col_img, col_report = st.columns([1, 1.3], gap="large")

    # ── Left Column: Image + Toolbar ────────────────────────
    with col_img:
        st.markdown(
            '<h3 style="font-size:0.75rem; text-transform:uppercase; letter-spacing:2px; '
            'color:#666; margin-bottom:0.5rem;">Uploaded Study</h3>',
            unsafe_allow_html=True,
        )

        # Image Inspection Toolbar
        st.markdown('<div class="image-toolbar">', unsafe_allow_html=True)
        toolbar_cols = st.columns([1, 1, 1])
        with toolbar_cols[0]:
            st.session_state.img_invert = st.toggle(
                "🔄 Invert",
                value=st.session_state.img_invert,
                help="Invert colors (Bone Suppression view)"
            )
        with toolbar_cols[1]:
            st.session_state.img_brightness = st.slider(
                "☀️ Brightness",
                0.2, 3.0,
                value=st.session_state.img_brightness,
                step=0.1,
                help="Adjust image brightness"
            )
        with toolbar_cols[2]:
            st.session_state.img_contrast = st.slider(
                "🔲 Contrast",
                0.2, 3.0,
                value=st.session_state.img_contrast,
                step=0.1,
                help="Adjust image contrast"
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # ROI toggle
        st.session_state.show_bbox = st.toggle(
            "🎯 Toggle AI Bounding Box",
            value=st.session_state.show_bbox,
            help="Show Region of Interest overlay"
        )

        # Load and process image
        img = Image.open(uploaded_file)
        display_img = apply_image_adjustments(img)
        if st.session_state.show_bbox:
            display_img = draw_roi_overlay(display_img)
        st.image(display_img, width="stretch")

        # Image metadata
        w, h = img.size
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        st.markdown(
            f'<div class="metrics-info">'
            f"📐 {w} × {h} px &nbsp;·&nbsp; 📦 {file_size_kb:.1f} KB &nbsp;·&nbsp; "
            f"🔬 {modality}</div>",
            unsafe_allow_html=True,
        )

        # Free-form narrative expander
        if report.get("narrative"):
            with st.expander("📝 Free-Form Clinical Dictation"):
                st.markdown(
                    f'<p style="color:#b0b0b0; line-height:1.8; font-size:0.9rem;">'
                    f'{report["narrative"]}</p>',
                    unsafe_allow_html=True,
                )

    # ── Right Column: Structured Report ─────────────────────
    with col_report:
        st.markdown(
            '<h3 style="font-size:0.75rem; text-transform:uppercase; letter-spacing:2px; '
            'color:#666; margin-bottom:0.5rem;">Diagnostic Report</h3>',
            unsafe_allow_html=True,
        )

        # Findings — rendered as styled list items
        if report.get("findings"):
            findings_html = render_findings_html(report["findings"])
            st.markdown(
                f'<div class="report-card">'
                f"<h4>🔍 Findings</h4>"
                f'{findings_html}'
                f"</div>",
                unsafe_allow_html=True,
            )

        # Differential Diagnosis — rendered with severity badges
        if report.get("differential_diagnosis"):
            dx_html = render_diagnosis_html(report["differential_diagnosis"])
            st.markdown(
                f'<div class="report-card">'
                f"<h4>🩺 Differential Diagnosis</h4>"
                f'{dx_html}'
                f"</div>",
                unsafe_allow_html=True,
            )

        # Recommended Actions — rendered as numbered list
        if report.get("recommended_actions"):
            actions_html = render_actions_html(report["recommended_actions"])
            st.markdown(
                f'<div class="report-card">'
                f"<h4>📋 Recommended Actions</h4>"
                f'{actions_html}'
                f"</div>",
                unsafe_allow_html=True,
            )

        # Clinical Notes — rendered as styled list
        if report.get("clinical_notes"):
            notes_html = render_findings_html(report["clinical_notes"])
            st.markdown(
                f'<div class="report-card">'
                f"<h4>📝 Clinical Notes</h4>"
                f'{notes_html}'
                f"</div>",
                unsafe_allow_html=True,
            )

        # Disclaimer
        st.markdown(
            '<div class="disclaimer">'
            "⚕️ <strong>Medical Disclaimer:</strong> This report is generated by an AI system "
            "and is not a substitute for professional clinical judgment, diagnosis, or treatment. "
            "Always consult a qualified healthcare professional."
            "</div>",
            unsafe_allow_html=True,
        )

        # Action buttons — PDF, FHIR, Copy
        btn_col1, btn_col2, btn_col3 = st.columns(3)

        with btn_col1:
            try:
                pdf_bytes = generate_pdf(
                    patient_id=patient_id or "N/A",
                    patient_name=patient_name or "N/A",
                    modality=modality,
                    clinical_context=clinical_context or "",
                    report_data=report,
                    inference_time=st.session_state.inference_time,
                    token_count=st.session_state.token_count,
                    image_path=st.session_state.image_path,
                )
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"NexRay_Report_{timestamp}.pdf"
                st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
                st.download_button(
                    label="📄  Export PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    width="stretch",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"PDF generation failed: {e}")

        with btn_col2:
            try:
                fhir_json = generate_fhir_json(
                    patient_id=patient_id or "N/A",
                    patient_name=patient_name or "N/A",
                    modality=modality,
                    clinical_context=clinical_context or "",
                    report_data=report,
                    inference_time=st.session_state.inference_time,
                    token_count=st.session_state.token_count,
                )
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                fhir_filename = f"NexRay_FHIR_{timestamp}.json"
                st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
                st.download_button(
                    label="🏥  Export FHIR",
                    data=fhir_json,
                    file_name=fhir_filename,
                    mime="application/json",
                    width="stretch",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"FHIR export failed: {e}")

        with btn_col3:
            full_report_text = (
                f"FINDINGS:\n{report.get('findings', 'N/A')}\n\n"
                f"DIFFERENTIAL DIAGNOSIS:\n{report.get('differential_diagnosis', 'N/A')}\n\n"
                f"RECOMMENDED ACTIONS:\n{report.get('recommended_actions', 'N/A')}\n\n"
                f"CLINICAL NOTES:\n{report.get('clinical_notes', 'N/A')}\n\n"
                f"NARRATIVE:\n{report.get('narrative', 'N/A')}"
            )
            st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
            if st.button("📋  Copy Report", width="stretch"):
                st.code(full_report_text, language=None)
                st.info("Report text displayed above — copy it from there.")
            st.markdown("</div>", unsafe_allow_html=True)

    # ── Clinical Copilot Chat ───────────────────────────────
    st.markdown("---")
    with st.expander("💬 Radiologist Assistant (Offline Multi-Turn Chat)", expanded=False):
        st.markdown(
            '<p style="color:#666; font-size:0.8rem; margin-bottom:1rem;">'
            "Ask follow-up questions about the report. Examples: "
            '"Draft a patient-friendly explanation", '
            '"What oblique view angles should I order?", '
            '"Summarize for the referring physician"'
            "</p>",
            unsafe_allow_html=True,
        )

        # Display chat history
        if st.session_state.chat_history:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="chat-msg-user">🧑‍⚕️ {msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="chat-msg-ai">🤖 {msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
            st.markdown('</div>', unsafe_allow_html=True)

        # Chat input
        chat_input = st.chat_input(
            "Ask a follow-up question about the report...",
        )

        if chat_input:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": chat_input,
            })

            # Get AI response
            with st.spinner("Thinking..."):
                try:
                    model, processor, config = get_model()
                    report_context = st.session_state.raw_response or ""
                    ai_response, chat_time = chat_followup(
                        model=model,
                        processor=processor,
                        config=config,
                        chat_history=st.session_state.chat_history[:-1],
                        user_message=chat_input,
                        report_context=report_context,
                        image_path=st.session_state.image_path,
                    )
                except Exception as e:
                    ai_response = f"Error: {str(e)}"
                    chat_time = 0.0

            # Add AI response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": ai_response,
            })

            st.rerun()

    # ── Telemetry Footer ────────────────────────────────────
    mem_usage = get_memory_usage()
    st.markdown(
        f'<div class="telemetry-bar">'
        f'<div class="telemetry-item">⏱️ Inference: <span class="value">{st.session_state.inference_time:.1f}s</span></div>'
        f'<div class="telemetry-item">🧠 Memory: <span class="value">{mem_usage}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Empty State (no analysis yet) ───────────────────────────
elif not st.session_state.report_data:
    st.markdown("<br>", unsafe_allow_html=True)

    empty_col1, empty_col2, empty_col3 = st.columns([1, 2, 1])
    with empty_col2:
        st.markdown(
            """
            <div style="text-align:center; padding:4rem 2rem;">
                <div style="font-size:4rem; margin-bottom:1rem; opacity:0.3;">🏥</div>
                <h3 style="color:#555; font-weight:400; font-size:1.1rem;">
                    Upload a medical image to begin analysis
                </h3>
                <p style="color:#444; font-size:0.85rem; max-width:400px; margin:0.5rem auto; line-height:1.6;">
                    Select the imaging modality, provide optional patient context,
                    and click <strong style="color:#1a73e8;">Analyze Image</strong>
                    to generate a comprehensive clinical report.
                </p>
                <div style="margin-top:2rem;">
                    <span class="badge-low" style="margin:0 4px;">X-ray</span>
                    <span class="badge-moderate" style="margin:0 4px;">MRI</span>
                    <span class="badge-high" style="margin:0 4px;">CT Scan</span>
                    <span class="badge-low" style="margin:0 4px;">Fundus</span>
                    <span class="badge-moderate" style="margin:0 4px;">Dermoscopy</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Telemetry footer even in empty state
    st.markdown(
        f'<div class="telemetry-bar">'
        f'<div class="telemetry-item">⏱️ Inference: <span class="value">—</span></div>'
        f'<div class="telemetry-item">🧠 Memory: <span class="value">—</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
