from models import FeatureRequest, GeneratedImage, ScheduledTask, ReflectionLog
from sqlalchemy.future import select

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