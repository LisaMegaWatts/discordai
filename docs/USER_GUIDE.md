# User Guide for Conversational Discord Bot

## Welcome! 🎉

This guide will help you get the most out of your conversational AI Discord bot. The bot now understands natural language and can have real conversations with you, while still supporting traditional slash commands for those who prefer them.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Natural Language Interaction](#natural-language-interaction)
3. [Supported Capabilities](#supported-capabilities)
4. [Examples by Use Case](#examples-by-use-case)
5. [Customizing Your Experience](#customizing-your-experience)
6. [Tips for Best Results](#tips-for-best-results)
7. [Frequently Asked Questions](#frequently-asked-questions)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### How to Talk to the Bot

You can interact with the bot in **two ways**:

#### 1. Natural Language (New! 🌟)

Just talk to the bot like you would to a person:

```
"Can you create an image of a sunset?"
"I'd like to request a new feature"
"What can you do?"
"Hello!"
```

#### 2. Slash Commands (Classic)

Traditional commands still work:

```
/generate-image a sunset
/submit-feature Feature Title | Description
/status
/help
```

### Where to Use the Bot

- **Server Channels**: Mention the bot or send messages in channels where it has access
- **Direct Messages**: Send DMs directly to the bot for private conversations
- **Thread Conversations**: The bot maintains context in threads

---

## Natural Language Interaction

### The Big Change ✨

**Before**: You had to remember specific command syntax
```
/generate-image create a photorealistic image of mountains
```

**Now**: Just talk naturally!
```
"Hey, can you make me a picture of mountains? Make it photorealistic."
```

### How It Works

The bot uses AI to understand what you want:

1. **You send a message** in natural language
2. **Bot analyzes your intent** using semantic understanding
3. **Bot takes action** based on what you need
4. **Bot responds** in a natural, conversational way

### Conversation Memory 🧠

The bot remembers your conversation! You can have multi-turn discussions:

```
You: "Can you help me with something?"
Bot: "Of course! What do you need help with?"

You: "I want to create an image"
Bot: "Great! What would you like me to generate?"

You: "A fantasy castle on a cliff"
Bot: "I'll create that for you! 🏰 Generating an image of a fantasy castle on a cliff..."
```

The bot remembers context for **30 minutes** of inactivity, then starts a fresh conversation.

---

## Supported Capabilities

### 1. Image Generation 🎨

**What it does**: Creates AI-generated images based on your description

---

#### ⚠️ Image Generation Update (v2.1)

- **Root Cause:** Previous failures were due to using the wrong API endpoint and payload.
- **Solution:** The bot now uses the `/v1/images/generations` endpoint with a payload containing both `model` and `prompt`.
- **Model:** The default image model is now `amazon/nova-2-lite-v1:free`.
- **Testing:** When writing tests for image generation, ensure you use proper async HTTP mocking to simulate API responses.

---

**Natural Language Examples**:
```
"Create an image of a sunset over the ocean"
"Draw me a cat wearing a wizard hat"
"Generate a picture of a cyberpunk city at night"
"I want a realistic photo of a red sports car"
"Make me an image of a fantasy dragon"
```

**How to use**:
- Describe what you want as clearly as possible
- Mention style preferences (realistic, cartoon, anime, etc.)
- Add details about colors, mood, lighting, etc.

**What happens**:
- Bot confirms it's generating your image
- Image is created (takes 10-30 seconds)
- Bot sends the image to the channel
- Image is saved for later retrieval

### 2. Feature Requests 💡

**What it does**: Submits feature requests and creates GitHub pull requests automatically

**Natural Language Examples**:
```
"I'd like to request a new feature for dark mode"
"Add support for voice message transcription"
"Feature request: allow users to export chat history"
"Can you add the ability to schedule reminders?"
"I want to be able to search old conversations"
```

**How to use**:
- Describe the feature you want
- Explain why it would be useful
- The bot will extract a title and description

**What happens**:
- Bot confirms your feature request
- Creates a GitHub PR with details
- Stores the request in the database
- Sends you the PR link

### 3. Status Queries 📊

**What it does**: Provides information about bot status and your requests

**Natural Language Examples**:
```
"What's the status of my request?"
"Are you working?"
"How are you doing?"
"Is the bot online?"
"What's happening with my feature request?"
```

**What you get**:
- Current bot status
- Information about your requests
- System health information

### 4. Help & Information ❓

**What it does**: Explains what the bot can do and how to use it

**Natural Language Examples**:
```
"Help"
"What can you do?"
"How do I use this bot?"
"Show me what you're capable of"
"I need help"
```

**What you get**:
- List of capabilities
- Usage examples
- Tips and suggestions

### 5. Conversation & Chat 💬

**What it does**: Engages in natural conversation

**Natural Language Examples**:
```
"Hello!"
"Good morning"
"Thanks for your help!"
"That's awesome"
"You're really helpful"
```

**Bot behavior**:
- Responds naturally and friendly
- Uses emojis appropriately
- Maintains conversational context
- Suggests relevant capabilities when appropriate

### 6. Retrieve Previous Actions 🔍

**What it does**: Shows you images you've generated or requests you've made

**Natural Language Examples**:
```
"Show me my last image"
"What did I request yesterday?"
"Get my previous generations"
"What images have I created?"
"Did my feature request get approved?"
```

**What you get**:
- Your previous images
- Your feature requests history
- Status updates

---

## Examples by Use Case

### Use Case 1: Creating Art & Images

**Scenario**: You want to create custom artwork

```
You: "I need an image for my project"
Bot: "I'd be happy to help! What kind of image are you looking for? 🎨"

You: "A minimalist logo design with a mountain and sun"
Bot: "Great idea! I'll generate a minimalist logo with a mountain and sun for you. ✨"
[Bot generates and sends image]

You: "Can you make it more colorful?"
Bot: "I'll create another version with more vibrant colors! 🌈"
[Bot generates updated image]
```

### Use Case 2: Requesting New Features

**Scenario**: You have an idea for improving the bot

```
You: "I have an idea for a new feature"
Bot: "That's great! I'd love to hear your idea. What feature are you thinking of? 💡"

You: "It would be cool if the bot could remind me about things"
Bot: "That's a useful feature! Let me submit a request for reminder functionality. 
I'll create a GitHub PR to track this. 📝"
[Bot creates PR and shares link]

You: "Thanks! When will it be implemented?"
Bot: "The development team will review the PR and prioritize it. You can track 
progress at [PR link]. I'll notify you of updates! 👍"
```

### Use Case 3: Getting Help

**Scenario**: You're new and want to learn what the bot does

```
You: "What can you do?"
Bot: "I can help you with several things! 🤖

🎨 **Image Generation**: Create custom images from text descriptions
💡 **Feature Requests**: Submit ideas and create GitHub PRs
📊 **Status Checks**: Check on your requests and bot health
💬 **Conversation**: Chat naturally about various topics
🔍 **Retrieve History**: Access your previous images and requests

Try saying something like 'create an image of a sunset' or 'I want to request a feature'!"
```

### Use Case 4: Multi-Turn Conversation

**Scenario**: Complex interaction requiring multiple exchanges

```
You: "I need your help with something"
Bot: "Of course! What do you need? 😊"

You: "I want to create some images for my website"
Bot: "Great! What kind of images are you looking for?"

You: "A hero banner image"
Bot: "What should the hero banner show?"

You: "A modern office space with people collaborating"
Bot: "Perfect! I'll create that for you. 🏢✨"
[Bot generates image]

You: "That's good, but can you make one more with a tech startup vibe?"
Bot: "Absolutely! I'll generate a tech startup version with a more energetic feel. 💻🚀"
[Bot generates second image]
```

---

## Customizing Your Experience

### User Preferences

The bot can adapt to your preferences (features may vary based on implementation):

#### Emoji Usage 😊

Control how many emojis the bot uses:

- **None**: No emojis in responses
- **Low**: Occasional emojis (1-2 per response)
- **Medium** (default): Balanced emoji usage (2-4 per response)
- **High**: Frequent emojis throughout responses

#### Response Tone

Choose how the bot communicates:

- **Formal**: Professional and structured
- **Friendly** (default): Warm and approachable
- **Casual**: Relaxed and informal
- **Technical**: Detailed and precise

### Conversation Context

The bot remembers:

- **Last 10-20 messages** in your conversation
- **Context for 30 minutes** after your last message
- **Your previous requests** and generated images

---

## Tips for Best Results

### For Image Generation 🎨

**✅ DO**:
- Be specific and descriptive
- Mention style preferences (realistic, cartoon, etc.)
- Include details about colors, mood, lighting
- Reference well-known artistic styles if relevant

**Examples**:
```
✅ "Create a photorealistic image of a golden retriever playing in a park at sunset"
✅ "Draw a cartoon-style robot with a friendly expression, bright colors"
✅ "Generate a cyberpunk cityscape at night with neon lights, rain-slicked streets"
```

**❌ DON'T**:
- Be too vague ("make something cool")
- Use contradictory requirements
- Request inappropriate content

### For Feature Requests 💡

**✅ DO**:
- Clearly explain what you want
- Describe why it would be useful
- Provide context or use cases

**Examples**:
```
✅ "Add dark mode so users can use the bot at night without eye strain"
✅ "Allow exporting conversation history to PDF for record keeping"
✅ "Implement voice message support since many users prefer speaking"
```

**❌ DON'T**:
- Be too vague ("make it better")
- Request features that violate terms of service
- Duplicate existing features

### For Conversations 💬

**✅ DO**:
- Ask follow-up questions
- Provide clarification when asked
- Be patient while bot processes requests

**❌ DON'T**:
- Send multiple messages rapidly (wait for responses)
- Expect instant responses for complex requests
- Use offensive or inappropriate language

---

## Frequently Asked Questions

### General Questions

**Q: Can the bot remember our previous conversations?**

A: Yes! The bot uses persistent memory and session management to remember your conversation for 30 minutes after your last message. Sessions are reliably maintained across bot restarts, Redis flushes, and multi-instance deployments.

**Q: Does the bot work in DMs?**

A: Yes! You can DM the bot directly for private conversations. All features work the same way in DMs.

**Q: Can I use the old slash commands?**

A: Absolutely! All original slash commands (`/generate-image`, `/submit-feature`, etc.) still work exactly as before. Use whichever method you prefer.

**Q: How does the bot understand what I want?**

A: The bot uses Claude AI to analyze your message and determine your intent. It looks at the words you use, the context of your conversation, and patterns in how people typically communicate requests.

**Q: Are secrets stored securely?**

A: Yes. All secrets are stored in environment variables only. Git history was rewritten to remove secrets from all tracked files and commits. Never commit secrets to version control.

### Image Generation

**Q: How long does image generation take?**

A: Typically 10-30 seconds depending on complexity. The bot will show a "typing" indicator while working.

**Q: Can I regenerate an image if I don't like it?**

A: Yes! Just ask for another image with more specific instructions. For example: "Can you make that more colorful?" or "Try again but make it darker."

**Q: Where are my images stored?**

A: Images are saved on the bot's server and recorded in the database. You can retrieve them later by asking "show me my images" or using `/get-image`.

**Q: What if the image doesn't match what I asked for?**

A: Try being more specific in your description. You can also ask for modifications: "Make it brighter" or "Add more trees."

### Feature Requests

**Q: What happens to my feature request?**

A: The bot creates a GitHub PR (Pull Request) with your feature details. The development team reviews it and may implement it in a future update.

**Q: Can I check the status of my feature request?**

A: Yes! Ask "What's the status of my feature request?" or check the GitHub PR link the bot provided.

**Q: Can I request multiple features?**

A: Yes, but it's better to submit them separately so each can be tracked individually.

### Privacy & Data

**Q: Is my conversation private?**

A: Conversations are stored in the database for context management and improvements. In DMs, only you and the bot can see messages. In server channels, it follows normal Discord privacy rules.

**Q: How long is my data kept?**

A: Conversation history is typically retained for 90 days, intent logs for 30 days, and user preferences until you delete them. Check the privacy policy for specifics.

**Q: Can I delete my data?**

A: Yes, contact the bot administrator to request data deletion.

---

## Troubleshooting

### Bot Not Responding

**Problem**: Bot doesn't respond to your messages

**Solutions**:
1. Check if the bot is online (green status indicator)
2. Verify the bot has permission to read/send messages in the channel
3. Try using a slash command like `/status` to test
4. Check if you're in a DM or channel where the bot is active

### Bot Misunderstands Your Request

**Problem**: Bot does the wrong thing or says it doesn't understand

**Solutions**:
1. Be more specific in your request
2. Try rephrasing your message
3. Use explicit keywords like "create image", "feature request", "help"
4. Break complex requests into simpler steps
5. Use a slash command for guaranteed behavior

**Example**:
```
❌ "Make something cool"  (too vague)
✅ "Create an image of a sunset over mountains"  (specific)
```

### Slow Response Times

**Problem**: Bot takes a long time to respond

**Possible Causes**:
- Image generation naturally takes 10-30 seconds
- High server load
- Complex request requiring more processing

**What to do**:
- Wait for the typing indicator to finish
- For very slow responses, try asking a simpler question first
- Check bot status: "Are you working okay?"

### Incorrect Image Generated

**Problem**: Generated image doesn't match your description

**Solutions**:
1. Provide more detailed descriptions
2. Specify the style explicitly (photorealistic, cartoon, etc.)
3. Mention what was wrong and ask for another attempt
4. Use reference terms (e.g., "like a movie poster", "professional photography style")

**Example iteration**:
```
You: "Create an image of a dog"
[Gets generic dog image]

You: "Can you make it a golden retriever puppy playing in a garden with flowers?"
[Gets more specific result]
```

### Lost Conversation Context

**Problem**: Bot seems to forget what you were talking about

**Possible Causes**:
- 30+ minutes passed since your last message (session timeout)
- Bot was restarted
- You switched channels/DMs

**What to do**:
- Restate the context briefly: "Earlier we were discussing image generation..."
- Start fresh if needed – the bot will understand your new request

### Can't Access Previous Images

**Problem**: Bot can't find your previous images

**Solutions**:
1. Use `/get-image` command for more reliable retrieval
2. Ask specifically: "Show me the image I created yesterday of a sunset"
3. Check that images were successfully generated (you received them in chat)

---

## Command Reference

### Slash Commands (For Quick Access)

| Command | Description | Example |
|---------|-------------|---------|
| `/generate-image <prompt>` | Generate an image | `/generate-image a sunset over mountains` |
| `/submit-feature <title> \| <desc>` | Submit feature request | `/submit-feature Dark Mode \| Add dark theme` |
| `/get-image [id]` | Retrieve an image | `/get-image` or `/get-image 123` |
| `/status` | Check bot status | `/status` |
| `/request-feature` | Feature request flow | `/request-feature` |

### Natural Language Patterns

**Image Generation**:
- "create/generate/draw/make an image of..."
- "can you create a picture of..."
- "I want an image showing..."

**Feature Requests**:
- "I'd like to request a feature..."
- "add support for..."
- "can you add..."
- "feature request: ..."

**Status Checks**:
- "what's the status..."
- "are you working..."
- "how are you..."

**Help**:
- "help"
- "what can you do..."
- "how do I..."

**Conversation**:
- "hello", "hi", "hey"
- "thanks", "thank you"
- "that's cool", "awesome"

---

## Best Practices Summary

### ✅ Do This

- ✅ Be clear and specific in your requests
- ✅ Use natural language – talk like you would to a person
- ✅ Ask follow-up questions if you need clarification
- ✅ Give the bot time to process complex requests
- ✅ Provide feedback on results ("that's perfect!" or "can you adjust...")
- ✅ Use slash commands when you want guaranteed behavior

### ❌ Avoid This

- ❌ Don't send multiple messages rapidly without waiting for responses
- ❌ Don't use vague requests ("make something cool")
- ❌ Don't expect instant responses for image generation
- ❌ Don't request inappropriate or offensive content
- ❌ Don't spam the bot if it's slow – it's likely processing your request

---

## Getting More Help

### Resources

- **Architecture Documentation**: [`docs/conversational_bot_architecture.md`](conversational_bot_architecture.md) - Technical details
- **Testing Guide**: [`docs/TESTING_GUIDE.md`](TESTING_GUIDE.md) - For developers and testers
- **Main README**: [`README.md`](../README.md) - Setup and configuration
- **GitHub Issues**: Report bugs or request features

### Contact

- **Bot Administrator**: Contact your Discord server admin
- **Technical Issues**: Create a GitHub issue
- **Feature Requests**: Use the bot's feature request functionality!

---

## Changelog & Updates

The bot is continuously improving! Check [`CHANGELOG.md`](../CHANGELOG.md) for recent updates and new features.

**Current Version**: 2.0.0

**Recent Additions**:
- 🎉 Natural language understanding
- 🧠 Conversation memory and context
- 😊 Emoji integration
- ⚡ Performance optimizations
- 📊 Intent logging and analytics

---

## Examples Gallery

### Quick Start Examples

Try these to get started:

```
"Hello! What can you do?"
"Create an image of a mountain landscape"
"I'd like to request a feature for user profiles"
"Show me my last image"
"What's your status?"
"Thanks for your help!"
```

### Creative Examples

```
"Generate a surreal painting of floating islands in a pink sky"
"Draw a cute robot character in anime style"
"Create a professional logo with a phoenix design"
"Make an image of a cozy coffee shop interior with warm lighting"
```

### Feature Request Examples

```
"Add support for scheduling daily reminders"
"I'd like to export my conversation history as a PDF"
"Feature request: implement multi-language support"
"Can you add voice message transcription?"
```

---

## Welcome to the Future of Discord Bots! 🚀

The conversational features make interacting with the bot feel natural and intuitive. Whether you're creating images, requesting features, or just chatting, the bot is here to help.

**Remember**: You can always fall back to slash commands if you prefer the traditional approach. Both methods work great!

Happy chatting! 🎉