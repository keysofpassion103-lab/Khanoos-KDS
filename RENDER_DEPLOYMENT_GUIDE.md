# Khanoos KDS Backend - Render Deployment Guide

## Overview
This guide will help you deploy the Khanoos KDS FastAPI backend to Render.com. Render provides free hosting for web services with easy deployment from Git repositories.

---

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **Git Repository**: Push your code to GitHub, GitLab, or Bitbucket
3. **Supabase Project**: Ensure your Supabase database is set up and accessible

---

## Step 1: Prepare Your Project

### 1.1 Create `render.yaml` (Optional but Recommended)

Create a `render.yaml` file in your project root for infrastructure-as-code deployment:

```yaml
services:
  - type: web
    name: khanoos-kds-backend
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: SECRET_KEY
        sync: false
      - key: ADMIN_SECRET_KEY
        sync: false
      - key: ALGORITHM
        value: HS256
      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: 3600
      - key: REFRESH_TOKEN_EXPIRE_DAYS
        value: 7
      - key: API_VERSION
        value: v1
      - key: DEBUG
        value: False
```

### 1.2 Create/Update `requirements.txt`

Your existing `requirements.txt` is already good. Ensure it includes:
```txt
fastapi==0.109.0
uvicorn==0.27.0
supabase==2.16.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
passlib==1.7.4
bcrypt==3.2.2
python-jose==3.3.0
PyJWT==2.11.0
# ... (rest of your dependencies)
```

### 1.3 Verify Python Version

Create a `runtime.txt` file to specify Python version:
```txt
python-3.11.0
```

---

## Step 2: Deploy to Render

### Method A: Using Render Dashboard (Recommended for First Deploy)

1. **Login to Render**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click "New +" → "Web Service"

2. **Connect Repository**
   - Connect your GitHub/GitLab/Bitbucket account
   - Select your Khanoos-KDS repository
   - Click "Connect"

3. **Configure Service**
   - **Name**: `khanoos-kds-backend` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your production branch)
   - **Runtime**: Python 3
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free (or paid plan for production)

4. **Add Environment Variables**

   Click "Advanced" → "Add Environment Variable" and add each:

   | Key | Value | Notes |
   |-----|-------|-------|
   | `SUPABASE_URL` | `https://xccnmjisskbldlalidlr.supabase.co` | Your Supabase project URL |
   | `SUPABASE_KEY` | `eyJhbGci...` | Your Supabase anon key |
   | `SUPABASE_SERVICE_KEY` | `eyJhbGci...` | Your Supabase service role key |
   | `SECRET_KEY` | `btpKbAOgY...` | JWT secret key (use secrets generator) |
   | `ADMIN_SECRET_KEY` | `9ug8f2VFY...` | Admin JWT secret |
   | `ALGORITHM` | `HS256` | JWT algorithm |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `3600` | Token expiry (60 mins) |
   | `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token expiry |
   | `API_VERSION` | `v1` | API version |
   | `DEBUG` | `False` | **IMPORTANT: Set to False in production** |
   | `PYTHON_VERSION` | `3.11.0` | Python version |

   **Security Note**: Generate new secret keys for production:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your app
   - Monitor the build logs for any errors

### Method B: Using `render.yaml` (Infrastructure as Code)

1. Push `render.yaml` to your repository root
2. In Render Dashboard, click "New +" → "Blueprint"
3. Connect your repository
4. Render will automatically detect `render.yaml` and configure everything
5. Add secret environment variables manually (they won't be in render.yaml)

---

## Step 3: Configure CORS for Production

After deployment, update your CORS settings in `app/main.py`:

```python
# Update CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com",  # Your production frontend
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push this change to trigger a new deployment.

---

## Step 4: Verify Deployment

### 4.1 Check Health Endpoints

Your app will be available at: `https://khanoos-kds-backend.onrender.com`

Test these endpoints:
```bash
# Root endpoint
curl https://your-app-name.onrender.com/

# Health check
curl https://your-app-name.onrender.com/health

# API Documentation
# Visit: https://your-app-name.onrender.com/docs
```

### 4.2 Test API Endpoints

```bash
# Test admin registration
curl -X POST https://your-app-name.onrender.com/api/v1/admin-auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "securePassword123",
    "full_name": "Admin User"
  }'
```

---

## Step 5: Database Configuration (Supabase)

### 5.1 Update Supabase CORS Settings

In Supabase Dashboard:
1. Go to Settings → API
2. Add your Render URL to allowed domains:
   - `https://your-app-name.onrender.com`

### 5.2 Verify RLS Policies

Ensure your Row Level Security policies allow service role access:
- Service role key bypasses RLS (already configured)
- Anon key respects RLS policies

---

## Step 6: Post-Deployment Configuration

### 6.1 Custom Domain (Optional)

1. In Render Dashboard → Your Service → Settings
2. Click "Custom Domains"
3. Add your domain (e.g., `api.khanoos.com`)
4. Follow DNS configuration instructions
5. Render provides free SSL certificates

### 6.2 Persistent Storage (If Needed)

For file uploads or logs:
1. In Render Dashboard → Your Service
2. Click "Disks"
3. Add a disk mount (Free tier: 1GB included)

### 6.3 Monitoring

1. **Logs**: View in Render Dashboard → Logs tab
2. **Metrics**: View in Render Dashboard → Metrics tab
3. **Alerts**: Set up in Settings → Notifications

---

## Important Notes

### Free Tier Limitations
- **Cold Starts**: Free services spin down after 15 minutes of inactivity
  - First request after inactivity may take 30-60 seconds
  - Consider upgrading to paid plan ($7/month) for always-on service
- **750 hours/month**: Free tier limit
- **Build time**: 5 minutes per deployment

### Environment Variables Security
- **Never commit** `.env` file to Git
- Store secrets in Render's environment variable settings
- Rotate keys regularly
- Use different keys for staging/production

### Auto-Deploy
Render automatically deploys when you push to your connected branch:
- Push to `main` → Auto-deploy
- Can disable in Settings → Deploy if needed

---

## Troubleshooting

### Build Fails

**Error**: `ModuleNotFoundError`
```bash
# Solution: Ensure all dependencies are in requirements.txt
pip freeze > requirements.txt
```

**Error**: Python version mismatch
```bash
# Solution: Create runtime.txt with:
python-3.11.0
```

### App Won't Start

**Error**: `Address already in use`
```bash
# Solution: Use Render's $PORT variable
# Start command should be:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Error**: `Config validation error`
```bash
# Solution: Verify all required environment variables are set in Render Dashboard
# Check Settings → Environment → Environment Variables
```

### Database Connection Issues

**Error**: `Could not connect to Supabase`
- Verify `SUPABASE_URL` and keys are correct
- Check Supabase project status
- Verify network connectivity

### Authentication Errors

**Error**: `Invalid JWT token`
- Ensure `SECRET_KEY` and `ADMIN_SECRET_KEY` match across all environments
- Check token expiration settings
- Verify Supabase Auth is configured correctly

### CORS Errors

**Error**: `CORS policy blocked`
- Update `allow_origins` in `app/main.py`
- Add your frontend domain to allowed origins
- Redeploy after changes

---

## Useful Commands

### View Logs
```bash
# Install Render CLI
npm install -g render-cli

# Login
render login

# View logs
render logs -s your-service-name
```

### Manual Redeploy
```bash
# From Render Dashboard
Click "Manual Deploy" → "Deploy latest commit"

# Or using API
curl -X POST https://api.render.com/v1/services/your-service-id/deploys \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Production Checklist

Before going live:

- [ ] Set `DEBUG=False` in environment variables
- [ ] Update CORS origins to specific domains
- [ ] Generate new production secret keys
- [ ] Configure custom domain
- [ ] Set up monitoring and alerts
- [ ] Test all API endpoints
- [ ] Verify Supabase RLS policies
- [ ] Review and optimize database indexes
- [ ] Set up backup strategy
- [ ] Document API for frontend team
- [ ] Load test the application
- [ ] Configure rate limiting (if needed)

---

## Support Resources

- **Render Documentation**: https://render.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Supabase Docs**: https://supabase.com/docs
- **Render Community**: https://community.render.com/

---

## Next Steps

1. **Frontend Deployment**: Deploy your frontend (React/Next.js) to Vercel/Netlify
2. **CI/CD**: Set up GitHub Actions for testing before deployment
3. **Monitoring**: Integrate Sentry or LogRocket for error tracking
4. **Performance**: Add Redis caching with Render's Redis addon
5. **Scaling**: Upgrade to paid plan when traffic increases

---

## Estimated Deployment Time

- Initial setup: 10-15 minutes
- First deployment: 5-10 minutes (depending on dependencies)
- Subsequent deployments: 2-5 minutes

---

**Your API will be live at**: `https://your-app-name.onrender.com`
**API Documentation**: `https://your-app-name.onrender.com/docs`

Good luck with your deployment! 🚀
