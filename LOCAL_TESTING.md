# Local Testing Guide

## Quick Test (3 Steps)

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Start the Server
```powershell
python bot.py
```

You should see:
```
[INFO] ... - Starting Flask web server on port 10000
[INFO] ... - Endpoints:
[INFO] ... -   GET / - Health check
[INFO] ... -   GET /trigger - Trigger instance creation
 * Running on http://127.0.0.1:10000
```

### Step 3: Test the Endpoints

**Option A: Using Web Browser (Easiest)**

1. Open your browser and go to: **http://localhost:10000/**
   - You should see JSON response with "status": "healthy"

2. Go to: **http://localhost:10000/trigger**
   - This will attempt to create an Oracle Cloud instance
   - You'll see the result in JSON format

**Option B: Using curl (Command Line)**

Open a **new terminal** (keep the server running) and run:

```powershell
# Test health check
curl http://localhost:10000/

# Test trigger endpoint
curl http://localhost:10000/trigger
```

**Option C: Using the Test Script**

```powershell
python test_server.py
```

Follow the prompts to test both endpoints.

## Expected Responses

### Health Check (GET /)
```json
{
  "status": "healthy",
  "service": "Oracle Cloud Instance Creator",
  "message": "Web server is running. Use POST /trigger to attempt instance creation.",
  "cloud_account": "your-account-name",
  "email": "your-email@example.com"
}
```

### Trigger - Out of Capacity (Most Common)
```json
{
  "status": "out_of_capacity",
  "message": "Out of host capacity - will retry on next trigger",
  "error": "500 - OutOfHostCapacity - Out of host capacity..."
}
```

### Trigger - Success
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

### Trigger - Error (Configuration Issue)
```json
{
  "status": "error",
  "message": "Failed to check storage",
  "error": "401 - NotAuthenticated - ..."
}
```

## Troubleshooting

### Server Won't Start

**Error: "Failed to initialize OCI clients"**
```
Solution: Check your Oracle Cloud credentials
- Make sure `config` file exists
- Make sure `private_key.pem` file exists
- Verify the credentials are correct
```

**Error: "Address already in use"**
```
Solution: Port 10000 is being used by another application
- Close the other application
- Or change the port in bot.py (line 330)
```

### Can't Connect to Server

**Error: "Connection refused"**
```
Solution: Make sure the server is running
- Run: python bot.py
- Wait for "Running on http://127.0.0.1:10000" message
```

### Trigger Returns Error

**Error: "Authentication Failed"**
```
Solution: OCI credentials are incorrect
- Sign up at https://cloud.oracle.com
- Download your config and private key
- Update the files in your project
```

**Error: "Duplicate display name"**
```
Solution: An instance with this name already exists
- Change displayName in bot.py (line 3)
- Or delete the existing instance in Oracle Cloud
```

**Error: "Resource limit exceeded"**
```
Solution: You've reached the free tier limit
- Free tier: 4 ARM cores + 24GB RAM total
- Delete existing instances to free up resources
```

## What to Watch in Server Logs

When you trigger the endpoint, the server terminal will show:

```
============================================================
Instance creation triggered via HTTP request
============================================================
[INFO] ... - Check available storage in account
[INFO] ... - Check current instances in account
[INFO] ... - No instance(s) found!
[INFO] ... - Total ocpus: 0 - Total memory: 0 GB || Free 4 ocpus - Free memory: 24 GB
[INFO] ... - Precheck pass! Attempting to create VM.Standard.A1.Flex: 4 ocpus - 24 GB
[INFO] ... - Attempting to launch instance in Jmgg:AP-SINGAPORE-1-AD-1...
[INFO] ... - 500 - OutOfHostCapacity - Out of host capacity...
```

This is exactly what will happen on Render when your cron job triggers it!

## Testing Different Scenarios

### Test 1: Health Check Only
```powershell
curl http://localhost:10000/
```
Should return immediately with "healthy" status.

### Test 2: Single Trigger Attempt
```powershell
curl http://localhost:10000/trigger
```
Takes 5-60 seconds depending on Oracle's response.

### Test 3: Multiple Triggers (Simulate Cron)
```powershell
# Windows PowerShell
for ($i=1; $i -le 5; $i++) {
    Write-Host "Attempt $i"
    curl http://localhost:10000/trigger
    Start-Sleep -Seconds 10
}
```

This simulates what your cron job will do every 10 minutes.

## Next Steps After Local Testing

Once local testing works:

1. ✅ **Commit your code to Git**
   ```bash
   git add .
   git commit -m "Web server ready for deployment"
   git push
   ```

2. ✅ **Deploy to Render**
   - See QUICK_START.md for deployment steps

3. ✅ **Set up Cron Job**
   - Use cron-job.org to hit your Render URL every 10 minutes

4. ✅ **Monitor Logs**
   - Check Render logs to see attempts
   - Wait for success notification

## Tips

- **Keep the server running** while testing
- **Use Ctrl+C** to stop the server
- **Check server logs** for detailed information
- **Test health check first** before testing trigger
- **Be patient** - Oracle capacity is limited, out of capacity is normal

## Common Questions

**Q: How long does /trigger take?**
A: Usually 5-10 seconds for "out of capacity", 60+ seconds if successful (needs to wait for IP assignment).

**Q: Can I test without Oracle Cloud credentials?**
A: No, the server needs valid OCI credentials to initialize.

**Q: Will testing create actual instances?**
A: Yes! The /trigger endpoint attempts real instance creation. But it will likely fail with "out of capacity" during testing.

**Q: How many times should I test?**
A: Test health check once, trigger 2-3 times to see the response. Don't spam it - save that for the cron job!

---

**Ready to deploy?** See QUICK_START.md for deployment instructions!

