from backend.server.database.models import User, Question, Answer, Feedback

# USER MODEL TESTS


def test_user_create_and_get(user_factory):
    """Test creating a user and retrieving it."""
    user_id = user_factory(email="alice@example.com", is_admin=True)
    user = User.get(user_id)
    assert user is not None
    assert user["email"] == "alice@example.com"
    assert user["is_admin"] == 1


def test_user_update(user_factory):
    """Test updating a user's email and admin status."""
    user_id = user_factory(email="bob@example.com", is_admin=False)
    User.create_or_update(user_id, "bob2@example.com", True)
    user = User.get(user_id)
    assert user["email"] == "bob2@example.com"
    assert user["is_admin"] == 1


def test_user_increment_question_count(user_factory):
    """Test incrementing a user's question count."""
    user_id = user_factory()
    quota_left = User.increment_question_count(user_id)
    assert quota_left >= 0


# SESSION MODEL TESTS


def test_session_create_and_get(session_factory, user_factory):
    """Test creating a session and verifying it via a question."""
    user_id = user_factory()
    session_id = session_factory(user_id=user_id)
    # No direct get, but we can create and use in question
    question_id = Question.create(session_id, user_id, "Test Q?")
    question = Question.get(question_id)
    assert question["session_id"] == session_id


# QUESTION MODEL TESTS


def test_question_create_get_list_search(question_factory):
    """Test creating, getting, listing, and searching questions."""
    question_id = question_factory(question_text="What is Python?")
    question = Question.get(question_id)
    assert question is not None
    assert question["question_text"] == "What is Python?"
    # List
    questions = Question.list_questions()
    assert any(q["question_id"] == question_id for q in questions)
    # Search
    results = Question.search_questions("Python")
    assert any(q["question_id"] == question_id for q in results)


def test_question_delete(question_factory):
    """Test deleting a question."""
    question_id = question_factory()
    deleted = Question.delete(question_id)
    assert deleted
    assert Question.get(question_id) is None


# ANSWER MODEL TESTS


def test_answer_create_get_list_search(answer_factory, question_factory):
    """Test creating, getting, listing, and searching answers."""
    answer_id = answer_factory(
        answer_text="42",
        prompt="What is the answer?",
        retrieved_chunks=[{"chunk": "test"}],
    )
    answer = Answer.get(answer_id)
    assert answer is not None
    assert answer["answer_text"] == "42"
    # List
    answers = Answer.list_answers()
    assert any(a["answer_id"] == answer_id for a in answers)
    # Search
    results = Answer.search_answers("42")
    assert any(a["answer_id"] == answer_id for a in results)


def test_answer_delete(answer_factory):
    """Test deleting an answer."""
    answer_id = answer_factory()
    deleted = Answer.delete(answer_id)
    assert deleted
    assert Answer.get(answer_id) is None


# FEEDBACK MODEL TESTS


def test_feedback_create_update_get_delete(
    feedback_factory, user_factory, answer_factory
):
    """Test creating, updating, getting, and deleting feedback."""
    user_id = user_factory()
    answer_id = answer_factory()
    Feedback.create_or_update(user_id, answer_id, like=True, suggestion="Good!")
    feedback = Feedback.get(answer_id, user_id)
    assert feedback is not None
    assert feedback["like"] == 1
    assert feedback["suggestion"] == "Good!"
    # Update
    Feedback.create_or_update(user_id, answer_id, like=False, suggestion="Bad!")
    feedback = Feedback.get(answer_id, user_id)
    assert feedback["like"] == 0
    assert feedback["suggestion"] == "Bad!"
    # Delete
    deleted = Feedback.delete(answer_id, user_id)
    assert deleted
    assert Feedback.get(answer_id, user_id) is None


def test_feedback_list(feedback_factory):
    """Test listing feedback entries."""
    feedback_id = feedback_factory()
    feedbacks = Feedback.list_feedback()
    assert any(f["feedback_id"] == feedback_id for f in feedbacks)
