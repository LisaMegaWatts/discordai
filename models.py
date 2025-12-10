from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, Index
from sqlalchemy.sql import func
from db import Base

class FeatureRequest(Base):
    __tablename__ = "feature_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GeneratedImage(Base):
    __tablename__ = "generated_images"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    task_name = Column(String, nullable=False)
    run_at = Column(DateTime(timezone=True), nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ReflectionLog(Base):
    __tablename__ = "reflection_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConversationSessions(Base):
    __tablename__ = "conversation_sessions"
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    message_count = Column(Integer, default=0)
    status = Column(String(20), default="active")
    
    def __repr__(self):
        return f"<ConversationSession(id={self.id}, user_id={self.user_id}, status={self.status}, messages={self.message_count})>"

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    __table_args__ = (
        Index('ix_conversation_history_user_id', 'user_id'),
        Index('ix_conversation_history_session_id', 'session_id'),
        Index('ix_conversation_history_created_at', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), ForeignKey('conversation_sessions.id'), nullable=False)
    user_id = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    intent = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, session_id={self.session_id}, role={self.role}, intent={self.intent})>"

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    tone_preference = Column(String(20), default="friendly")  # friendly, professional, casual, enthusiastic
    emoji_density = Column(String(20), default="moderate")  # none, low, moderate, high
    language = Column(String(10), default="en")
    context_retention = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, tone={self.tone_preference}, emoji={self.emoji_density})>"

class IntentLogs(Base):
    __tablename__ = "intent_logs"
    __table_args__ = (
        Index('ix_intent_logs_user_id', 'user_id'),
        Index('ix_intent_logs_created_at', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    detected_intent = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    entities = Column(JSON, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<IntentLog(id={self.id}, user_id={self.user_id}, intent={self.detected_intent}, confidence={self.confidence})>"

class DocumentBlob(Base):
    __tablename__ = "document_blobs"
    id = Column(Integer, primary_key=True)
    owner_id = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    from sqlalchemy import LargeBinary
    data = Column(LargeBinary, nullable=False)  # Use LargeBinary for BYTEA
    blob_metadata = Column(JSON, nullable=True)
    document = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<DocumentBlob(id={self.id}, owner_id={self.owner_id}, name={self.name}, content_type={self.content_type})>"