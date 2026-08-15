# 🏥 Nexray — Sovereign Clinical AI

A **fully offline** medical image analysis system powered by **HealthGPT-Pro-8B** running locally on Apple Silicon via MLX. Zero data leakage. Complete patient data sovereignty.

---

## ✨ Features

- **100% Offline** — After one-time model download, no internet connection required
- **Multimodal Medical AI** — Analyzes X-rays, MRIs, CT scans, fundus photography, dermoscopy, and more
- **Structured Clinical Reports** — Findings, differential diagnosis, recommended actions, clinical notes
- **Free-Form Narrative** — Radiologist-style dictation alongside structured data
- **Confidence Scores** — Each finding includes confidence percentages and severity ratings
- **Encrypted Storage** — All patient data encrypted at rest with Fernet symmetric encryption
- **PDF Export** — Enterprise-grade clinical reports with embedded images
- **Premium UI** — Dark glassmorphic design with Apple Health aesthetics

## 🏗️ Architecture

```
Medical Image → Pillow (Standardize) → HealthGPT-Pro-8B (MLX) → Structured Report + Narrative
                                                                        ↓
                                                              Encrypted SQLite + PDF Export
```

**Model**: `lintw/HealthGPT-Pro-8B` (Qwen3-VL architecture, 4-bit quantized)  
**Framework**: MLX via `mlx-vlm` — native Apple Silicon acceleration  
**UI**: Streamlit with custom CSS injection  
**Storage**: SQLite + `cryptography` (Fernet)  
**Export**: `fpdf2` (no system binary dependencies)

## 🚀 Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.10+
- ~5GB disk space for quantized model

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download & Quantize the Model (One-Time)

```bash
chmod +x setup_model.sh
./setup_model.sh
```

This downloads HealthGPT-Pro-8B (~16GB) from Hugging Face and quantizes it to 4-bit (~5GB).  
**Requires internet. All subsequent runs are fully offline.**

### 3. Launch the App

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## 📁 Project Structure

```
Nexray/
├── app.py              # Streamlit entry point
├── engine.py           # MLX model loading & inference
├── prompts.py          # Clinical prompt templates & output parsing
├── database.py         # Encrypted SQLite operations
├── pdf_export.py       # PDF report generation
├── styles.py           # Custom CSS (dark glassmorphism theme)
├── setup_model.sh      # Model download & quantization script
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── models/             # Pre-downloaded quantized model (created by setup_model.sh)
│   └── HealthGPT-Pro-8B-4bit/
├── data/               # Encrypted SQLite database (created on first run)
│   ├── reports.db
│   └── .encryption_key
└── Plan.md             # Original architecture plan
```

## 🔒 Security & Data Sovereignty

- **Zero network calls** during inference — model runs entirely in local memory
- **Fernet encryption** (AES-128-CBC) for all patient data at rest
- **No telemetry, no cloud, no APIs** — complete data isolation
- Encryption key stored locally at `./data/.encryption_key`

## ⚠️ Medical Disclaimer

This system is an AI-powered research tool and is **not a substitute for professional clinical judgment, diagnosis, or treatment**. Always consult a qualified healthcare professional for medical decisions.

## 📄 License

Apache 2.0 (following HealthGPT-Pro's license)
