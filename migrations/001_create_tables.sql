CREATE TABLE feature_requests (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE generated_images (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    image_url VARCHAR NOT NULL,
    prompt TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scheduled_tasks (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    task_name VARCHAR NOT NULL,
    run_at TIMESTAMPTZ NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reflection_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);