# ROLLBACK PLAN - Supabase Auth Integration

## Quick Rollback (If Needed)

### If something breaks, run these commands:

```bash
# 1. Stop the server
# Press Ctrl+C

# 2. Checkout backup files
git checkout app/services/admin_user_service.py.backup
git checkout app/routers/admin_auth.py.backup
git checkout app/auth/dependencies.py.backup

# 3. Restart server
uvicorn app.main:app --reload
```

## What's Backed Up

- ✅ Original service files (*.backup)
- ✅ Original router files (*.backup)
- ✅ Original auth files (*.backup)
- ✅ SQL schema kept password_hash column

## SQL Rollback

```sql
-- If you need to rollback SQL changes:

-- Remove new columns (if needed)
ALTER TABLE admin_users DROP COLUMN IF EXISTS auth_user_id;
ALTER TABLE single_outlets DROP COLUMN IF EXISTS auth_user_id;

-- System will work with old password_hash column
```

## Testing Before Full Cutover

1. Old endpoints still work: `/api/v1/admin-auth/*`
2. New endpoints at: `/api/v1/admin-auth-v2/*` (test first)
3. Switch when confident

## Recovery Steps

1. **Stop server**
2. **Restore backup files**
3. **Restart server**
4. **Old system works immediately**

---

**Created:** 2026-02-07
**Safe:** All changes reversible
**No data loss:** Old columns preserved
