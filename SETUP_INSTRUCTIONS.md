# ✅ SETUP INSTRUCTIONS - Supabase Auth Integration

## What's Been Done

Your system now uses **Supabase Authentication** for all users:
- ✅ **Admin registration** → Creates user in Supabase Auth
- ✅ **Admin login** → Uses Supabase Auth
- ✅ **Outlet user signup** → Creates user in Supabase Auth
- ✅ **All users visible** in Supabase Dashboard → Authentication → Users

---

## 🚀 Quick Setup (2 Steps)

### **Step 1: Run SQL in Supabase** (1 minute)

1. Go to: https://supabase.com/dashboard
2. Select your project
3. Click: **SQL Editor** → **New Query**
4. Open file: `RUN_THIS_SQL_FIRST.sql`
5. Copy ALL contents
6. Paste in SQL Editor
7. Click: **RUN**

**You should see:** "SQL Migration Complete! Now update the code."

---

### **Step 2: Restart Server** (1 minute)

```bash
cd C:\Users\katar\Desktop\Production\Khanoos-KDS-main
.venv\Scripts\activate
uvicorn app.main:app --reload
```

**Done!** ✅

---

## 🧪 Test It Works

### **Test 1: Admin Registration**

Go to: http://localhost:8000/docs

Find: `POST /api/v1/admin-auth/register`

Try:
```json
{
  "email": "newadmin@example.com",
  "password": "AdminPass123",
  "full_name": "New Admin",
  "phone": "1234567890"
}
```

**Check Supabase Dashboard:**
1. Go to: **Authentication → Users**
2. You should see: `newadmin@example.com` ✅
3. User metadata shows: `user_type: "admin"`

---

### **Test 2: Admin Login**

Find: `POST /api/v1/admin-auth/login`

Try:
```json
{
  "email": "newadmin@example.com",
  "password": "AdminPass123"
}
```

**Should get:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "admin": {...},
    "access_token": "eyJ...",  ← Supabase token!
    "refresh_token": "...",
    "token_type": "bearer"
  }
}
```

---

### **Test 3: Outlet User Signup**

**First, create an outlet (as admin):**

Find: `POST /api/v1/outlets`

Use the access_token from admin login to authenticate.

**Then test outlet signup:**

Find: `POST /api/v1/licenses/outlet-signup`

Try:
```json
{
  "license_key": "your-license-key-here",
  "email": "outlet@example.com",
  "password": "OutletPass123",
  "full_name": "Outlet Owner"
}
```

**Check Supabase Dashboard:**
- You should see: `outlet@example.com` ✅
- User metadata shows: `user_type: "outlet_owner"`

---

## 📊 What Happens Now

### **For Admin Users:**

**Registration:**
```
1. Admin fills form
2. System creates user in Supabase Auth
3. User appears in Supabase Dashboard
4. Admin profile saved in admin_users table (with link to auth user)
5. Admin can login
```

**Login:**
```
1. Admin enters email/password
2. Supabase Auth verifies credentials
3. Returns Supabase session token
4. Token works with your API
```

---

### **For Outlet Users:**

**Signup (with license key):**
```
1. Outlet owner has license key from admin
2. Fills signup form with license key + password
3. System creates user in Supabase Auth
4. User appears in Supabase Dashboard
5. License activated
6. Outlet owner can login
```

**Login:**
```
1. Outlet owner enters email/password
2. Supabase Auth verifies credentials
3. Returns session token
4. Can access their outlet data
```

---

## 🎯 Benefits

### ✅ What You Get

1. **All users in one place**
   - Supabase Dashboard → Authentication → Users
   - See all admins and outlet owners

2. **Built-in features**
   - Email verification
   - Password reset
   - Session management

3. **Better security**
   - Supabase handles password hashing
   - No need to manage bcrypt yourself
   - Industry-standard security

4. **Easy to extend**
   - Add OAuth (Google, Facebook) later
   - Add Multi-Factor Auth (MFA)
   - Add magic links

---

## 📋 API Endpoints

### **Admin Endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/admin-auth/register` | POST | Register new admin (creates in Supabase Auth) |
| `/api/v1/admin-auth/login` | POST | Login admin (uses Supabase Auth) |
| `/api/v1/admin-auth/me` | GET | Get admin profile |

### **Outlet User Endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/licenses/outlet-signup` | POST | Signup with license key (creates in Supabase Auth) |
| `/api/v1/licenses/verify` | POST | Verify license key |

---

## ⚠️ Important Notes

### **Old Admin User**

If you created admin BEFORE this update:
- **Email:** `admin@khanoos.com`
- **Password:** `Admin123`
- **Status:** ❌ Won't work anymore (not in Supabase Auth)

**Solution:** Re-register with new system:
```json
POST /api/v1/admin-auth/register
{
  "email": "admin@khanoos.com",
  "password": "Admin123",
  "full_name": "Admin User",
  "phone": "1234567890"
}
```

---

## 🔍 Verification

### **Check User in Supabase Dashboard**

1. Go to: https://supabase.com/dashboard
2. Select your project
3. Click: **Authentication** → **Users**

**You should see:**
```
Users:
  - newadmin@example.com
    └─ user_metadata: { "user_type": "admin", "full_name": "..." }

  - outlet@example.com
    └─ user_metadata: { "user_type": "outlet_owner", "outlet_id": "..." }
```

---

## ✅ Success Checklist

After setup:
- [ ] SQL migration run successfully
- [ ] Server restarted without errors
- [ ] Admin registration creates user in Supabase Dashboard
- [ ] Admin login returns Supabase access_token
- [ ] Outlet signup creates user in Supabase Dashboard
- [ ] All users visible in Authentication section

---

## 🆘 Troubleshooting

### **Error: "column auth_user_id does not exist"**
**Fix:** Run the SQL migration (`RUN_THIS_SQL_FIRST.sql`)

### **Error: "Failed to create auth user"**
**Check:**
1. Supabase URL and keys in `.env` are correct
2. Supabase project is active
3. Email is not already registered

### **Users don't appear in dashboard**
**Check:**
1. Used correct endpoint (`/admin-auth/register` not old endpoint)
2. SQL migration was run
3. No errors in server logs

---

## 🎉 You're Done!

**Now:**
- ✅ All new users are created in Supabase Auth
- ✅ All users visible in Supabase Dashboard
- ✅ Login uses Supabase authentication
- ✅ Better security and features

**Next time you create an admin or outlet user:**
- They automatically appear in Supabase Dashboard → Authentication
- They can login using Supabase Auth
- You can manage them from the dashboard

---

**Setup Time:** 2 minutes
**Status:** Production Ready
**Users in Dashboard:** ✅ Yes!
