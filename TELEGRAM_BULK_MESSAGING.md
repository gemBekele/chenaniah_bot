# Telegram Bulk Messaging Guide

## ⚠️ Important: Telegram Rate Limits

Telegram has strict anti-spam policies and rate limits to prevent abuse:

### Official Rate Limits (2024)
- **Per Chat**: Maximum **1 message per second** per individual chat
- **Global**: Maximum **30 messages per second** across all chats
- **Groups**: Maximum **20 messages per minute** per group chat

### Consequences of Violating Limits
- **429 Too Many Requests** errors
- **Temporary bot restrictions** (minutes to hours)
- **Permanent bot ban** for repeated violations
- **IP-based rate limiting** in severe cases

## ✅ Safe Practices

### Current Implementation
The system currently sends messages **one at a time** when:
- An admin approves/rejects an application (automatic notification)
- This is **safe** because it's triggered by user actions, not bulk operations

### For Bulk Messaging
If you need to send messages to multiple applicants, use the **`telegram_bulk_messenger.py`** utility:

#### Features:
- ✅ **Rate limiting**: 2-second delay between messages (0.5 msg/sec - well below limit)
- ✅ **Per-minute tracking**: Max 50 messages per minute (conservative limit)
- ✅ **Error handling**: Automatically handles 429 errors with retry logic
- ✅ **Dry-run mode**: Test without sending actual messages

#### Usage Examples:

**1. Preview recipients (dry run):**
```bash
python3 telegram_bulk_messenger.py "Your message here" --dry-run
```

**2. Send to all approved applicants:**
```bash
python3 telegram_bulk_messenger.py "Congratulations! Your application was approved." --status approved
```

**3. Send to specific applicants (with limit):**
```bash
python3 telegram_bulk_messenger.py "Important update..." --status pending --limit 50
```

**4. Send to specific user IDs:**
```bash
python3 telegram_bulk_messenger.py "Your message" --user-ids 123456789 987654321 555555555
```

## 📊 Recommended Approach

### For Individual Notifications (Current System)
✅ **Safe** - One message per admin action:
- Admin approves → Applicant gets 1 message
- Admin rejects → Applicant gets 1 message
- No rate limit concerns

### For Bulk Announcements
⚠️ **Use the bulk messenger utility** with:
- Dry-run first to verify recipients
- Start with small batches (10-20 users)
- Monitor for errors
- Spread large batches over time

### Example: Sending to 100 Applicants
```bash
# Step 1: Preview who will receive it
python3 telegram_bulk_messenger.py "Your message" --status approved --dry-run

# Step 2: Send in batches (if needed)
python3 telegram_bulk_messenger.py "Your message" --status approved --limit 50
# Wait a few minutes, then send next batch
```

## 🚫 What NOT to Do

❌ **Don't** send messages in a tight loop without delays
❌ **Don't** send more than 1 message per second to the same user
❌ **Don't** send unsolicited promotional messages (against Telegram ToS)
❌ **Don't** ignore 429 errors - always implement retry logic

## 🔧 Technical Details

### Rate Limiting Implementation
The `telegram_bulk_messenger.py` implements:
- **Per-chat delay**: 2 seconds minimum between messages to same chat
- **Global rate tracking**: Tracks messages per minute
- **Exponential backoff**: On 429 errors, waits 60 seconds before retry
- **Error tracking**: Logs failures without stopping entire batch

### Code Example
```python
from telegram_bulk_messenger import TelegramBulkMessenger

messenger = TelegramBulkMessenger()

# Send to all approved applicants
result = await messenger.send_to_applicants(
    message="Important update about your application",
    status_filter="approved"
)

print(f"Sent: {result['sent']}, Failed: {result['failed']}")
```

## 📝 Best Practices Summary

1. ✅ **Use automatic notifications** for status updates (already implemented)
2. ✅ **Use bulk messenger** for announcements (with dry-run first)
3. ✅ **Start small** - test with 5-10 users before large batches
4. ✅ **Monitor logs** for errors
5. ✅ **Respect delays** - don't try to "speed up" the process
6. ✅ **Only send to users who opted in** (applicants who submitted via your bot)

## ⚖️ Legal & Policy Compliance

- ✅ Only send messages to users who have interacted with your bot
- ✅ Provide value in messages (not pure spam)
- ✅ Allow users to opt-out (respond with /stop or similar)
- ✅ Follow Telegram's Terms of Service
- ✅ Respect user privacy

## 🆘 Troubleshooting

### Getting 429 errors?
- Wait 60 seconds and try again
- Reduce batch size
- Increase delay between messages

### Messages not sending?
- Check bot token is valid
- Verify user_id (chat_id) exists in database
- Check if user has blocked the bot
- Review logs for specific error messages

### Need to send urgent messages?
- Use the bulk messenger with appropriate delays
- Consider splitting into multiple smaller batches
- Monitor success rate and adjust if needed

