from models import FeatureRequest, GeneratedImage, ScheduledTask, ReflectionLog, ConversationSessions, ConversationHistory, UserPreferences, IntentLogs
from sqlalchemy.future import select
from sqlalchemy import func
import uuid
from typing import Optional

# FeatureRequest CRUD
async def create_feature_request(session, user_id, title, description):
    fr = FeatureRequest(user_id=user_id, title=title, description=description)
    session.add(fr)
    await session.commit()
    await session.refresh(fr)
    return fr

async def get_feature_request(session, fr_id):
    result = await session.execute(select(FeatureRequest).where(FeatureRequest.id == fr_id))
    return result.scalar_one_or_none()

async def update_feature_request(session, fr_id, **kwargs):
    fr = await get_feature_request(session, fr_id)
    if fr:
        for key, value in kwargs.items():
            setattr(fr, key, value)
        await session.commit()
        await session.refresh(fr)
    return fr

async def delete_feature_request(session, fr_id):
    fr = await get_feature_request(session, fr_id)
    if fr:
        await session.delete(fr)
        await session.commit()
    return fr

# GeneratedImage CRUD
async def create_generated_image(session, user_id, image_url, prompt):
    gi = GeneratedImage(user_id=user_id, image_url=image_url, prompt=prompt)
    session.add(gi)
    await session.commit()
    await session.refresh(gi)
    return gi

async def get_generated_image(session, gi_id):
    result = await session.execute(select(GeneratedImage).where(GeneratedImage.id == gi_id))
    return result.scalar_one_or_none()

async def update_generated_image(session, gi_id, **kwargs):
    gi = await get_generated_image(session, gi_id)
    if gi:
        for key, value in kwargs.items():
            setattr(gi, key, value)
        await session.commit()
        await session.refresh(gi)
    return gi

async def delete_generated_image(session, gi_id):
    gi = await get_generated_image(session, gi_id)
    if gi:
        await session.delete(gi)
        await session.commit()
    return gi

# ScheduledTask CRUD
async def create_scheduled_task(session, user_id, task_name, run_at):
    st = ScheduledTask(user_id=user_id, task_name=task_name, run_at=run_at)
    session.add(st)
    await session.commit()
    await session.refresh(st)
    return st

async def get_scheduled_task(session, st_id):
    result = await session.execute(select(ScheduledTask).where(ScheduledTask.id == st_id))
    return result.scalar_one_or_none()

async def update_scheduled_task(session, st_id, **kwargs):
    st = await get_scheduled_task(session, st_id)
    if st:
        for key, value in kwargs.items():
            setattr(st, key, value)
        await session.commit()
        await session.refresh(st)
    return st

async def delete_scheduled_task(session, st_id):
    st = await get_scheduled_task(session, st_id)
    if st:
        await session.delete(st)
        await session.commit()
    return st

# ReflectionLog CRUD
async def create_reflection_log(session, user_id, content):
    rl = ReflectionLog(user_id=user_id, content=content)
    session.add(rl)
    await session.commit()
    await session.refresh(rl)
    return rl

async def get_reflection_log(session, rl_id):
    result = await session.execute(select(ReflectionLog).where(ReflectionLog.id == rl_id))
    return result.scalar_one_or_none()

async def update_reflection_log(session, rl_id, **kwargs):
    rl = await get_reflection_log(session, rl_id)
    if rl:
        for key, value in kwargs.items():
            setattr(rl, key, value)
        await session.commit()
        await session.refresh(rl)
    return rl

async def delete_reflection_log(session, rl_id):
    rl = await get_reflection_log(session, rl_id)
    if rl:
        await session.delete(rl)
        await session.commit()
    return rl

# ConversationSessions CRUD
async def create_conversation_session(session, user_id: str, session_id: Optional[str] = None) -> ConversationSessions:
    if session_id is None:
        session_id = str(uuid.uuid4())
    cs = ConversationSessions(id=session_id, user_id=user_id)
    session.add(cs)
    await session.commit()
    await session.refresh(cs)
    return cs

async def get_conversation_session(session, session_id: str) -> Optional[ConversationSessions]:
    result = await session.execute(select(ConversationSessions).where(ConversationSessions.id == session_id))
    return result.scalar_one_or_none()

async def get_active_session_for_user(session, user_id: str) -> Optional[ConversationSessions]:
    result = await session.execute(
        select(ConversationSessions)
        .where(ConversationSessions.user_id == user_id)
        .where(ConversationSessions.status == "active")
        .order_by(ConversationSessions.last_active.desc())
    )
    return result.scalars().first()

async def update_session_activity(session, session_id: str, message_count_increment: int = 1) -> Optional[ConversationSessions]:
    cs = await get_conversation_session(session, session_id)
    if cs:
        cs.message_count += message_count_increment
        cs.last_active = func.now()
        await session.commit()
        await session.refresh(cs)
    return cs

async def end_conversation_session(session, session_id: str) -> Optional[ConversationSessions]:
    cs = await get_conversation_session(session, session_id)
    if cs:
        cs.status = "ended"
        await session.commit()
        await session.refresh(cs)
    return cs

# ConversationHistory CRUD
async def create_conversation_message(
    session,
    session_id: str,
    user_id: str,
    message: str,
    role: str,
    intent: Optional[str] = None,
    confidence: Optional[float] = None
) -> ConversationHistory:
    ch = ConversationHistory(
        session_id=session_id,
        user_id=user_id,
        message=message,
        role=role,
        intent=intent,
        confidence=confidence
    )
    session.add(ch)
    await session.commit()
    await session.refresh(ch)
    return ch

async def get_conversation_history(session, session_id: str, limit: int = 50) -> list[ConversationHistory]:
    result = await session.execute(
        select(ConversationHistory)
        .where(ConversationHistory.session_id == session_id)
        .order_by(ConversationHistory.created_at.asc())
        .limit(limit)
    )
    return result.scalars().all()

async def get_user_recent_messages(session, user_id: str, limit: int = 10) -> list[ConversationHistory]:
    result = await session.execute(
        select(ConversationHistory)
        .where(ConversationHistory.user_id == user_id)
        .order_by(ConversationHistory.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

# UserPreferences CRUD
async def create_user_preferences(session, user_id: str, **kwargs) -> UserPreferences:
    up = UserPreferences(user_id=user_id, **kwargs)
    session.add(up)
    await session.commit()
    await session.refresh(up)
    return up

async def get_user_preferences(session, user_id: str) -> UserPreferences:
    result = await session.execute(select(UserPreferences).where(UserPreferences.user_id == user_id))
    up = result.scalar_one_or_none()
    if up is None:
        # Auto-create with defaults if not exists
        up = await create_user_preferences(session, user_id)
    return up

async def update_user_preferences(session, user_id: str, **kwargs) -> Optional[UserPreferences]:
    up = await get_user_preferences(session, user_id)
    if up:
        for key, value in kwargs.items():
            setattr(up, key, value)
        await session.commit()
        await session.refresh(up)
    return up

# IntentLogs CRUD
async def create_intent_log(
    session,
    user_id: str,
    message: str,
    detected_intent: str,
    confidence: float,
    entities: Optional[dict] = None,
    processing_time_ms: Optional[int] = None
) -> IntentLogs:
    il = IntentLogs(
        user_id=user_id,
        message=message,
        detected_intent=detected_intent,
        confidence=confidence,
        entities=entities,
        processing_time_ms=processing_time_ms
    )
    session.add(il)
    await session.commit()
    await session.refresh(il)
    return il

async def get_intent_logs(session, user_id: Optional[str] = None, limit: int = 100) -> list[IntentLogs]:
    query = select(IntentLogs).order_by(IntentLogs.created_at.desc()).limit(limit)
    if user_id is not None:
        query = query.where(IntentLogs.user_id == user_id)
    result = await session.execute(query)
    return result.scalars().all()

async def get_intent_accuracy_stats(session) -> dict:
    # Get average confidence by intent type
    result = await session.execute(
        select(
            IntentLogs.detected_intent,
            func.avg(IntentLogs.confidence).label('avg_confidence'),
            func.count(IntentLogs.id).label('count')
        )
        .group_by(IntentLogs.detected_intent)
    )
    stats = {}
    for row in result:
        stats[row.detected_intent] = {
            'average_confidence': float(row.avg_confidence),
            'count': row.count
        }
    return stats