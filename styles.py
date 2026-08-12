"""
Custom CSS injection for Hack4Health Streamlit UI.
Enterprise Apple Health dark mode aesthetic with glassmorphism effects.
"""
import streamlit as st


def inject_custom_css():
    """Injects the complete custom CSS theme into the Streamlit app."""
    st.markdown("""
<style>
/* ============================================
   1. FONT IMPORT
   ============================================ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ============================================
   2. GLOBAL STYLING & BACKGROUND
   ============================================ */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #0a0a0a !important;
    color: #e0e0e0 !important;
}

.main .block-container {
    padding-top: 2rem !important;
    max-width: 1200px !important;
}

/* ============================================
   3. HIDE STREAMLIT BRANDING
   ============================================ */
#MainMenu {visibility: hidden !important;}
header {visibility: hidden !important; display: none !important;}
footer {visibility: hidden !important; display: none !important;}
.stDeployButton {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}

/* ============================================
   4. GLASSMORPHISM SIDEBAR
   ============================================ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(15,15,15,0.97) 0%, rgba(8,8,8,0.97) 100%) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] p {
    color: #a0a0a0 !important;
    font-size: 0.85rem !important;
}

/* Sidebar Section Headers */
[data-testid="stSidebar"] .stMarkdown h3 {
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    font-size: 0.7rem !important;
    color: #666666 !important;
    font-weight: 600 !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.5rem !important;
    padding-bottom: 0.3rem !important;
    border-bottom: 1px solid rgba(255,255,255,0.06) !important;
}

/* ============================================
   5. TYPOGRAPHY & HEADERS
   ============================================ */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Gradient Title Effect */
.gradient-title {
    background: linear-gradient(135deg, #00d4aa 0%, #00bfff 50%, #00d4aa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 0;
    animation: shimmer 3s ease-in-out infinite;
    background-size: 200% 100%;
}

@keyframes shimmer {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

.subtitle {
    color: #666666;
    font-size: 0.85rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 2px;
}

/* ============================================
   6. INPUTS & SELECTBOXES
   ============================================ */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #141414 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > div:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #00d4aa !important;
    box-shadow: 0 0 0 1px rgba(0, 212, 170, 0.3), 0 0 12px rgba(0, 212, 170, 0.1) !important;
}

/* Select dropdown label */
.stSelectbox label, .stTextInput label, .stTextArea label {
    color: #a0a0a0 !important;
    font-size: 0.85rem !important;
}

/* ============================================
   7. FILE UPLOADER
   ============================================ */
[data-testid="stFileUploadDropzone"] {
    background-color: rgba(20, 20, 20, 0.6) !important;
    border: 1px dashed rgba(255,255,255,0.15) !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: #00d4aa !important;
    background-color: rgba(0, 212, 170, 0.03) !important;
    box-shadow: 0 0 20px rgba(0, 212, 170, 0.05) !important;
}

/* ============================================
   8. BUTTONS
   ============================================ */

/* Analyze Button (Primary CTA) */
.analyze-btn > div > button {
    width: 100% !important;
    border-radius: 12px !important;
    background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1.5rem !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(26, 115, 232, 0.25) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    letter-spacing: 0.5px !important;
}

.analyze-btn > div > button:hover {
    box-shadow: 0 8px 25px rgba(26, 115, 232, 0.4) !important;
    transform: translateY(-2px) !important;
}

.analyze-btn > div > button:active {
    transform: translateY(0) !important;
}

/* Ghost Button */
.ghost-btn > div > button {
    background: transparent !important;
    border: 1px solid rgba(0, 212, 170, 0.5) !important;
    color: #00d4aa !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
    font-size: 0.85rem !important;
}

.ghost-btn > div > button:hover {
    background: rgba(0, 212, 170, 0.08) !important;
    border-color: #00d4aa !important;
    box-shadow: 0 0 15px rgba(0, 212, 170, 0.15) !important;
}

/* ============================================
   9. GLASSMORPHISM CARDS & METRICS
   ============================================ */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.03) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    transition: all 0.3s ease !important;
}

[data-testid="metric-container"]:hover {
    transform: translateY(-2px) !important;
    border-color: rgba(0, 212, 170, 0.2) !important;
}

/* Report Section Cards */
.report-card {
    background: rgba(255,255,255,0.025);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 3px solid #00d4aa;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}

.report-card:hover {
    transform: translateY(-1px);
    border-color: rgba(0, 212, 170, 0.15);
    border-left-color: #00d4aa;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.report-card h4 {
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #00d4aa !important;
    margin-bottom: 0.75rem;
}

.report-card p, .report-card li {
    color: #c8c8c8;
    font-size: 0.9rem;
    line-height: 1.7;
}

/* Metrics Monospace */
.metrics-info {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.78rem;
    color: #555555;
    padding: 0.5rem 0;
    border-top: 1px solid rgba(255,255,255,0.04);
    margin-top: 1rem;
}

/* ============================================
   10. EXPANDERS
   ============================================ */
.streamlit-expanderHeader {
    background-color: rgba(255,255,255,0.02) !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
    font-weight: 500 !important;
}

.streamlit-expanderHeader:hover {
    color: #00d4aa !important;
    background-color: rgba(0, 212, 170, 0.04) !important;
}

.streamlit-expanderContent {
    background-color: rgba(255,255,255,0.01) !important;
    border: 1px solid rgba(255,255,255,0.04) !important;
    border-top: none !important;
    border-bottom-left-radius: 10px !important;
    border-bottom-right-radius: 10px !important;
    padding: 1rem !important;
}

/* ============================================
   11. IMAGES
   ============================================ */
[data-testid="stImage"] img {
    border-radius: 12px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
    transition: all 0.3s ease !important;
}

[data-testid="stImage"] img:hover {
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6) !important;
}

/* ============================================
   12. SCROLLBAR
   ============================================ */
::-webkit-scrollbar {
    width: 5px;
    height: 5px;
}

::-webkit-scrollbar-track {
    background: #0a0a0a;
}

::-webkit-scrollbar-thumb {
    background: rgba(0, 212, 170, 0.2);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 212, 170, 0.4);
}

/* ============================================
   13. DISCLAIMER
   ============================================ */
.disclaimer {
    color: #777777;
    font-style: italic;
    font-size: 0.82rem;
    border-left: 3px solid #ffb300;
    padding: 0.75rem 1rem;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    background: rgba(255, 179, 0, 0.03);
    border-radius: 0 8px 8px 0;
    line-height: 1.6;
}

/* ============================================
   14. CONFIDENCE / SEVERITY BADGES
   ============================================ */
.badge-critical {
    display: inline-block;
    background-color: rgba(244, 67, 54, 0.12);
    color: #ff5252;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    border: 1px solid rgba(244, 67, 54, 0.25);
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.badge-high {
    display: inline-block;
    background-color: rgba(255, 152, 0, 0.12);
    color: #ffb300;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    border: 1px solid rgba(255, 152, 0, 0.25);
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.badge-moderate {
    display: inline-block;
    background-color: rgba(33, 150, 243, 0.12);
    color: #42a5f5;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    border: 1px solid rgba(33, 150, 243, 0.25);
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.badge-low {
    display: inline-block;
    background-color: rgba(76, 175, 80, 0.12);
    color: #69f0ae;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    border: 1px solid rgba(76, 175, 80, 0.25);
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ============================================
   15. CUSTOM SPINNER
   ============================================ */
.custom-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 3rem 0;
}

.custom-spinner .ring {
    width: 48px;
    height: 48px;
    border: 3px solid rgba(0, 212, 170, 0.1);
    border-top: 3px solid #00d4aa;
    border-radius: 50%;
    animation: spin 1s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.stSpinner > div > div {
    border-color: rgba(0, 212, 170, 0.15) !important;
    border-top-color: #00d4aa !important;
}

/* ============================================
   16. LOGO & BRANDING
   ============================================ */
.sidebar-logo {
    text-align: center;
    padding: 1.5rem 0 1rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 1rem;
}

.sidebar-logo .logo-text {
    font-size: 1.3rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00d4aa, #00bfff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}

.sidebar-logo .logo-sub {
    font-size: 0.65rem;
    color: #555555;
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-top: 2px;
}

/* ============================================
   17. DIVIDERS & SEPARATORS
   ============================================ */
hr {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.06) !important;
    margin: 1.5rem 0 !important;
}

/* ============================================
   18. TABS (if used)
   ============================================ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    background: rgba(255,255,255,0.02) !important;
    border-radius: 10px !important;
    padding: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: #888888 !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(0, 212, 170, 0.1) !important;
    color: #00d4aa !important;
}

/* ============================================
   19. STATUS INDICATOR
   ============================================ */
.status-ready {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #69f0ae;
    font-size: 0.78rem;
    font-weight: 500;
}

.status-ready::before {
    content: '';
    width: 6px;
    height: 6px;
    background: #69f0ae;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(105, 240, 174, 0.5);
    animation: pulse 2s ease-in-out infinite;
}

.status-offline {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #00d4aa;
    font-size: 0.78rem;
    font-weight: 500;
}

.status-offline::before {
    content: '';
    width: 6px;
    height: 6px;
    background: #00d4aa;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(0, 212, 170, 0.4);
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
</style>
""", unsafe_allow_html=True)
