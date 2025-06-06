-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    is_admin BOOLEAN NOT NULL DEFAULT 0,
    question_count INTEGER NOT NULL DEFAULT 0,
    last_question_reset DATE NOT NULL
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Questions table
CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Answers table
CREATE TABLE IF NOT EXISTS answers (
    answer_id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    prompt TEXT NOT NULL,
    retrieved_chunks TEXT,
    response_time FLOAT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    answer_id TEXT NOT NULL,
    like BOOLEAN NOT NULL,
    suggestion TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (answer_id) REFERENCES answers(answer_id),
    UNIQUE(user_id, answer_id)
);
