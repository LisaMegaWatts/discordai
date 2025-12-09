from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

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