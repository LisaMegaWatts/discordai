CREATE TABLE document_blobs (
    id SERIAL PRIMARY KEY,
    owner_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    data BYTEA NOT NULL,
    blob_metadata JSONB,
    document JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ix_document_blobs_owner_id ON document_blobs(owner_id);