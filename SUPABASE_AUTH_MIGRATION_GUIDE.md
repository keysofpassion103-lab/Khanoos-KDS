# Supabase Auth Migration Guide

## ✅ Safe Implementation Complete!

**Status:** Both V1 (old) and V2 (new) systems are running side-by-side

### What's Been Done

1. ✅ **SQL Migration Created** (not applied yet)
2. ✅ **V2 Service Created** (admin_user_service_v2.py)
3. ✅ **V2 Router Created** (admin_auth_v2.py)
4. ✅ **Backups Created** (*.backup files)
5. ✅ **Rollback Plan** (documented)
6. ✅ **Both Systems Active** (can test V2 without breaking V1)

---

## 🎯 Next Steps

### Step 1: Run SQL Migration

**Go to Supabase Dashboard:**
1. Open https://supabase.com/dashboard
2. Select your project
3. Go to **SQL Editor**
4. Open the file: `migrations/001_add_supabase_auth.sql`
5. Copy and paste into SQL Editor
6. Click **RUN**

**What this does:**
- ✅ Adds `auth_user_id` column (keeps `password_hash`)
- ✅ Adds indexes for performance
- ✅ Updates RLS policies
- ✅ **Fully reversible** (rollback included in file)

---

### Step 2: Test V2 System

**Restart your server:**
```bash
cd C:\Users\katar\Desktop\Production\Khanoos-KDS-main
.venv\Scripts\activate
uvicorn app.main:app --reload
```

**Go to:** http://localhost:8000/docs

You'll now see **TWO** sets of admin auth endpoints:

#### 📁 V1 Endpoints (Old - Still Working)
- `POST /api/v1/admin-auth/register` ← Uses bcrypt
- `POST /api/v1/admin-auth/login` ← Uses custom JWT

#### 📁 V2 Endpoints (New - Supabase Auth)
- `POST /api/v1/admin-auth-v2/register` ← Uses Supabase Auth ✨
- `POST /api/v1/admin-auth-v2/login` ← Uses Supabase Auth ✨
- `POST /api/v1/admin-auth-v2/password-reset-request` ← NEW feature! ✨

---

### Step 3: Test V2 Registration

**Try creating a new admin with V2:**

```json
POST /api/v1/admin-auth-v2/register
{
  "email": "testadmin@example.com",
  "password": "TestPass123",
  "full_name": "Test Admin V2",
  "phone": "1234567890"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Admin registered successfully. Check email for verification link.",
  "data": {
    "admin": {
      "id": "...",
      "email": "testadmin@example.com",
      "full_name": "Test Admin V2",
      ...
    },
    "session": {
      "access_token": "eyJ...",
      "refresh_token": "...",
      "token_type": "bearer"
    }
  }
}
```

**Check Supabase Dashboard:**
1. Go to **Authentication → Users**
2. You should see `testadmin@example.com` ✅
3. User will have metadata: `user_type: "admin"`

---

### Step 4: Test V2 Login

```json
POST /api/v1/admin-auth-v2/login
{
  "email": "testadmin@example.com",
  "password": "TestPass123"
}
```

**Should return:**
- ✅ Supabase access_token
- ✅ Admin profile data
- ✅ Refresh token

---

### Step 5: Verify Old System Still Works

**Test V1 endpoints to ensure nothing broke:**

```json
POST /api/v1/admin-auth/login
{
  "email": "admin@khanoos.com",
  "password": "Admin123"
}
```

**Should still work:** ✅
- Old admin users can still login
- Old system unchanged

---

## 🔄 Comparison: V1 vs V2

| Feature | V1 (Old) | V2 (New) |
|---------|----------|----------|
| **Password Storage** | Custom bcrypt | Supabase (more secure) |
| **Tokens** | Custom JWT | Supabase session |
| **Visible in Dashboard** | ❌ No | ✅ Yes |
| **Email Verification** | ❌ No | ✅ Yes |
| **Password Reset** | ❌ No | ✅ Yes |
| **OAuth (Google, etc.)** | ❌ No | ✅ Ready |
| **MFA** | ❌ No | ✅ Available |
| **Session Management** | Manual | Automatic |

---

## 🚀 When You're Ready to Switch

### Option A: Gradual Migration (Recommended)

1. **Keep both systems active**
2. **Create new admins with V2**
3. **Old admins keep using V1**
4. **Eventually migrate all to V2**

### Option B: Full Switch

**When ALL admins have been recreated with V2:**

1. **Remove V1 router from main.py:**
   ```python
   # Comment out V1 router
   # app.include_router(admin_auth.router, prefix=f"/api/{settings.API_VERSION}")
   ```

2. **Rename V2 endpoints (optional):**
   - Change `/admin-auth-v2/*` to `/admin-auth/*`

3. **Remove old code:**
   ```bash
   rm app/services/admin_user_service.py.backup
   rm app/routers/admin_auth.py.backup
   ```

---

## 🛡️ Safety Features

### ✅ What's Protected

1. **Old System Unchanged**
   - V1 endpoints work exactly as before
   - Existing admin users unaffected
   - No breaking changes

2. **Data Preserved**
   - `password_hash` column still exists
   - Old admins can still login
   - No data loss

3. **Easy Rollback**
   ```bash
   # If you need to rollback:
   git checkout app/main.py
   # Remove V2 router line
   # Restart server
   ```

4. **SQL Reversible**
   - Rollback SQL included in migration file
   - Just run the commented-out section

---

## 📊 Testing Checklist

- [ ] SQL migration run successfully
- [ ] Server restarted
- [ ] V2 registration works
- [ ] User appears in Supabase Dashboard
- [ ] V2 login works
- [ ] V1 login still works (old admin)
- [ ] Both systems coexist peacefully

---

## ⚠️ Important Notes

### For Production

1. **Don't delete V1 immediately**
   - Keep both systems for transition period
   - Let users migrate gradually

2. **Supabase Email Settings**
   - Configure in: Supabase Dashboard → Authentication → Email Templates
   - Customize verification and password reset emails

3. **Domain Configuration**
   - Set site URL in: Supabase Dashboard → Settings → URL Configuration
   - For password reset links to work correctly

### Migration for Existing Admins

**Old admin:** `admin@khanoos.com` (V1 - bcrypt)

**Options:**
1. **Ask them to re-register** with V2
2. **They keep using V1** (works indefinitely)
3. **Create migration script** (advanced)

---

## 🆘 Troubleshooting

### Issue: "User not found in admin_users table"
**Fix:** Make sure SQL migration was run

### Issue: "Email already registered"
**Cause:** User exists in V1 system
**Fix:** Use a different email for V2 testing

### Issue: Users don't appear in dashboard
**Check:**
1. SQL migration was run
2. Registration used V2 endpoint (`/admin-auth-v2/register`)
3. No errors in server logs

### Issue: Want to rollback
**Steps:**
1. See `ROLLBACK_PLAN.md`
2. Remove V2 router from main.py
3. Restart server

---

## 📞 Support

If you encounter issues:

1. **Check logs:** Server console output
2. **Check Supabase logs:** Dashboard → Logs
3. **Verify SQL migration:** Check if columns exist
4. **Test V1:** Make sure old system still works

---

## ✅ Success Criteria

**You'll know it's working when:**

1. ✅ New admin registration creates user in Supabase Dashboard
2. ✅ Login returns Supabase session token
3. ✅ Old system still works
4. ✅ Both systems run side-by-side
5. ✅ Can rollback anytime

---

**Implementation Date:** 2026-02-07
**Status:** Ready for Testing
**Risk Level:** ✅ Low (Fully reversible)
**Downtime:** ✅ None (Both systems active)
