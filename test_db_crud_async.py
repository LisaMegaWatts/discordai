import asyncio
import os
import random
import string
from db import AsyncSessionLocal
from crud import (
    create_feature_request, get_feature_request, update_feature_request, delete_feature_request,
    create_generated_image, get_generated_image, update_generated_image, delete_generated_image,
    create_scheduled_task, get_scheduled_task, update_scheduled_task, delete_scheduled_task,
    create_reflection_log, get_reflection_log, update_reflection_log, delete_reflection_log,
    create_conversation_session, get_conversation_session, update_session_activity, end_conversation_session,
    create_conversation_message, get_conversation_history,
    create_user_preferences, get_user_preferences, update_user_preferences,
    create_intent_log, get_intent_logs,
    create_document_blob, get_document_blob, update_document_blob, delete_document_blob
)

def randstr(n=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

async def test_feature_request_crud():
    fr = await create_feature_request("user1", "Test FR", "Description")
    assert fr.id
    fr2 = await get_feature_request(fr.id)
    assert fr2.title == "Test FR"
    fr3 = await update_feature_request(fr.id, title="Updated FR")
    assert fr3.title == "Updated FR"
    fr4 = await delete_feature_request(fr.id)
    assert fr4.id == fr.id

async def test_document_blob_crud():
    data = "hello world".encode("utf-8")
    print(f"[TEST] type(data)={type(data)}, value={data}")
    blob = await create_document_blob("owner1", "doc1", "text/plain", data, blob_metadata={"foo": "bar"})
    assert blob.id
    blob2 = await get_document_blob(blob.id)
    assert blob2.name == "doc1"
    blob3 = await update_document_blob(blob.id, name="doc2", blob_metadata={"foo": "baz"})
    assert blob3.name == "doc2"
    blob4 = await delete_document_blob(blob.id)
    assert blob4.id == blob.id

async def test_concurrent_sessions():
    tasks = []
    for i in range(10):
        user_id = f"user_{i}"
        tasks.append(create_conversation_session(user_id))
    sessions = await asyncio.gather(*tasks)
    assert all(s.id for s in sessions if s)

async def run_all_tests():
    await test_feature_request_crud()
    await test_document_blob_crud()
    await test_concurrent_sessions()
    print("CRUD and concurrency tests passed.")

if __name__ == "__main__":
    asyncio.run(run_all_tests())