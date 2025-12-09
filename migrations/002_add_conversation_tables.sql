-- Create conversation_sessions table
CREATE TABLE conversation_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active'
);

-- Create index on user_id for conversation_sessions
CREATE INDEX ix_conversation_sessions_user_id ON conversation_sessions(user_id);

-- Create conversation_history table
CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    role VARCHAR(20) NOT NULL,
    intent VARCHAR(50),
    confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_conversation_history_session
        FOREIGN KEY (session_id)
        REFERENCES conversation_sessions(id)
        ON DELETE CASCADE
);

-- Create indexes for conversation_history
CREATE INDEX ix_conversation_history_user_id ON conversation_history(user_id);
CREATE INDEX ix_conversation_history_session_id ON conversation_history(session_id);
CREATE INDEX ix_conversation_history_created_at ON conversation_history(created_at);

-- Create user_preferences table
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    tone_preference VARCHAR(20) DEFAULT 'friendly',
    emoji_density VARCHAR(20) DEFAULT 'moderate',
    language VARCHAR(10) DEFAULT 'en',
    context_retention BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create index on user_id for user_preferences
CREATE INDEX ix_user_preferences_user_id ON user_preferences(user_id);

-- Create intent_logs table
CREATE TABLE intent_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    detected_intent VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    entities JSONB,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for intent_logs
CREATE INDEX ix_intent_logs_user_id ON intent_logs(user_id);
CREATE INDEX ix_intent_logs_created_at ON intent_logs(created_at);