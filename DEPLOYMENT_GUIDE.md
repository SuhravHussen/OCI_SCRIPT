# Oracle Cloud Instance Creator - Web Server Deployment Guide

## Overview

This application has been converted from a continuous background worker to a **web server** that can be triggered by external cron jobs. This allows deployment on Render's **free tier** web services.

## How It Works

1. **Web Server**: The bot runs as a Flask web server with two endpoints:
   - `GET /` - Health check endpoint
   - `GET /trigger` - Triggers a single instance creation attempt

2. **External Cron**: You set up an external cron service (like cron-job.org) to hit the `/trigger` endpoint every 10 minutes

3. **Single Attempt**: Each trigger attempts to create an Oracle Cloud instance once (not continuously)

## Deployment on Render

### Step 1: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub, GitLab, or email

### Step 2: Push Code to GitHub
1. Create a new GitHub repository
2. Push this code to your repository:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Step 3: Deploy on Render
1. Log in to Render Dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `oracle-cloud-bot` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: Leave empty (Procfile will be used automatically)
   - **Plan**: Select **"Free"**

5. Click **"Create Web Service"**

### Step 4: Verify Deployment
1. Wait for deployment to complete (2-5 minutes)
2. Click on the service URL (e.g., `https://oracle-cloud-bot.onrender.com`)
3. You should see a JSON response:
```json
{
  "status": "healthy",
  "service": "Oracle Cloud Instance Creator",
  "message": "Web server is running. Use POST /trigger to attempt instance creation.",
  "cloud_account": "your-account-name",
  "email": "your-email@example.com"
}
```

## Setting Up External Cron Job

You need an external service to trigger your bot every 10 minutes. Here are the best free options:

### Option 1: cron-job.org (Recommended)
1. Go to https://cron-job.org
2. Sign up for free account
3. Click **"Create Cron Job"**
4. Configure:
   - **Title**: `Oracle Cloud Bot Trigger`
   - **URL**: `https://YOUR-RENDER-URL.onrender.com/trigger`
   - **Execution Schedule**: Every 10 minutes
   - **Request Method**: `GET`
5. Save and enable the cron job

### Option 2: EasyCron
1. Go to https://www.easycron.com
2. Sign up for free account (80 executions/day = every ~18 minutes)
3. Create new cron job with your `/trigger` URL

### Option 3: UptimeRobot
1. Go to https://uptimerobot.com
2. Sign up for free account
3. Add new monitor:
   - **Monitor Type**: HTTP(s)
   - **URL**: `https://YOUR-RENDER-URL.onrender.com/trigger`
   - **Monitoring Interval**: 5 minutes (free tier)

### Option 4: GitHub Actions (Advanced)
Create `.github/workflows/trigger-bot.yml`:
```yaml
name: Trigger Oracle Cloud Bot

on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Bot
        run: |
          curl https://YOUR-RENDER-URL.onrender.com/trigger
```

## Testing Your Setup

### Test Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python bot.py

# In another terminal, test the endpoints
curl http://localhost:10000/
curl http://localhost:10000/trigger
```

### Test on Render
```bash
# Health check
curl https://YOUR-RENDER-URL.onrender.com/

# Trigger instance creation
curl https://YOUR-RENDER-URL.onrender.com/trigger
```

## Expected Responses

### Success (Instance Created)
```json
{
  "status": "success",
  "message": "\"myfreevps\" VPS created successfully! IP: 123.45.67.89",
  "ip": "123.45.67.89",
  "instance_name": "myfreevps",
  "cloud_account": "your-account",
  "email": "your-email@example.com"
}
```

### Out of Capacity (Most Common)
```json
{
  "status": "out_of_capacity",
  "message": "Out of host capacity - will retry on next trigger",
  "error": "500 - OutOfHostCapacity - Out of host capacity..."
}
```

### Error (Configuration Issue)
```json
{
  "status": "error",
  "message": "Failed to check storage",
  "error": "401 - NotAuthenticated - ..."
}
```

## Important Notes

### Render Free Tier Limitations
- **Sleep after 15 minutes**: Free web services sleep after 15 minutes of inactivity
- **Wake-up time**: First request after sleep takes ~30 seconds
- **Solution**: Your cron job (every 10 minutes) will keep it awake

### Differences from Original Bot
| Feature | Original Bot | Web Server Version |
|---------|-------------|-------------------|
| Execution | Continuous loop | Triggered by HTTP request |
| Retry Logic | Infinite retries | Single attempt per trigger |
| Response Time | Immediate | Depends on cron frequency |
| Resource Usage | High (always running) | Low (runs on demand) |
| Render Compatibility | Requires paid plan | Works on free tier |

### Success Rate
- **Original bot**: Checks every 1-2 seconds until success
- **Web server**: Checks every 10 minutes (600 seconds)
- **Trade-off**: Lower success rate but completely free hosting

### Telegram Notifications
- Telegram notifications still work if you configure `bot_token` and `uid` in `bot.py`
- You'll receive a message when an instance is successfully created

## Troubleshooting

### "Service Unavailable" Error
- Your Render service might be sleeping
- Wait 30 seconds and try again
- Check Render logs for errors

### "Authentication Failed" Error
- Check your `config` file has correct OCI credentials
- Verify `private_key.pem` is present and valid
- Make sure files are committed to your Git repository

### No Response from Cron Job
- Verify your Render URL is correct
- Check cron job is enabled and running
- View Render logs to see if requests are received

### Instance Not Created After Many Attempts
- This is normal - Oracle Cloud capacity is limited
- Keep the cron job running - it will eventually succeed
- Check Render logs to confirm attempts are being made

## Monitoring

### View Render Logs
1. Go to Render Dashboard
2. Click on your service
3. Click **"Logs"** tab
4. You'll see each trigger attempt and its result

### Check Cron Job Status
- Most cron services provide execution history
- Verify requests are being sent successfully
- Check for any error responses

## Cost Analysis

| Service | Cost | Notes |
|---------|------|-------|
| Render Web Service | **FREE** | Free tier with limitations |
| Cron-job.org | **FREE** | Unlimited cron jobs |
| Oracle Cloud | **FREE** | Free tier (4 ARM cores, 24GB RAM) |
| **Total** | **$0/month** | Completely free! |

## Next Steps

1. ✅ Deploy to Render
2. ✅ Set up external cron job
3. ✅ Monitor logs for first few triggers
4. ✅ Wait for successful instance creation
5. ✅ Receive Telegram notification (if configured)
6. ✅ SSH into your new free VPS!

## Support

If you encounter issues:
1. Check Render logs for error messages
2. Verify OCI credentials are correct
3. Test the `/trigger` endpoint manually with curl
4. Ensure cron job is hitting the correct URL

Good luck! 🚀

