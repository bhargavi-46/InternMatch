"""Coaching features with the LLM replaced by canned replies."""

from fastapi.testclient import TestClient

from app import coach
from app.main import app
from app.models import Job

JOB = Job(id=7, title="ML Intern", company="Acme", location="Pune, India", description="PyTorch, SQL and DSA.")


class FakeLLM:
    def __init__(self, reply):
        self.reply = reply
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return self.reply


def test_prep_plan_links_come_from_the_curated_list(monkeypatch):
    draft = coach._PlanDraft(
        summary="Tests ML basics.",
        topics=[
            coach.PrepTopic(name="Bias-variance", category="ml_fundamentals", why="Core ML", priority="high",
                            student_knows=False),
            coach.PrepTopic(name="Acme's products", category="domain", why="Company", priority="low",
                            student_knows=False),
        ],
        interview_questions=[coach.InterviewQuestion(question="What is overfitting?", kind="technical", hint="...")],
        week_plan=[f"Day {i}" for i in range(1, 9)],
    )
    monkeypatch.setattr(coach, "structured_llm", lambda schema: FakeLLM(draft))
    plan = coach.prep_plan(None, JOB)
    assert plan.topics[0].resources == coach.RESOURCES["ml_fundamentals"]
    assert plan.topics[1].resources == []
    assert len(plan.week_plan) == 7


def test_every_category_has_resources_entry():
    assert set(coach.RESOURCES) == set(coach.Category.__args__)
    assert all(r.url.startswith("https://") for rs in coach.RESOURCES.values() for r in rs)


def test_quiz_drops_malformed_questions_and_keeps_the_right_answer(monkeypatch):
    good = coach.QuizQuestion(topic="SQL", question="Which clause filters groups?",
                              options=["WHERE", "HAVING", "ORDER BY", "LIMIT"], answer_index=1, explanation="...")
    three_options = good.model_copy(update={"options": ["A", "B", "C"]})
    bad_index = good.model_copy(update={"answer_index": 4})
    duplicate = good.model_copy(update={"options": ["A", "A", "B", "C"]})
    quiz = coach.Quiz(questions=[good] * 20 + [three_options, bad_index, duplicate])
    monkeypatch.setattr(coach, "structured_llm", lambda schema: FakeLLM(quiz))
    result = coach.make_quiz(["SQL"], [], [], 10)
    assert len(result.questions) == 10
    for q in result.questions:
        assert sorted(q.options) == sorted(good.options)
        assert q.options[q.answer_index] == "HAVING"


def test_interview_ends_after_the_last_answer(monkeypatch):
    fake = FakeLLM(type("Reply", (), {"content": "Next question?"})())
    monkeypatch.setattr(coach, "get_llm", lambda: fake)
    reply, done = coach.interview_reply(None, JOB, [])
    assert reply == "Next question?" and not done
    assert fake.messages[-1] == ("human", "Hi, I'm ready to start.")
    turns = []
    for i in range(coach.INTERVIEW_QUESTIONS):
        turns += [coach.InterviewTurn(role="interviewer", content=f"Q{i}"),
                  coach.InterviewTurn(role="candidate", content=f"A{i}")]
    _, done = coach.interview_reply(None, JOB, turns)
    assert done
    assert fake.messages[1] == ("ai", "Q0") and fake.messages[2] == ("human", "A0")


def test_quiz_endpoint_validates_input():
    client = TestClient(app)
    assert client.post("/quiz", json={"topics": []}).status_code == 422
    assert client.post("/quiz", json={"topics": ["SQL"], "count": 50}).status_code == 422


def test_language_links_match_the_topic():
    topic = coach.PrepTopic(name="Java fundamentals", category="programming_language", why="", priority="high",
                            student_knows=True)
    assert [r.title for r in coach.resources_for(topic)] == ["Learn Java (dev.java)"]
    topic = topic.model_copy(update={"name": "JavaScript closures"})
    assert [r.title for r in coach.resources_for(topic)] == ["javascript.info"]
    topic = topic.model_copy(update={"name": "Clean code"})
    assert len(coach.resources_for(topic)) == 4  # no language named: show them all
