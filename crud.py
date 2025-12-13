import asyncio
import logging
from typing import Optional

from db import AsyncSessionLocal
from models import (
    ConversationHistory,
    ConversationSessions,
    DocumentBlob,
    FeatureRequest,
    GeneratedImage,
    IntentLogs,
    ReflectionLog,
    ScheduledTask,
    UserPreferences,
)
from sqlalchemy.future import select
from sqlalchemy import func
import uuid


# Utility to check if event loop is running and not closed
def is_event_loop_running():
    """Check if event loop is running and not closed."""
    try:
        loop = asyncio.get_running_loop()
        return not loop.is_closed()
    except RuntimeError:
        return False


# FeatureRequest CRUD
async def create_feature_request(session, user_id, title, description):
    """Create a feature request."""
    from discord_bot import is_event_loop_running, is_shutting_down
    if is_shutting_down() or not is_event_loop_running():
        logging.getLogger(__name__).warning(
            "Skipping DB operation in create_feature_request: shutdown or "
            "closed event loop."
        )
        return None
    fr = FeatureRequest(user_id=user_id, title=title, description=description)
    session.add(fr)
    await session.commit()
    await session.refresh(fr)
    return fr


async def get_feature_request(session, fr_id):
    """Get a feature request by ID."""
    result = await session.execute(
        select(FeatureRequest).where(FeatureRequest.id == fr_id)
    )
    return result.scalar_one_or_none()


async def update_feature_request(session, fr_id, **kwargs):
    """Update a feature request."""
    result = await session.execute(
        select(FeatureRequest).where(FeatureRequest.id == fr_id)
    )
    fr = result.scalar_one_or_none()
    if fr:
        for key, value in kwargs.items():
            setattr(fr, key, value)
        await session.commit()
        await session.refresh(fr)
    return fr


async def delete_feature_request(session, fr_id):
    """Delete a feature request."""
    fr = await get_feature_request(session, fr_id)
    if fr:
        await session.delete(fr)
        await session.commit()
    return fr


# GeneratedImage CRUD
async def create_generated_image(session, user_id, image_url, prompt):
    """Create a generated image."""
    from discord_bot import is_event_loop_running, is_shutting_down
    if is_shutting_down() or not is_event_loop_running():
        logging.getLogger(__name__).warning(
            "Skipping DB operation in create_generated_image: shutdown or "
            "closed event loop."
        )
        return None
    gi = GeneratedImage(user_id=user_id, image_url=image_url, prompt=prompt)
    session.add(gi)
    await session.commit()
    await session.refresh(gi)
    return gi


async def get_generated_image(session, gi_id):
    """Get a generated image by ID."""
    result = await session.execute(
        select(GeneratedImage).where(GeneratedImage.id == gi_id)
    )
    return result.scalar_one_or_none()


async def update_generated_image(gi_id, **kwargs):
    """Update a generated image."""
    async with AsyncSessionLocal() as session:
        gi = await get_generated_image(session, gi_id)
        if gi:
            for key, value in kwargs.items():
                setattr(gi, key, value)
            await session.commit()
            await session.refresh(gi)
        return gi


async def delete_generated_image(gi_id):
    """Delete a generated image."""
    async with AsyncSessionLocal() as session:
        gi = await get_generated_image(session, gi_id)
        if gi:
            await session.delete(gi)
            await session.commit()
        return gi


# ScheduledTask CRUD
async def create_scheduled_task(user_id, task_name, run_at):
    """Create a scheduled task."""
    try:
        async with AsyncSessionLocal() as session:
            st = ScheduledTask(
                user_id=user_id,
                task_name=task_name,
                run_at=run_at
            )
            session.add(st)
            await session.commit()
            await session.refresh(st)
            return st
    except (RuntimeError, AttributeError) as e:
        logging.getLogger(__name__).warning(
            f"Skipping DB operation in create_scheduled_task: {e}"
        )
        return None


async def get_scheduled_task(st_id):
    """Get a scheduled task by ID."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ScheduledTask).where(ScheduledTask.id == st_id)
            )
            return result.scalar_one_or_none()
    except (RuntimeError, AttributeError) as e:
        logging.getLogger(__name__).warning(
            f"Skipping DB operation in get_scheduled_task: {e}"
        )
        return None


async def update_scheduled_task(st_id, **kwargs):
    """Update a scheduled task."""
    try:
        async with AsyncSessionLocal() as session:
            st = await get_scheduled_task(st_id)
            if st:
                for key, value in kwargs.items():
                    setattr(st, key, value)
                await session.commit()
                await session.refresh(st)
            return st
    except (RuntimeError, AttributeError) as e:
        logging.getLogger(__name__).warning(
            f"Skipping DB operation in update_scheduled_task: {e}"
        )
        return None


async def delete_scheduled_task(st_id):
    """Delete a scheduled task."""
    try:
        async with AsyncSessionLocal() as session:
            st = await get_scheduled_task(st_id)
            if st:
                await session.delete(st)
                await session.commit()
            return st
    except (RuntimeError, AttributeError) as e:
        logging.getLogger(__name__).warning(
            f"Skipping DB operation in delete_scheduled_task: {e}"
        )
        return None


# ReflectionLog CRUD
async def create_reflection_log(user_id, content):
    """Create a reflection log."""
    async with AsyncSessionLocal() as session:
        rl = ReflectionLog(user_id=user_id, content=content)
        session.add(rl)
        await session.commit()
        await session.refresh(rl)
        return rl


async def get_reflection_log(rl_id):
    """Get a reflection log by ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ReflectionLog).where(ReflectionLog.id == rl_id)
        )
        return result.scalar_one_or_none()


async def update_reflection_log(rl_id, **kwargs):
    """Update a reflection log."""
    async with AsyncSessionLocal() as session:
        rl = await get_reflection_log(rl_id)
        if rl:
            for key, value in kwargs.items():
                setattr(rl, key, value)
            await session.commit()
            await session.refresh(rl)
        return rl


async def delete_reflection_log(rl_id):
    """Delete a reflection log."""
    async with AsyncSessionLocal() as session:
        rl = await get_reflection_log(rl_id)
        if rl:
            await session.delete(rl)
            await session.commit()
        return rl


# ConversationSessions CRUD
async def create_conversation_session(
    user_id: str, session_id: Optional[str] = None
) -> ConversationSessions:
    """Create a conversation session."""
    logger = logging.getLogger(__name__)
    async with AsyncSessionLocal() as session:
        if session_id is None:
            session_id = str(uuid.uuid4())
        cs = ConversationSessions(id=session_id, user_id=user_id)
        session.add(cs)
        await session.commit()
        await session.refresh(cs)
        logger.info(
            f"[END] create_conversation_session: user_id={user_id}, "
            f"created_session_id={cs.id}"
        )
        return cs


async def get_conversation_session(
    session_id: str
) -> Optional[ConversationSessions]:
    """Get a conversation session by ID."""
    logger = logging.getLogger(__name__)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ConversationSessions).where(
                ConversationSessions.id == session_id
            )
        )
        obj = result.scalar_one_or_none()
        logger.info(
            f"[END] get_conversation_session: target_session_id={session_id}, "
            f"found={obj is not None}"
        )
        return obj


async def get_active_session_for_user(
    user_id: str
) -> Optional[ConversationSessions]:
    """Get active conversation session for a user."""
    logger = logging.getLogger(__name__)
    from discord_bot import is_shutting_down, is_event_loop_running
    if is_shutting_down() or not is_event_loop_running():
        logger.warning(
            f"Shutdown or closed event loop. Skipping "
            f"get_active_session_for_user for user {user_id}."
        )
        return None
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ConversationSessions)
            .where(ConversationSessions.user_id == user_id)
            .where(ConversationSessions.status == "active")
            .order_by(ConversationSessions.last_active.desc())
        )
        obj = result.scalars().first()
        logger.info(
            f"[END] get_active_session_for_user: user_id={user_id}, "
            f"found={obj is not None}"
        )
        return obj


async def update_session_activity(
    session_id: str, message_count_increment: int = 1
) -> Optional[ConversationSessions]:
    """Update session activity."""
    logger = logging.getLogger(__name__)
    async with AsyncSessionLocal() as session:
        try:
            cs = await get_conversation_session(session_id)
            if cs:
                cs.message_count += message_count_increment
                cs.last_active = func.now()
                session.add(cs)
                await session.commit()
                await session.refresh(cs)
            logger.info(
                f"[END] update_session_activity: "
                f"target_session_id={session_id}, updated={cs is not None}"
            )
            return cs
        except (RuntimeError, AttributeError) as e:
            logger.warning(
                f"Skipping DB operation in update_session_activity: {e}"
            )
            return None


async def end_conversation_session(
    session_id: str
) -> Optional[ConversationSessions]:
    """End a conversation session."""
    logger = logging.getLogger(__name__)
    async with AsyncSessionLocal() as session:
        cs = await get_conversation_session(session_id)
        if cs:
            cs.status = "ended"
            session.add(cs)
            await session.commit()
            await session.refresh(cs)
        logger.info(
            f"[END] end_conversation_session: target_session_id={session_id}, "
            f"ended={cs is not None}"
        )
        return cs


# ConversationHistory CRUD
async def create_conversation_message(
    session_id: str,
    user_id: str,
    message: str,
    role: str,
    intent: Optional[str] = None,
    confidence: Optional[float] = None
) -> ConversationHistory:
    """Create a conversation message."""
    logger = logging.getLogger(__name__)
    async with AsyncSessionLocal() as session:
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
        logger.info(
            f"[END] create_conversation_message: session_id={session_id}, "
            f"user={user_id}, role={role}, message_id={ch.id}"
        )
        return ch


async def get_conversation_history(
    session_id: str, limit: int = 50
) -> list[ConversationHistory]:
    """Get conversation history for a session."""
    logger = logging.getLogger(__name__)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ConversationHistory)
            .where(ConversationHistory.session_id == session_id)
            .order_by(ConversationHistory.created_at.asc())
            .limit(limit)
        )
        objs = result.scalars().all()
        logger.info(
            f"[END] get_conversation_history: session_id={session_id}, "
            f"limit={limit}, count={len(objs)}"
        )
        return objs


async def get_user_recent_messages(
    user_id: str, limit: int = 10
) -> list[ConversationHistory]:
    """Get recent messages for a user."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ConversationHistory)
            .where(ConversationHistory.user_id == user_id)
            .order_by(ConversationHistory.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


# UserPreferences CRUD
async def create_user_preferences(user_id: str, **kwargs) -> UserPreferences:
    """Create user preferences."""
    async with AsyncSessionLocal() as session:
        up = UserPreferences(user_id=user_id, **kwargs)
        session.add(up)
        await session.commit()
        await session.refresh(up)
        return up


async def get_user_preferences(user_id: str) -> UserPreferences:
    """Get user preferences, creating with defaults if not exists."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        up = result.scalar_one_or_none()
        if up is None:
            up = await create_user_preferences(user_id)
        return up


async def update_user_preferences(
    user_id: str, **kwargs
) -> Optional[UserPreferences]:
    """Update user preferences."""
    async with AsyncSessionLocal() as session:
        up = await get_user_preferences(user_id)
        if up:
            for key, value in kwargs.items():
                setattr(up, key, value)
            await session.commit()
            await session.refresh(up)
        return up


# IntentLogs CRUD
async def create_intent_log(
    user_id: str,
    message: str,
    detected_intent: str,
    confidence: float,
    entities: Optional[dict] = None,
    processing_time_ms: Optional[int] = None
) -> IntentLogs:
    """Create an intent log."""
    async with AsyncSessionLocal() as session:
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


async def get_intent_logs(
    user_id: Optional[str] = None, limit: int = 100
) -> list[IntentLogs]:
    """Get intent logs."""
    async with AsyncSessionLocal() as session:
        query = select(IntentLogs).order_by(
            IntentLogs.created_at.desc()
        ).limit(limit)
        if user_id is not None:
            query = query.where(IntentLogs.user_id == user_id)
        result = await session.execute(query)
        return result.scalars().all()


async def get_intent_accuracy_stats() -> dict:
    """Get average confidence by intent type."""
    async with AsyncSessionLocal() as session:
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


# DocumentBlob CRUD
async def create_document_blob(
    owner_id, name, content_type, data, blob_metadata=None, document=None
):
    """Create a document blob."""
    async with AsyncSessionLocal() as session:
        blob = DocumentBlob(
            owner_id=owner_id,
            name=name,
            content_type=content_type,
            data=data,
            blob_metadata=blob_metadata,
            document=document
        )
        session.add(blob)
        await session.commit()
        await session.refresh(blob)
        return blob


async def get_document_blob(blob_id):
    """Get a document blob by ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DocumentBlob).where(DocumentBlob.id == blob_id)
        )
        return result.scalar_one_or_none()


async def update_document_blob(blob_id, **kwargs):
    """Update a document blob."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DocumentBlob).where(DocumentBlob.id == blob_id)
        )
        blob = result.scalar_one_or_none()
        if blob:
            for key, value in kwargs.items():
                if key == "metadata":
                    setattr(blob, "blob_metadata", value)
                else:
                    setattr(blob, key, value)
            await session.commit()
            await session.refresh(blob)
        return blob


async def delete_document_blob(blob_id):
    """Delete a document blob."""
    async with AsyncSessionLocal() as session:
        blob = await get_document_blob(blob_id)
        if blob:
            await session.delete(blob)
            await session.commit()
        return blob


async def list_document_blobs_by_owner(owner_id, limit=50):
    """List document blobs by owner."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DocumentBlob)
            .where(DocumentBlob.owner_id == owner_id)
            .order_by(DocumentBlob.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
