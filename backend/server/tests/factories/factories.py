import pytest
import uuid
from backend.server.database.models import User, Session, Question, Answer, Feedback


@pytest.fixture
def user_factory():
    def make_user(email=None, is_admin=False):
        user_id = str(uuid.uuid4())
        email = email or f"user_{user_id[:8]}@example.com"
        User.create_or_update(user_id, email, is_admin)
        return user_id

    return make_user


@pytest.fixture
def session_factory(user_factory):
    def make_session(user_id=None):
        user_id = user_id or user_factory()
        return Session.create(user_id)

    return make_session


@pytest.fixture
def question_factory(session_factory, user_factory):
    def make_question(session_id=None, user_id=None, question_text="What is AI?"):
        user_id = user_id or user_factory()
        session_id = session_id or session_factory(user_id)
        return Question.create(session_id, user_id, question_text)

    return make_question


@pytest.fixture
def answer_factory(question_factory):
    def make_answer(
        question_id=None,
        answer_text="AI is artificial intelligence.",
        prompt="Explain AI",
        retrieved_chunks=None,
        response_time=1.0,
    ):
        question_id = question_id or question_factory()
        retrieved_chunks = retrieved_chunks or []
        return Answer.create(
            question_id, answer_text, prompt, retrieved_chunks, response_time
        )

    return make_answer


@pytest.fixture
def feedback_factory(user_factory, answer_factory):
    def make_feedback(user_id=None, answer_id=None, like=True, suggestion=None):
        user_id = user_id or user_factory()
        answer_id = answer_id or answer_factory()
        return Feedback.create_or_update(user_id, answer_id, like, suggestion)

    return make_feedback
