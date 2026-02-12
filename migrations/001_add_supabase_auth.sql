-- =============================================================================
-- SAFE MIGRATION: Add Supabase Auth Integration
-- Version: 1.0
-- Reversible: Yes
-- Breaking Changes: No
-- =============================================================================

-- This migration adds Supabase Auth support WITHOUT breaking existing system
-- Old password_hash column is KEPT for rollback safety

-- =============================================================================
-- 1. ADD NEW COLUMNS (Non-breaking)
-- =============================================================================

-- Add auth_user_id to admin_users (nullable, so existing records work)
ALTER TABLE admin_users
ADD COLUMN IF NOT EXISTS auth_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- Add auth_user_id to single_outlets (nullable, so existing records work)
ALTER TABLE single_outlets
ADD COLUMN IF NOT EXISTS auth_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- Add auth_user_id to chain_outlets (nullable, so existing records work)
ALTER TABLE chain_outlets
ADD COLUMN IF NOT EXISTS auth_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- =============================================================================
-- 2. ADD INDEXES (Performance optimization)
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_admin_users_auth_user_id
ON admin_users(auth_user_id) WHERE auth_user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_single_outlets_auth_user_id
ON single_outlets(auth_user_id) WHERE auth_user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_chain_outlets_auth_user_id
ON chain_outlets(auth_user_id) WHERE auth_user_id IS NOT NULL;

-- =============================================================================
-- 3. ADD UNIQUE CONSTRAINTS (Only for non-null values)
-- =============================================================================

-- This allows both old (password_hash) and new (auth_user_id) systems to coexist
CREATE UNIQUE INDEX IF NOT EXISTS admin_users_auth_user_id_unique
ON admin_users(auth_user_id) WHERE auth_user_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS single_outlets_auth_user_id_unique
ON single_outlets(auth_user_id) WHERE auth_user_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS chain_outlets_auth_user_id_unique
ON chain_outlets(auth_user_id) WHERE auth_user_id IS NOT NULL;

-- =============================================================================
-- 4. UPDATE RLS POLICIES (Add auth.uid() support)
-- =============================================================================

-- Allow users to read their own admin profile via auth.uid()
DROP POLICY IF EXISTS admin_users_select_own_auth ON admin_users;
CREATE POLICY admin_users_select_own_auth ON admin_users
  FOR SELECT TO authenticated
  USING (auth.uid() = auth_user_id OR auth.uid() = id);

-- Allow users to update their own admin profile via auth.uid()
DROP POLICY IF EXISTS admin_users_update_own_auth ON admin_users;
CREATE POLICY admin_users_update_own_auth ON admin_users
  FOR UPDATE TO authenticated
  USING (auth.uid() = auth_user_id OR auth.uid() = id);

-- Allow outlet users to access their own outlet
DROP POLICY IF EXISTS single_outlets_select_own ON single_outlets;
CREATE POLICY single_outlets_select_own ON single_outlets
  FOR SELECT TO authenticated
  USING (auth.uid() = auth_user_id);

DROP POLICY IF EXISTS single_outlets_update_own ON single_outlets;
CREATE POLICY single_outlets_update_own ON single_outlets
  FOR UPDATE TO authenticated
  USING (auth.uid() = auth_user_id);

-- =============================================================================
-- 5. CREATE HELPER FUNCTION (Check if using Supabase Auth)
-- =============================================================================

CREATE OR REPLACE FUNCTION is_using_supabase_auth(p_email TEXT)
RETURNS BOOLEAN AS $$
DECLARE
  v_admin admin_users%ROWTYPE;
BEGIN
  SELECT * INTO v_admin FROM admin_users WHERE email = p_email;

  IF NOT FOUND THEN
    RETURN FALSE;
  END IF;

  -- If auth_user_id is set, user is using Supabase Auth
  RETURN v_admin.auth_user_id IS NOT NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- ROLLBACK INSTRUCTIONS
-- =============================================================================

-- To rollback this migration, run:
/*

-- Remove new columns
ALTER TABLE admin_users DROP COLUMN IF EXISTS auth_user_id;
ALTER TABLE single_outlets DROP COLUMN IF EXISTS auth_user_id;
ALTER TABLE chain_outlets DROP COLUMN IF EXISTS auth_user_id;

-- Remove indexes
DROP INDEX IF EXISTS idx_admin_users_auth_user_id;
DROP INDEX IF EXISTS idx_single_outlets_auth_user_id;
DROP INDEX IF EXISTS idx_chain_outlets_auth_user_id;
DROP INDEX IF EXISTS admin_users_auth_user_id_unique;
DROP INDEX IF EXISTS single_outlets_auth_user_id_unique;
DROP INDEX IF EXISTS chain_outlets_auth_user_id_unique;

-- Remove helper function
DROP FUNCTION IF EXISTS is_using_supabase_auth(TEXT);

-- Restore original policies
DROP POLICY IF EXISTS admin_users_select_own_auth ON admin_users;
DROP POLICY IF EXISTS admin_users_update_own_auth ON admin_users;
DROP POLICY IF EXISTS single_outlets_select_own ON single_outlets;
DROP POLICY IF EXISTS single_outlets_update_own ON single_outlets;

-- Recreate original policies
CREATE POLICY admin_users_select_own ON admin_users
  FOR SELECT TO authenticated USING (auth.uid() = id);

CREATE POLICY admin_users_update_own ON admin_users
  FOR UPDATE TO authenticated USING (auth.uid() = id);

*/

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
  RAISE NOTICE '================================================================';
  RAISE NOTICE 'MIGRATION COMPLETE: Supabase Auth Integration';
  RAISE NOTICE '================================================================';
  RAISE NOTICE 'Changes:';
  RAISE NOTICE '  - Added auth_user_id columns (nullable)';
  RAISE NOTICE '  - Added indexes for performance';
  RAISE NOTICE '  - Updated RLS policies';
  RAISE NOTICE '  - Created helper function';
  RAISE NOTICE '';
  RAISE NOTICE 'Safety:';
  RAISE NOTICE '  - Old password_hash column PRESERVED';
  RAISE NOTICE '  - Existing data NOT modified';
  RAISE NOTICE '  - Fully reversible';
  RAISE NOTICE '';
  RAISE NOTICE 'Status: Both old and new auth systems can coexist';
  RAISE NOTICE '================================================================';
END $$;
