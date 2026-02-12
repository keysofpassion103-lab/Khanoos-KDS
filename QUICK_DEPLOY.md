# Quick Deploy to Render - Khanoos KDS Backend

## TL;DR - Fast Track Deployment

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit for Render deployment"
git remote add origin https://github.com/YOUR_USERNAME/khanoos-kds.git
git push -u origin main
```

### 2. Deploy on Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Use these settings:

**Basic Settings:**
```
Name: khanoos-kds-backend
Runtime: Python 3
Branch: main
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables** (Add these in "Advanced" settings):
```
SUPABASE_URL = <your-supabase-url>
SUPABASE_KEY = <your-supabase-anon-key>
SUPABASE_SERVICE_KEY = <your-supabase-service-key>
SECRET_KEY = <generate-new-secret>
ADMIN_SECRET_KEY = <generate-new-secret>
ALGORITHM = HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 3600
REFRESH_TOKEN_EXPIRE_DAYS = 7
API_VERSION = v1
DEBUG = False
```

5. Click **"Create Web Service"**
6. Wait 5-10 minutes for deployment

### 3. Test Your API

Your API will be live at: `https://your-app-name.onrender.com`

Test it:
```bash
curl https://your-app-name.onrender.com/health
```

Visit API docs: `https://your-app-name.onrender.com/docs`

---

## Generate New Secret Keys

**DO NOT use the keys from your `.env` file in production!**

Generate new ones:
```bash
# For SECRET_KEY and ADMIN_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Run this command twice and use the outputs for your secret keys.

---

## Important Notes

- **Free Tier**: App sleeps after 15 min of inactivity (first request will be slow)
- **Auto-Deploy**: Pushes to `main` branch auto-deploy
- **Logs**: View in Render Dashboard → Your Service → Logs
- **DEBUG**: Make sure it's set to `False` in production!

---

## Environment Variables Checklist

Copy these and replace with your actual values:

```env
SUPABASE_URL=https://xccnmjisskbldlalidlr.supabase.co
SUPABASE_KEY=eyJhbGci...  # Your anon key
SUPABASE_SERVICE_KEY=eyJhbGci...  # Your service role key
SECRET_KEY=<NEW_64_CHAR_SECRET>  # Generate new!
ADMIN_SECRET_KEY=<NEW_64_CHAR_SECRET>  # Generate new!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=3600
REFRESH_TOKEN_EXPIRE_DAYS=7
API_VERSION=v1
DEBUG=False
```

---

## Troubleshooting

**Build fails?**
- Check `requirements.txt` has all dependencies
- Verify Python version in `runtime.txt` is 3.11.0

**App won't start?**
- Make sure start command uses `$PORT` variable
- Check all environment variables are set

**Can't connect to Supabase?**
- Verify Supabase URL and keys are correct
- Check Supabase project is active

---

For detailed deployment guide, see **RENDER_DEPLOYMENT_GUIDE.md**

Done! 🚀
