"""Default evaluation criteria seeded into a fresh database.

These are configuration data, not prompt content: the LLM never receives
hard-coded criteria — it only ever sees whatever is currently active in
SQLite, fetched at evaluation time.
"""

DEFAULT_CRITERIA = [
    {
        "name": "Technical Capability",
        "description": "Architecture, integrations, scalability and technical fit.",
        "weight": 30,
        "max_score": 10,
    },
    {
        "name": "Implementation Plan",
        "description": "Timeline, milestones, staffing and risk plan.",
        "weight": 20,
        "max_score": 10,
    },
    {
        "name": "Commercial Value",
        "description": "Pricing clarity, total cost and assumptions.",
        "weight": 20,
        "max_score": 10,
    },
    {
        "name": "Security & Compliance",
        "description": "Controls, certifications, privacy and auditability.",
        "weight": 20,
        "max_score": 10,
    },
    {
        "name": "Support & Experience",
        "description": "Support model, similar projects and references.",
        "weight": 10,
        "max_score": 10,
    },
]
