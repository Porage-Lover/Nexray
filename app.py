"""
Hack4Health — Sovereign Clinical AI
A fully offline medical image analysis system powered by HealthGPT-Pro-8B
running locally on Apple Silicon via MLX.

Entry point: streamlit run app.py
"""
import os
import tempfile
import datetime
from PIL import Image
import streamlit as st

from styles import inject_custom_css
from prompts import MODALITIES, build_combined_prompt, parse_model_output
from engine import get_model, analyze_image
from database import init_database, save_report, get_all_reports
from pdf_export import generate_pdf


# ── Page Configuration ──────────────────────────────────────
st.set_page_config(
    page_title="Hack4Health — Clinical AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Custom CSS ───────────────────────────────────────
inject_custom_css()

# ── Constants ───────────────────────────────────────────────
DB_PATH = "./data/reports.db"

# ── Initialize Database ────────────────────────────────────
init_database(DB_PATH)

# ── Session State ───────────────────────────────────────────
if "report_data" not in st.session_state:
    st.session_state.report_data = None
if "raw_response" not in st.session_state:
    st.session_state.raw_response = None
if "inference_time" not in st.session_state:
    st.session_state.inference_time = 0.0
if "token_count" not in st.session_state:
    st.session_state.token_count = 0
if "image_path" not in st.session_state:
    st.session_state.image_path = None
if "report_saved" not in st.session_state:
    st.session_state.report_saved = False


# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    # Logo / Branding
    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="logo-text">🏥 Hack4Health</div>
            <div class="logo-sub">Sovereign Clinical AI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Status indicator
    st.markdown(
        '<div class="status-offline">● Fully Offline &nbsp;·&nbsp; Zero Data Leakage</div>',
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
    if st.button("⚡  Analyze Image", use_container_width=True):
        analyze_clicked = True
    st.markdown("</div>", unsafe_allow_html=True)

    # Report History
    st.markdown("---")
    st.markdown("### Report History")
    past_reports = get_all_reports(DB_PATH)
    if past_reports:
        st.markdown(
            f'<p style="color:#555; font-size:0.8rem;">{len(past_reports)} report(s) saved</p>',
            unsafe_allow_html=True,
        )
        for r in past_reports[:5]:
            created = r.get("created_at", "")[:16].replace("T", " ")
            st.markdown(
                f'<p style="color:#888; font-size:0.78rem; margin:2px 0;">'
                f'📋 {r.get("modality", "—")} · {r.get("patient_name", "N/A")[:15]} · {created}'
                f"</p>",
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
    '<p class="gradient-title">Hack4Health</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="subtitle">Sovereign Clinical AI · Powered by HealthGPT-Pro</p>',
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

        # Build patient info string
        patient_info_str = ""
        if patient_id:
            patient_info_str += f"ID: {patient_id}"
        if patient_name:
            if patient_info_str:
                patient_info_str += ", "
            patient_info_str += f"Name: {patient_name}"

        # Build prompt
        prompt = build_combined_prompt(
            modality=modality,
            clinical_context=clinical_context,
            patient_info=patient_info_str,
        )

        # Run inference
        with st.spinner(""):
            st.markdown(
                """
                <div class="custom-spinner">
                    <div class="ring"></div>
                </div>
                <p style="text-align:center; color:#555; font-size:0.85rem; margin-top:-1rem;">
                    Analyzing image with HealthGPT-Pro on Apple Silicon...
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

    # ── Left Column: Image ──────────────────────────────────
    with col_img:
        st.markdown(
            '<h3 style="font-size:0.75rem; text-transform:uppercase; letter-spacing:2px; '
            'color:#666; margin-bottom:0.5rem;">Uploaded Study</h3>',
            unsafe_allow_html=True,
        )

        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)

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

        # Findings
        if report.get("findings"):
            st.markdown(
                f'<div class="report-card">'
                f"<h4>🔍 Findings</h4>"
                f'<p>{report["findings"]}</p>'
                f"</div>",
                unsafe_allow_html=True,
            )

        # Differential Diagnosis
        if report.get("differential_diagnosis"):
            st.markdown(
                f'<div class="report-card">'
                f"<h4>🩺 Differential Diagnosis</h4>"
                f'<p>{report["differential_diagnosis"]}</p>'
                f"</div>",
                unsafe_allow_html=True,
            )

        # Recommended Actions
        if report.get("recommended_actions"):
            st.markdown(
                f'<div class="report-card">'
                f"<h4>📋 Recommended Actions</h4>"
                f'<p>{report["recommended_actions"]}</p>'
                f"</div>",
                unsafe_allow_html=True,
            )

        # Clinical Notes
        if report.get("clinical_notes"):
            st.markdown(
                f'<div class="report-card">'
                f"<h4>📝 Clinical Notes</h4>"
                f'<p>{report["clinical_notes"]}</p>'
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

        # Action buttons
        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            # Copy Report
            full_report_text = (
                f"FINDINGS:\n{report.get('findings', 'N/A')}\n\n"
                f"DIFFERENTIAL DIAGNOSIS:\n{report.get('differential_diagnosis', 'N/A')}\n\n"
                f"RECOMMENDED ACTIONS:\n{report.get('recommended_actions', 'N/A')}\n\n"
                f"CLINICAL NOTES:\n{report.get('clinical_notes', 'N/A')}\n\n"
                f"NARRATIVE:\n{report.get('narrative', 'N/A')}"
            )
            st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
            if st.button("📋  Copy Report", use_container_width=True):
                st.code(full_report_text, language=None)
                st.info("Report text displayed above — copy it from there.")
            st.markdown("</div>", unsafe_allow_html=True)

        with btn_col2:
            # Export PDF
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
                filename = f"Hack4Health_Report_{timestamp}.pdf"
                st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
                st.download_button(
                    label="📄  Export PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"PDF generation failed: {e}")

        # Inference metrics
        st.markdown(
            f'<div class="metrics-info">'
            f"⚡ Inference: {st.session_state.inference_time:.2f}s &nbsp;·&nbsp; "
            f"🔤 ~{st.session_state.token_count} tokens &nbsp;·&nbsp; "
            f"💾 {'Saved' if st.session_state.report_saved else 'Not saved'} &nbsp;·&nbsp; "
            f"🖥️ HealthGPT-Pro-8B (4-bit, MLX)"
            f"</div>",
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
