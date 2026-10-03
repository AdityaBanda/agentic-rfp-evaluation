import json

from src.agents.evaluation_agent import EvaluationAgent
from src.llm.demo_provider import DemoLLMProvider
from src.models.schemas import CriterionDefinition


def _criteria():
    return [
        CriterionDefinition(
            criterion_id=1,
            name="Technical Capability",
            description="Architecture, integrations, scalability and technical fit.",
            weight=30,
            max_score=10,
        ),
        CriterionDefinition(
            criterion_id=2,
            name="Security & Compliance",
            description="Controls, certifications, privacy and auditability.",
            weight=20,
            max_score=10,
        ),
    ]


def test_demo_provider_parses_real_prompt_and_covers_every_criterion():
    """Regression test: the demo provider parses the exact prompt format built by
    EvaluationAgent. If the prompt template changes, this must be kept in sync —
    otherwise the demo provider silently returns empty criteria and every score
    defaults to 0 via ValidationTool's MISSING_CRITERION path.
    """
    agent = EvaluationAgent(DemoLLMProvider())
    proposal_text = (
        "Our architecture uses a scalable microservices platform with strong integrations. "
        "We maintain SOC 2 certification and strict access controls for compliance and auditability."
    )
    user_prompt = agent.build_user_prompt("Test Supplier", proposal_text, _criteria())

    raw = DemoLLMProvider().generate_json("", user_prompt)
    parsed = json.loads(raw)

    assert parsed["supplier_name"] == "Test Supplier"
    assert {c["criterion_id"] for c in parsed["criteria"]} == {1, 2}
    for c in parsed["criteria"]:
        assert 0 <= c["score"] <= c["max_score"]
    # Keyword-rich text should score meaningfully above the floor, not default to 0.
    assert any(c["score"] > 1 for c in parsed["criteria"])
