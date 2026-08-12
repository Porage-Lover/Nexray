"""
Encrypted SQLite database for storing clinical reports locally.
Uses Fernet symmetric encryption for at-rest patient data protection.
"""
import sqlite3
import os
import datetime
from cryptography.fernet import Fernet


def _get_or_create_key(data_dir: str) -> bytes:
    """
    Looks for .encryption_key file in data_dir.
    If not found, generates a new Fernet key and saves it.

    Args:
        data_dir: Directory to store/find the encryption key.

    Returns:
        The Fernet key as bytes.
    """
    key_path = os.path.join(data_dir, ".encryption_key")
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return f.read().strip()
    else:
        key = Fernet.generate_key()
        os.makedirs(data_dir, exist_ok=True)
        with open(key_path, "wb") as f:
            f.write(key)
        return key


def _encrypt(data: str, key: bytes) -> str:
    """
    Encrypts a string using Fernet, returns base64-encoded ciphertext as string.

    Args:
        data: Plaintext string to encrypt.
        key: Fernet key bytes.

    Returns:
        Encrypted ciphertext as a string, or None if input is None.
    """
    if data is None:
        return None
    f = Fernet(key)
    return f.encrypt(data.encode("utf-8")).decode("utf-8")


def _decrypt(token: str, key: bytes) -> str:
    """
    Decrypts a Fernet token back to plaintext string.

    Args:
        token: Encrypted ciphertext string.
        key: Fernet key bytes.

    Returns:
        Decrypted plaintext string, or None if input is None.
    """
    if token is None:
        return None
    f = Fernet(key)
    return f.decrypt(token.encode("utf-8")).decode("utf-8")


def init_database(db_path: str = "./data/reports.db") -> None:
    """
    Creates the data directory if needed and initializes the SQLite database
    with the reports table.

    Args:
        db_path: Path to the SQLite database file.
    """
    data_dir = os.path.dirname(db_path)
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)

    # Initialize encryption key
    _get_or_create_key(data_dir if data_dir else ".")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            patient_name TEXT,
            modality TEXT,
            clinical_context TEXT,
            findings TEXT,
            differential_diagnosis TEXT,
            recommended_actions TEXT,
            clinical_notes TEXT,
            narrative TEXT,
            raw_output TEXT,
            image_filename TEXT,
            inference_time REAL,
            token_count INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_report(
    db_path: str,
    patient_id: str,
    patient_name: str,
    modality: str,
    clinical_context: str,
    report_data: dict,
    image_filename: str,
    inference_time: float,
    token_count: int,
) -> int:
    """
    Encrypts sensitive fields and stores the report in the database.

    Args:
        db_path: Path to the SQLite database file.
        patient_id: Patient identifier string.
        patient_name: Patient name string.
        modality: Imaging modality (e.g., "X-ray").
        clinical_context: Clinical context provided by clinician.
        report_data: Dict with keys: findings, differential_diagnosis,
                     recommended_actions, clinical_notes, narrative, raw.
        image_filename: Name of the uploaded image file.
        inference_time: Model inference time in seconds.
        token_count: Approximate number of tokens generated.

    Returns:
        The inserted row ID.
    """
    data_dir = os.path.dirname(db_path)
    key = _get_or_create_key(data_dir if data_dir else ".")

    enc_patient_id = _encrypt(patient_id, key)
    enc_patient_name = _encrypt(patient_name, key)
    enc_clinical_context = _encrypt(clinical_context, key)
    enc_findings = _encrypt(report_data.get("findings", ""), key)
    enc_differential_diagnosis = _encrypt(report_data.get("differential_diagnosis", ""), key)
    enc_recommended_actions = _encrypt(report_data.get("recommended_actions", ""), key)
    enc_clinical_notes = _encrypt(report_data.get("clinical_notes", ""), key)
    enc_narrative = _encrypt(report_data.get("narrative", ""), key)
    enc_raw_output = _encrypt(report_data.get("raw", ""), key)

    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO reports (
            patient_id, patient_name, modality, clinical_context,
            findings, differential_diagnosis, recommended_actions,
            clinical_notes, narrative, raw_output, image_filename,
            inference_time, token_count, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            enc_patient_id,
            enc_patient_name,
            modality,
            enc_clinical_context,
            enc_findings,
            enc_differential_diagnosis,
            enc_recommended_actions,
            enc_clinical_notes,
            enc_narrative,
            enc_raw_output,
            image_filename,
            inference_time,
            token_count,
            created_at,
        ),
    )

    row_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return row_id


def get_all_reports(db_path: str = "./data/reports.db") -> list[dict]:
    """
    Returns all reports, decrypted, sorted by created_at DESC.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A list of dicts, each representing a decrypted report.
    """
    if not os.path.exists(db_path):
        return []

    data_dir = os.path.dirname(db_path)
    key = _get_or_create_key(data_dir if data_dir else ".")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    reports = []
    for row in rows:
        report = dict(row)
        report["patient_id"] = _decrypt(report["patient_id"], key)
        report["patient_name"] = _decrypt(report["patient_name"], key)
        report["clinical_context"] = _decrypt(report["clinical_context"], key)
        report["findings"] = _decrypt(report["findings"], key)
        report["differential_diagnosis"] = _decrypt(report["differential_diagnosis"], key)
        report["recommended_actions"] = _decrypt(report["recommended_actions"], key)
        report["clinical_notes"] = _decrypt(report["clinical_notes"], key)
        report["narrative"] = _decrypt(report["narrative"], key)
        report["raw_output"] = _decrypt(report["raw_output"], key)
        reports.append(report)

    return reports


def get_report_by_id(db_path: str, report_id: int) -> dict | None:
    """
    Returns a single decrypted report by its ID.

    Args:
        db_path: Path to the SQLite database file.
        report_id: The integer ID of the report.

    Returns:
        A dict representing the decrypted report, or None if not found.
    """
    if not os.path.exists(db_path):
        return None

    data_dir = os.path.dirname(db_path)
    key = _get_or_create_key(data_dir if data_dir else ".")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    report = dict(row)
    report["patient_id"] = _decrypt(report["patient_id"], key)
    report["patient_name"] = _decrypt(report["patient_name"], key)
    report["clinical_context"] = _decrypt(report["clinical_context"], key)
    report["findings"] = _decrypt(report["findings"], key)
    report["differential_diagnosis"] = _decrypt(report["differential_diagnosis"], key)
    report["recommended_actions"] = _decrypt(report["recommended_actions"], key)
    report["clinical_notes"] = _decrypt(report["clinical_notes"], key)
    report["narrative"] = _decrypt(report["narrative"], key)
    report["raw_output"] = _decrypt(report["raw_output"], key)

    return report
