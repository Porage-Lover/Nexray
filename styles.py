"""
Custom macOS HIG (Human Interface Guidelines) CSS injection for Hack4Health Streamlit UI.
"""

macos_hig_css = """
<style>
/* ============================================
   1. MAC OS HIG TYPOGRAPHY
   ============================================ */
p, h1, h2, h3, h4, h5, h6, label, input, textarea, select, .stMarkdown, div[data-testid="stText"] {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", Helvetica, Arial, sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
}

/* Preserve Streamlit Icon Fonts */
[data-testid="stIcon"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] *,
[data-testid="stSidebarHeader"] *,
.material-symbols-outlined,
.material-icons,
[class*="material-symbols"] {
    font-family: 'Material Symbols Outlined', 'Material Icons' !important;
    font-weight: normal !important;
    font-style: normal !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-smoothing: antialiased !important;
}

/* ============================================
   2. GLOBAL BACKGROUND & LAYOUT
   ============================================ */
.stApp {
    background-color: #121212 !important;
    color: #ffffff !important;
}

.main .block-container {
    padding-top: 2rem !important;
    padding-bottom: 60px !important;
    max-width: 1200px !important;
}

/* ============================================
   3. CLEAN THE CANVAS & NUCLEAR ICON FALLBACK
   ============================================ */
#MainMenu { visibility: hidden !important; }
header[data-testid="stHeader"] { 
    background-color: transparent !important; 
    pointer-events: none !important; /* Prevent transparent header from blocking clicks */
}
header[data-testid="stHeader"] * {
    pointer-events: auto !important; /* Allow buttons inside header to be clicked */
}
footer { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

/* Target the exact inner span of the collapse/expand buttons */
[data-testid="stSidebarCollapseButton"] span,
[data-testid="baseButton-header"] span,
button[kind="header"] span {
    font-size: 0px !important; /* Hides the ugly broken text string */
    color: transparent !important; 
}

/* Inject a clean, native macOS chevron in its place */
[data-testid="stSidebarCollapseButton"] span::after {
    content: "☰" !important; /* Apple SF Symbol for sidebar (or use "☰" / "‹‹" if SF symbols fail) */
    font-size: 18px !important;
    color: #ffffff !important;
    display: block !important;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-weight: 300 !important;
}

/* Restore Floating Expand Button when Sidebar is Collapsed */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    position: fixed !important;
    top: 12px !important;
    left: 12px !important;
    z-index: 999999 !important;
    background-color: rgba(30, 30, 30, 0.85) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 8px !important;
    padding: 4px !important;
    cursor: pointer !important;
}

/* Make the icon inside the collapsed control clearly visible */
[data-testid="collapsedControl"] span,
[data-testid="collapsedControl"] button,
[data-testid="stSidebarCollapsedControl"] span,
[data-testid="stSidebarCollapsedControl"] button {
    color: #ffffff !important;
    font-size: 16px !important;
    visibility: visible !important;
}

/* If ligature text breaks inside collapsed control, render a clean fallback icon */
[data-testid="collapsedControl"] span::after,
[data-testid="stSidebarCollapsedControl"] span::after {
    content: "›" !important;
    font-size: 20px !important;
    font-weight: bold !important;
    color: #0A84FF !important;
}

/* ============================================
   4. WINDOW MATERIALS (GLASSMORPHISM / VIBRANCY)
   ============================================ */
/* Sidebar */
[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    width: 340px !important;
    min-width: 340px !important;
    background-color: rgba(18, 18, 18, 0.75) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}
[data-testid="stSidebarContent"] {
    visibility: visible !important;
    padding-top: 1.5rem !important;
}

/* Metric Containers & Custom Report Cards */
[data-testid="metric-container"], .report-card {
    background-color: rgba(25, 25, 25, 0.65) !important;
    backdrop-filter: blur(24px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    padding: 1.25rem 1.5rem !important;
    margin-bottom: 1rem !important;
}

/* Adjust report card specific elements */
.report-card h4 {
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #0A84FF !important;
    margin-bottom: 0.75rem;
}

/* ============================================
   5. DESKTOP CORNER RADII (INPUTS & IMAGES)
   ============================================ */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
[data-testid="stImage"] img,
[data-testid="stFileUploadDropzone"] {
    border-radius: 12px !important;
    background-color: rgba(30, 30, 30, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    transition: border-color 0.2s ease !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > div:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #0A84FF !important;
    box-shadow: 0 0 0 1px #0A84FF !important;
}

/* ============================================
   6. CONTROLS & ACCENT COLORS (BUTTONS)
   ============================================ */
.stButton > button, .analyze-btn > div > button, .ghost-btn > div > button {
    border-radius: 6px !important;
    background: linear-gradient(180deg, #1A8CFF 0%, #0070E0 100%) !important;
    border: 1px solid #005FBF !important;
    color: #ffffff !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.4rem 1rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.2) !important;
    transition: transform 0.1s ease, filter 0.1s ease !important;
}

/* Hover & Active States for Buttons */
.stButton > button:hover, .analyze-btn > div > button:hover, .ghost-btn > div > button:hover {
    filter: brightness(1.1) !important;
}

.stButton > button:active, .analyze-btn > div > button:active, .ghost-btn > div > button:active {
    transform: scale(0.97) !important;
    background: #0070E0 !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.3) !important;
}

/* Override ghost button to look like native secondary buttons */
.ghost-btn > div > button {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    box-shadow: none !important;
}
.ghost-btn > div > button:hover {
    background: rgba(255, 255, 255, 0.15) !important;
}
.ghost-btn > div > button:active {
    background: rgba(255, 255, 255, 0.05) !important;
}

/* ============================================
   7. CUSTOM COMPONENT SUPPORT (BADGES, TELEMETRY, ETC)
   ============================================ */
/* Gradient Title (Updated to HIG colors) */
.gradient-title {
    background: linear-gradient(135deg, #0A84FF 0%, #5E5CE6 50%, #0A84FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 0;
}
.subtitle {
    color: #8E8E93;
    font-size: 0.85rem;
    letter-spacing: 1px;
    margin-top: 2px;
}

/* Badges */
.badge-critical { background: #FF453A; color: #fff; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; margin-right: 6px; }
.badge-high { background: #FF9F0A; color: #fff; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; margin-right: 6px; }
.badge-moderate { background: #FFD60A; color: #1c1c1e; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; margin-right: 6px; }
.badge-low { background: #32D74B; color: #1c1c1e; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; margin-right: 6px; }

/* Lists & Findings */
.diagnosis-item { display: flex; align-items: flex-start; gap: 8px; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.diagnosis-item:last-child { border-bottom: none; }
.diagnosis-text { color: #E5E5EA; font-size: 0.85rem; }
.finding-item { color: #E5E5EA; font-size: 0.85rem; padding: 2px 0 2px 10px; border-left: 2px solid #0A84FF; margin-bottom: 6px; }

/* Telemetry Bar */
.telemetry-bar {
    position: fixed; bottom: 0; left: 0; right: 0; z-index: 9999;
    background-color: rgba(25, 25, 25, 0.65);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    border-top: 1px solid rgba(255,255,255,0.1);
    padding: 8px 24px; display: flex; justify-content: center; align-items: center; gap: 32px;
    font-size: 0.75rem;
}
.telemetry-item { color: #8E8E93; display: flex; align-items: center; gap: 6px; }
.telemetry-item .value { color: #E5E5EA; font-weight: 600; }
.telemetry-secure { color: #32D74B; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.telemetry-secure::before {
    content: ''; width: 6px; height: 6px; background: #32D74B; border-radius: 50%;
    box-shadow: 0 0 8px rgba(50, 215, 75, 0.6); animation: pulse 2s infinite;
}

/* Chat & Image Toolbar */
.chat-container { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1rem; max-height: 400px; overflow-y: auto; }
.chat-msg-user { background: #0A84FF; color: #fff; border-radius: 14px 14px 4px 14px; padding: 8px 12px; margin: 6px 0; font-size: 0.85rem; max-width: 80%; margin-left: auto; }
.chat-msg-ai { background: rgba(255,255,255,0.1); color: #E5E5EA; border-radius: 14px 14px 14px 4px; padding: 8px 12px; margin: 6px 0; font-size: 0.85rem; max-width: 80%; }
.image-toolbar { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 0.5rem; margin-bottom: 0.75rem; }

/* Custom Spinner */
.custom-spinner { display: flex; justify-content: center; align-items: center; padding: 2rem 0; }
.custom-spinner .ring { width: 40px; height: 40px; border: 3px solid rgba(10, 132, 255, 0.2); border-top: 3px solid #0A84FF; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* Sidebar UI Helpers */
.sidebar-logo { text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1rem; }
.logo-text { font-size: 1.2rem; font-weight: 700; color: #fff; }
.logo-sub { font-size: 0.7rem; color: #8E8E93; }
.status-offline { color: #32D74B; font-size: 0.75rem; font-weight: 500; display: flex; align-items: center; gap: 4px; }
.disclaimer { color: #8E8E93; font-size: 0.8rem; font-style: italic; background: rgba(255,255,255,0.03); border-radius: 8px; padding: 10px; margin-top: 1rem; border: 1px solid rgba(255,255,255,0.05); }
.metrics-info { font-family: 'SF Mono', monospace; font-size: 0.75rem; color: #8E8E93; margin-top: 0.5rem; }

</style>
"""
