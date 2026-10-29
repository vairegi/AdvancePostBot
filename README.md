# Advanced Telegram Post Creator Bot

Advanced Telegram bot for creating and publishing channel posts: caption, media,
inline buttons, tables, auto-delete, preview, saved posts and MongoDB storage.

Built with aiogram 3.31, MongoDB and Render webhook deployment.

## Render Deployment

1. Upload this folder to GitHub.
2. Render -> New Web Service -> select repo.
3. Build Command: pip install -r requirements.txt
4. Start Command: python -m app.main
5. Add environment variables: BOT_TOKEN, MONGODB_URI, WEBHOOK_SECRET.
6. Deploy, then send /start to the bot once. It sets its own webhook.

## 24/7 Keep Alive

Add an UptimeRobot HTTP monitor for:

https://your-render-url.onrender.com/health

Interval: 5 minutes.

## Channel Setup

Add the bot as channel administrator with Post Messages permission.
Then use My Channels -> Add Channel and send @channelusername
or forward any message from the channel.