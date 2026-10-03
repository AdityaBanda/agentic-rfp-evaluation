CREATE TABLE IF NOT EXISTS evaluation_criteria (
    criterion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    weight REAL NOT NULL,
    max_score REAL NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS rfp_runs (
    rfp_run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    llm_provider TEXT,
    llm_model TEXT,
    demo_mode INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS supplier_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfp_run_id TEXT NOT NULL REFERENCES rfp_runs(rfp_run_id),
    supplier_name TEXT NOT NULL,
    submission_date TEXT NOT NULL,
    experience_rating REAL NOT NULL,
    absolute_score REAL,
    ppi REAL,
    final_rank INTEGER,
    tie_break_notes TEXT,
    status TEXT NOT NULL,
    extraction_warning TEXT,
    result_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS supplier_criterion_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfp_run_id TEXT NOT NULL REFERENCES rfp_runs(rfp_run_id),
    supplier_name TEXT NOT NULL,
    criterion_id INTEGER NOT NULL,
    criterion_name TEXT NOT NULL,
    score REAL NOT NULL,
    max_score REAL NOT NULL,
    weight REAL NOT NULL,
    benchmark REAL,
    gap REAL,
    relative_performance REAL,
    evidence TEXT,
    justification TEXT,
    validation_status TEXT NOT NULL DEFAULT 'OK'
);

CREATE TABLE IF NOT EXISTS run_warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfp_run_id TEXT NOT NULL REFERENCES rfp_runs(rfp_run_id),
    supplier_name TEXT,
    warning_type TEXT NOT NULL,
    criterion_id INTEGER,
    original_value TEXT,
    normalized_value TEXT,
    message TEXT
);

CREATE INDEX IF NOT EXISTS idx_supplier_results_run ON supplier_results(rfp_run_id);
CREATE INDEX IF NOT EXISTS idx_criterion_results_run ON supplier_criterion_results(rfp_run_id);
CREATE INDEX IF NOT EXISTS idx_warnings_run ON run_warnings(rfp_run_id);
