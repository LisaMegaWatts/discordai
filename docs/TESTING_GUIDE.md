# Testing Guide for Conversational Discord Bot

## Overview

This guide provides comprehensive instructions for testing the conversational bot features, including semantic intent detection, conversation context management, and natural language interactions. Use this guide to verify all functionality works as expected.

## Table of Contents

1. [Testing Prerequisites](#testing-prerequisites)
2. [Intent Detection Testing](#intent-detection-testing)
3. [Conversation Context Testing](#conversation-context-testing)
4. [Response Generation Testing](#response-generation-testing)
5. [User Preferences Testing](#user-preferences-testing)
6. [Performance Testing](#performance-testing)
7. [Database Verification](#database-verification)
8. [Integration Testing](#integration-testing)
9. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)

---

## Testing Prerequisites

### Required Setup

Before testing, ensure:

1. **Bot is running** with all services initialized
2. **Database is accessible** and migrations are applied
3. **API keys are configured**:
   - `ANTHROPIC_API_KEY` - For Claude AI
   - `OPENROUTER_API_KEY` - For image generation
   - `GITHUB_TOKEN` - For feature requests
4. **Test Discord server** with appropriate permissions

### Environment Verification

```bash
# Verify environment variables
python -c "import os; print('Anthropic:', bool(os.getenv('ANTHROPIC_API_KEY'))); print('OpenRouter:', bool(os.getenv('OPENROUTER_API_KEY')))"

# Check database connectivity
python setup_db.py

# Verify bot is online
# Check Discord for bot's online status
```

---

## Intent Detection Testing

### Test Cases by Intent Type

#### 1. Generate Image Intent

**Purpose**: Verify the bot correctly identifies image generation requests.

**Test Messages**:

```
✓ "create an image of a sunset over mountains"
✓ "can you draw me a cat wearing a hat?"
✓ "generate a picture of a cyberpunk cityscape"
✓ "make me an image of a fantasy castle"
✓ "I want a realistic photo of a red sports car"
```

**Expected Behavior**:
- Intent detected as `generate_image`
- Confidence score ≥ 0.75
- Entities extracted: `prompt`, optionally `style` and `modifiers`
- Image generation initiated
- Response includes confirmation and image

**Verification**:
```sql
-- Check intent log
SELECT * FROM intent_logs 
WHERE detected_intent = 'generate_image' 
ORDER BY created_at DESC LIMIT 5;

-- Verify entities were extracted
SELECT message_content, entities 
FROM intent_logs 
WHERE detected_intent = 'generate_image';
```

#### 2. Submit Feature Intent

**Purpose**: Verify feature request detection and GitHub PR creation.

**Test Messages**:

```
✓ "I'd like to request a new feature for scheduling tasks"
✓ "add support for voice message transcription"
✓ "feature request: implement dark mode for the interface"
✓ "can you add the ability to export conversation history?"
✓ "I want to be able to set reminders"
```

**Expected Behavior**:
- Intent detected as `submit_feature`
- Confidence score ≥ 0.70
- Entities extracted: `title`, `description`
- Feature stored in database
- GitHub PR created
- Response includes PR link

**Verification**:
```sql
-- Check feature requests
SELECT * FROM feature_requests 
ORDER BY created_at DESC LIMIT 5;

-- Check intent detection
SELECT message_content, confidence, entities 
FROM intent_logs 
WHERE detected_intent = 'submit_feature';
```

#### 3. Get Status Intent

**Purpose**: Verify status query detection.

**Test Messages**:

```
✓ "what's the status of my request?"
✓ "are you working?"
✓ "how are you doing?"
✓ "is the bot online?"
✓ "what's happening with my feature request?"
```

**Expected Behavior**:
- Intent detected as `get_status`
- Confidence score ≥ 0.80
- Appropriate status response provided
- No external actions triggered

**Verification**:
```sql
SELECT message_content, confidence 
FROM intent_logs 
WHERE detected_intent = 'get_status'
ORDER BY created_at DESC;
```

#### 4. Get Help Intent

**Purpose**: Verify help request detection.

**Test Messages**:

```
✓ "help"
✓ "what can you do?"
✓ "how do I use this bot?"
✓ "show me the commands"
✓ "I need help with something"
```

**Expected Behavior**:
- Intent detected as `get_help`
- Confidence score ≥ 0.85
- Comprehensive help information provided
- Lists available capabilities

**Verification**:
```sql
SELECT message_content, confidence 
FROM intent_logs 
WHERE detected_intent = 'get_help';
```

#### 5. General Conversation Intent

**Purpose**: Verify casual conversation handling.

**Test Messages**:

```
✓ "hello!"
✓ "good morning"
✓ "thanks for your help"
✓ "that's awesome"
✓ "cool, thanks!"
```

**Expected Behavior**:
- Intent detected as `general_conversation`
- Confidence score ≥ 0.60
- Friendly, contextual response
- Natural emoji usage based on preferences

**Verification**:
```sql
SELECT message_content, confidence, entities 
FROM intent_logs 
WHERE detected_intent = 'general_conversation'
ORDER BY created_at DESC LIMIT 10;
```

#### 6. Action Query Intent

**Purpose**: Verify queries about previous actions.

**Test Messages**:

```
✓ "show me my last image"
✓ "what did I request yesterday?"
✓ "get my previous generations"
✓ "did my feature request get approved?"
✓ "what images have I created?"
```

**Expected Behavior**:
- Intent detected as `action_query`
- Confidence score ≥ 0.75
- Retrieves relevant historical data
- Provides requested information

#### 7. Unclear Intent

**Purpose**: Verify handling of ambiguous messages.

**Test Messages**:

```
✓ "hmm"
✓ "..."
✓ "what?"
✓ "ok"
✓ (very short/incomplete messages)
```

**Expected Behavior**:
- Intent detected as `unclear`
- Confidence score < 0.40
- Bot asks for clarification
- Suggests possible intents

---

## Conversation Context Testing

### Session Management Tests

#### Test 1: New Session Creation

**Steps**:
1. Send first message from a new user
2. Verify session is created

**Verification**:
```sql
-- Check session was created
SELECT * FROM conversation_sessions 
WHERE user_id = '<user_discord_id>' 
AND status = 'active'
ORDER BY started_at DESC LIMIT 1;

-- Should return 1 active session
```

#### Test 2: Session Continuity

**Steps**:
1. Send multiple messages within 30 minutes
2. Verify all messages use same session

**Expected**: All messages associated with same `session_id`

**Verification**:
```sql
-- Check messages share same session
SELECT session_id, COUNT(*) as message_count 
FROM conversation_history 
WHERE user_id = '<user_discord_id>' 
GROUP BY session_id 
ORDER BY MAX(created_at) DESC;
```

#### Test 3: Session Timeout

**Steps**:
1. Send a message
2. Wait 31+ minutes
3. Send another message
4. Verify new session was created

**Verification**:
```sql
-- Check for multiple sessions
SELECT id, started_at, status, message_count 
FROM conversation_sessions 
WHERE user_id = '<user_discord_id>' 
ORDER BY started_at DESC LIMIT 5;

-- Should show old session marked as 'ended' and new 'active' session
```

### Context Window Tests

#### Test 4: Context Retrieval

**Steps**:
1. Send 15 messages in a conversation
2. Verify only last 10-20 messages are used as context

**Verification**:
```sql
-- Check conversation history
SELECT COUNT(*) 
FROM conversation_history 
WHERE session_id = '<session_id>';

-- Should return all messages, but context manager limits what's sent to Claude
```

#### Test 5: Context Awareness

**Test Conversation**:
```
User: "My name is Alice"
Bot: (acknowledges)
User: "What's my name?"
Bot: (should remember "Alice")
```

**Expected**: Bot responds with the name from earlier in conversation

#### Test 6: Multi-turn Conversation

**Test Scenario**:
```
User: "Can you help me with something?"
Bot: "Of course! What do you need help with?"
User: "I want to create an image"
Bot: (should understand this refers to previous context)
User: "of a sunset"
Bot: (should combine both messages to understand: image of a sunset)
```

**Expected**: Bot maintains context across multiple turns

---

## Response Generation Testing

### Natural Language Response Tests

#### Test 7: Response Quality

**Criteria to Verify**:
- [ ] Responses are grammatically correct
- [ ] Tone matches user preferences (friendly by default)
- [ ] Appropriate emoji usage
- [ ] No placeholder text or incomplete responses
- [ ] Responses are contextually relevant
- [ ] Technical terms explained when appropriate

#### Test 8: Emoji Integration

**Test with different preferences** (if user preference system is exposed):

**No Emojis**: Response should have 0 emojis
**Low Emoji**: 1-2 emojis per response
**Medium Emoji** (default): 2-4 emojis naturally placed
**High Emoji**: Emojis used liberally

**Verification**: Count emojis in responses and compare to preference setting

#### Test 9: Response Consistency

**Test**: Ask the same question multiple times

**Expected**: 
- Answers should be consistent in content
- Phrasing may vary (not robotic repetition)
- Cache may return identical response for same query

---

## User Preferences Testing

### Preference Storage

#### Test 10: Preference Persistence

**Steps**:
1. Set user preference (if command available)
2. Restart bot
3. Send message
4. Verify preference is still applied

**Verification**:
```sql
-- Check stored preferences
SELECT * FROM user_preferences 
WHERE user_id = '<user_discord_id>';
```

### Preference Application

**Verify preferences affect**:
- [ ] Response tone (formal/friendly/casual/technical)
- [ ] Emoji density
- [ ] Context window size
- [ ] Notification preferences

---

## Performance Testing

### Response Time Benchmarks

#### Test 11: Intent Detection Speed

**Target**: < 2 seconds for intent detection

**Test**:
```python
import time

start = time.time()
# Send message to bot
# Wait for intent to be logged
end = time.time()

print(f"Intent detection: {end - start:.2f}s")
```

**Verification**:
```sql
-- Check processing times
SELECT AVG(processing_time_ms) as avg_ms, 
       MAX(processing_time_ms) as max_ms,
       MIN(processing_time_ms) as min_ms
FROM intent_logs 
WHERE created_at > NOW() - INTERVAL '1 hour';

-- Should show avg < 2000ms
```

#### Test 12: End-to-End Response Time

**Target**: < 5 seconds for complete response

**Test**: Measure time from message send to bot response received

**Acceptable Times**:
- Simple conversation: < 2 seconds
- Image generation: < 30 seconds
- Feature request: < 5 seconds
- Status query: < 2 seconds

### Cache Performance

#### Test 13: Cache Hit Rate

**Steps**:
1. Send same message multiple times
2. Verify cache is being used

**Verification**:
```python
# Check cache statistics (if exposed via logs/metrics)
# Look for "Cache hit" messages in logs

# Expected: Cache hit rate > 30% for repeated queries
```

#### Test 14: Cache Invalidation

**Steps**:
1. Send message
2. Wait for TTL to expire (5 minutes default)
3. Send same message
4. Verify fresh response is generated

**Expected**: Response regenerated after cache expiry

### Load Testing

#### Test 15: Concurrent Users

**Test**: Simulate multiple users sending messages simultaneously

**Tools**: Use Discord bot testing framework or manual testing with multiple accounts

**Target Performance**:
- Handle 10 concurrent users without degradation
- Queue properly manages multiple requests
- No message loss or errors

**Verification**:
```sql
-- Check for errors during load test period
SELECT COUNT(*) as error_count
FROM intent_logs 
WHERE execution_success = FALSE 
AND created_at > NOW() - INTERVAL '5 minutes';
```

---

## Database Verification

### Data Integrity Tests

#### Test 16: Conversation History Storage

**Verification Query**:
```sql
-- Check conversation history is being stored
SELECT 
    ch.id,
    ch.user_id,
    ch.role,
    ch.message,
    ch.intent,
    ch.confidence,
    ch.created_at
FROM conversation_history ch
WHERE ch.user_id = '<user_discord_id>'
ORDER BY ch.created_at DESC
LIMIT 20;

-- Verify:
-- - User and assistant messages alternate properly
-- - User messages have intent/confidence
-- - Timestamps are sequential
-- - No NULL values in required fields
```

#### Test 17: Intent Logging

**Verification Query**:
```sql
-- Check intent logs are comprehensive
SELECT 
    detected_intent,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence,
    AVG(execution_time_ms) as avg_time_ms
FROM intent_logs
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY detected_intent
ORDER BY count DESC;

-- Should show distribution of intents and performance metrics
```

#### Test 18: Session Tracking

**Verification Query**:
```sql
-- Check session data
SELECT 
    id,
    user_id,
    started_at,
    last_active,
    status,
    message_count,
    EXTRACT(EPOCH FROM (last_active - started_at))/60 as duration_minutes
FROM conversation_sessions
WHERE user_id = '<user_discord_id>'
ORDER BY started_at DESC
LIMIT 10;

-- Verify:
-- - Sessions properly marked as active/ended
-- - Message counts are accurate
-- - Timestamps make sense
```

### Database Performance

#### Test 19: Query Performance

**Test Queries**:
```sql
-- This should be fast (< 100ms)
EXPLAIN ANALYZE
SELECT * FROM conversation_history 
WHERE session_id = '<session_id>' 
ORDER BY created_at DESC 
LIMIT 20;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE tablename IN ('conversation_history', 'intent_logs', 'user_preferences');
```

**Expected**: Indexes are being used, queries execute quickly

---

## Integration Testing

### GitHub Integration

#### Test 20: Feature Request PR Creation

**Steps**:
1. Send: "I'd like to request a feature for exporting chat history"
2. Verify PR is created on GitHub
3. Check PR content matches request

**Verification**:
- [ ] PR exists on GitHub
- [ ] PR title and description are accurate
- [ ] Discord link is included in PR
- [ ] Feature request stored in database

### OpenRouter Integration

#### Test 21: Image Generation

**Steps**:
1. Send: "create an image of a mountain landscape"
2. Verify image is generated and sent
3. Check image is stored

**Verification**:
- [ ] Image file exists in `generated_images/` directory
- [ ] Image metadata in database
- [ ] Image displayed in Discord
- [ ] Prompt is stored correctly

```sql
SELECT * FROM generated_images 
WHERE user_id = '<user_discord_id>' 
ORDER BY created_at DESC LIMIT 5;
```

### Backward Compatibility

#### Test 22: Slash Commands Still Work

**Test all original commands**:

```
/status
/generate-image a sunset
/submit-feature Feature Title | Feature Description
/get-image
/request-feature
```

**Expected**: All commands work as they did before conversational features

---

## Common Issues and Troubleshooting

### Issue: Intent Detection Returns "unclear"

**Symptoms**: Most messages classified as "unclear" intent

**Possible Causes**:
1. Anthropic API key not configured
2. Claude API request failing
3. Response parsing error

**Debugging**:
```bash
# Check logs for errors
grep "Error detecting intent" bot.log

# Verify API key
python -c "import os; print('Key set:', bool(os.getenv('ANTHROPIC_API_KEY')))"

# Test API directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model": "claude-3-5-sonnet-20241022", "max_tokens": 100, "messages": [{"role": "user", "content": "Hello"}]}'
```

### Issue: Conversation Context Not Maintained

**Symptoms**: Bot doesn't remember previous messages

**Possible Causes**:
1. Database connection issues
2. Session creation failing
3. Context retrieval error

**Debugging**:
```sql
-- Check if messages are being stored
SELECT COUNT(*) FROM conversation_history 
WHERE created_at > NOW() - INTERVAL '1 hour';

-- Check sessions
SELECT * FROM conversation_sessions 
WHERE status = 'active';

-- Check for errors
SELECT * FROM intent_logs 
WHERE execution_success = FALSE 
ORDER BY created_at DESC;
```

### Issue: Slow Response Times

**Symptoms**: Bot takes >10 seconds to respond

**Possible Causes**:
1. Claude API slow/timing out
2. Database queries slow
3. Too much context being sent
4. Cache not working

**Debugging**:
```sql
-- Check processing times
SELECT 
    detected_intent,
    AVG(execution_time_ms) as avg_ms,
    MAX(execution_time_ms) as max_ms
FROM intent_logs
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY detected_intent;
```

**Solutions**:
- Enable/verify caching is working
- Reduce context window size
- Check database indexes
- Monitor API rate limits

### Issue: Cache Not Working

**Symptoms**: Same queries always generate fresh responses

**Debugging**:
```python
# Check if cache service is initialized
# Look for cache hit/miss logs in bot output

# Verify cache settings in code
```

**Solutions**:
- Check cache service initialization in [`discord_bot.py`](discord_bot.py:57)
- Verify TTL settings
- Check cache cleanup task is running

### Issue: Emojis Not Appearing

**Symptoms**: Bot responses don't include emojis

**Possible Causes**:
1. User preference set to "none"
2. Claude not generating emojis
3. Emoji being stripped somewhere

**Debugging**:
```sql
-- Check user preference
SELECT emoji_density FROM user_preferences 
WHERE user_id = '<user_discord_id>';

-- Check raw responses in conversation_history
SELECT message FROM conversation_history 
WHERE role = 'assistant' 
ORDER BY created_at DESC LIMIT 10;
```

### Issue: Database Connection Errors

**Symptoms**: Errors about database connectivity

**Debugging**:
```bash
# Test database connection
python setup_db.py

# Check Docker container
docker ps | grep postgres

# View logs
docker-compose logs postgres

# Test connection string
psql $DATABASE_URL -c "SELECT 1;"
```

---

## Testing Checklist

Use this checklist to ensure comprehensive testing:

### Functional Testing
- [ ] All 7 intent types detect correctly
- [ ] Entity extraction works for each intent
- [ ] Conversation context is maintained
- [ ] Session management works (create/timeout/end)
- [ ] Responses are natural and appropriate
- [ ] Emoji usage matches preferences
- [ ] Image generation works end-to-end
- [ ] Feature requests create GitHub PRs
- [ ] Slash commands still work (backward compatibility)

### Performance Testing
- [ ] Intent detection < 2 seconds
- [ ] End-to-end response < 5 seconds
- [ ] Cache hit rate > 30% for repeated queries
- [ ] Handles 10+ concurrent users
- [ ] Database queries use indexes

### Data Integrity Testing
- [ ] All messages stored in conversation_history
- [ ] Intent logs capture all attempts
- [ ] Sessions track properly
- [ ] User preferences persist
- [ ] No data loss during errors

### Integration Testing
- [ ] GitHub integration creates valid PRs
- [ ] OpenRouter generates and stores images
- [ ] External API errors handled gracefully
- [ ] Rate limiting works correctly

### Error Handling Testing
- [ ] Unclear intents ask for clarification
- [ ] API failures show user-friendly messages
- [ ] Database errors don't crash bot
- [ ] Invalid input handled gracefully
- [ ] Timeout scenarios handled

---

## Performance Benchmarks

### Expected Metrics

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Intent Detection | < 1s | < 2s | > 3s |
| Response Generation | < 3s | < 5s | > 7s |
| Image Generation | < 20s | < 30s | > 45s |
| Cache Hit Rate | > 40% | > 30% | < 20% |
| Database Query Time | < 50ms | < 100ms | > 200ms |
| Conversation Retrieval | < 100ms | < 200ms | > 500ms |

### Monitoring Commands

```sql
-- Overall system health
SELECT 
    'Intent Detection' as metric,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN execution_success THEN 1 ELSE 0 END) as successful,
    AVG(execution_time_ms) as avg_time_ms,
    MAX(execution_time_ms) as max_time_ms
FROM intent_logs
WHERE created_at > NOW() - INTERVAL '1 hour';

-- Intent distribution
SELECT 
    detected_intent,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence
FROM intent_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY detected_intent
ORDER BY count DESC;

-- Active sessions
SELECT COUNT(*) as active_sessions
FROM conversation_sessions
WHERE status = 'active';

-- Recent errors
SELECT message_content, error_message, created_at
FROM intent_logs
WHERE execution_success = FALSE
ORDER BY created_at DESC
LIMIT 10;
```

---

## Automated Testing

### Unit Test Examples

Create test files in a `tests/` directory:

```python
# tests/test_intent_detection.py
import pytest
from services.intent_service import IntentDetectionService

@pytest.mark.asyncio
async def test_image_generation_intent():
    service = IntentDetectionService(mock_anthropic_client)
    result = await service.detect_intent("create an image of a sunset")
    
    assert result['intent'] == 'generate_image'
    assert result['confidence'] > 0.75
    assert 'prompt' in result['entities']

@pytest.mark.asyncio
async def test_feature_request_intent():
    service = IntentDetectionService(mock_anthropic_client)
    result = await service.detect_intent("I want to add dark mode")
    
    assert result['intent'] == 'submit_feature'
    assert result['confidence'] > 0.70
```

### Integration Test Examples

```python
# tests/test_conversation_flow.py
import pytest
from services.conversation_service import ConversationContextManager

@pytest.mark.asyncio
async def test_session_creation():
    manager = ConversationContextManager(mock_db_session)
    session_id = await manager.get_or_create_session("test_user_123")
    
    assert session_id is not None
    assert isinstance(session_id, str)

@pytest.mark.asyncio
async def test_message_storage():
    manager = ConversationContextManager(mock_db_session)
    session_id = await manager.get_or_create_session("test_user_123")
    
    await manager.add_message(
        session_id=session_id,
        user_id="test_user_123",
        message="Hello",
        role="user",
        intent="general_conversation",
        confidence=0.95
    )
    
    context = await manager.get_conversation_context(session_id)
    assert len(context) == 1
    assert context[0]['message'] == "Hello"
```

---

## Test Report Template

Use this template to document test results:

```markdown
# Test Report - Conversational Bot Features

**Date**: YYYY-MM-DD
**Tester**: Your Name
**Bot Version**: 2.0.0
**Environment**: Development/Staging/Production

## Test Summary

- **Total Tests**: XX
- **Passed**: XX
- **Failed**: XX
- **Skipped**: XX

## Detailed Results

### Intent Detection (X/Y passed)
- ✅ Generate Image Intent
- ✅ Submit Feature Intent
- ⚠️ Get Status Intent (low confidence on some queries)
- ❌ Action Query Intent (not detecting correctly)

### Performance Metrics
- Average Intent Detection: X.XXs
- Average Response Time: X.XXs
- Cache Hit Rate: XX%

### Issues Found
1. **Issue**: Action queries not detecting properly
   **Severity**: Medium
   **Steps to Reproduce**: Send "show me my last image"
   **Expected**: action_query intent
   **Actual**: unclear intent

## Recommendations
- [ ] Improve action query intent detection prompts
- [ ] Add more test cases for edge cases
- [ ] Optimize database query performance

## Sign-off
Tested by: _______________
Date: _______________
```

---

## Conclusion

This testing guide provides comprehensive coverage of all conversational bot features. Regular testing ensures:

- ✅ Reliable intent detection
- ✅ Smooth conversation flow
- ✅ Good performance
- ✅ Data integrity
- ✅ Integration stability

**For questions or issues**, refer to:
- [`docs/conversational_bot_architecture.md`](conversational_bot_architecture.md) - Technical architecture
- [`docs/USER_GUIDE.md`](USER_GUIDE.md) - User-facing documentation
- GitHub Issues - Report bugs or request features