# Quick Start Guide - 5 Minutes to Deploy

## What Changed?

Your bot is now a **web server** instead of a background worker. This means:
- ✅ Works on Render's **FREE** tier
- ✅ Triggered by external cron jobs every 10 minutes
- ✅ No infinite loops (single attempt per trigger)
- ✅ All configuration is hardcoded (no environment variables needed)

## Deploy in 5 Steps

### 1. Push to GitHub (2 minutes)
```bash
git init
git add .
git commit -m "Convert to web server"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2. Deploy on Render (2 minutes)
1. Go to https://render.com and sign up
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo
4. Select **"Free"** plan
5. Click **"Create Web Service"**
6. Wait for deployment (2-3 minutes)

### 3. Test Your Deployment (30 seconds)
Visit your Render URL (e.g., `https://your-app.onrender.com`)

You should see:
```json
{
  "status": "healthy",
  "service": "Oracle Cloud Instance Creator",
  "message": "Web server is running..."
}
```

### 4. Set Up Cron Job (1 minute)
1. Go to https://cron-job.org and sign up
2. Click **"Create Cron Job"**
3. Enter:
   - **URL**: `https://your-app.onrender.com/trigger`
   - **Schedule**: Every 10 minutes
   - **Method**: GET
4. Save and enable

### 5. Monitor (Ongoing)
- Check Render logs to see attempts
- Wait for Telegram notification (if configured)
- Instance will be created when capacity is available

## Test Locally (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python bot.py

# Test in another terminal
curl http://localhost:10000/
curl http://localhost:10000/trigger
```

## Files Modified

| File | Change |
|------|--------|
| `bot.py` | Converted to Flask web server |
| `requirements.txt` | Added Flask and Gunicorn |
| `Procfile` | Changed from `worker:` to `web:` |

## How It Works Now

**Before (Background Worker):**
```
Start → Infinite Loop → Check capacity every 1-2 seconds → Create instance → Exit
```

**After (Web Server):**
```
Start → Wait for HTTP request → Check capacity once → Return result → Wait for next request
```

**With Cron Job:**
```
Cron triggers every 10 minutes → Bot checks capacity → Returns result → Repeat
```

## Important Notes

1. **No Oracle Account Yet?** 
   - You need to sign up at https://cloud.oracle.com
   - Update `config` and `private_key.pem` files with your credentials
   - Update hardcoded values in `bot.py` (compartmentId, subnetId, etc.)

2. **Telegram Notifications (Optional)**
   - Set `bot_token` and `uid` in `bot.py` to receive notifications
   - Leave as `"xxxx"` to disable

3. **Free Tier Limits**
   - Render: Service sleeps after 15 min inactivity (cron keeps it awake)
   - Oracle: 4 ARM cores + 24GB RAM total (or 2 AMD VMs)
   - Cron-job.org: Unlimited free cron jobs

## Troubleshooting

**"Service Unavailable"**
- Service is waking up from sleep (wait 30 seconds)

**"Authentication Failed"**
- Check `config` and `private_key.pem` files
- Verify OCI credentials are correct

**No Instance Created After Hours**
- This is normal! Oracle capacity is limited
- Keep cron job running - it will eventually succeed
- Original bot had same issue, just checked more frequently

## What's Next?

1. ✅ Deploy to Render
2. ✅ Set up cron job
3. ✅ Monitor logs
4. ✅ Wait for success notification
5. ✅ SSH into your free VPS!

## Need Help?

See `DEPLOYMENT_GUIDE.md` for detailed instructions and troubleshooting.

---

**Total Cost: $0/month** 🎉

