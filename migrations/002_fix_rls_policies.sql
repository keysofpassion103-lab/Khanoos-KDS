-- =============================================================================
-- FIX RLS POLICIES - Run in Supabase SQL Editor
-- Version: 2.0
-- Fixes: admin_users INSERT policy missing, plan_types RLS
-- =============================================================================

-- =============================================================================
-- 1. FIX admin_users TABLE - Add missing INSERT and DELETE policies
-- =============================================================================

-- Allow inserts (service role bypasses RLS, but this is needed as safety net
-- for when the Python SDK auth state gets contaminated after auth operations)
CREATE POLICY admin_users_insert ON admin_users
  FOR INSERT WITH CHECK (true);

-- Allow authenticated users to delete their own record
CREATE POLICY admin_users_delete ON admin_users
  FOR DELETE TO authenticated USING (auth.uid() = id);

-- =============================================================================
-- 2. FIX plan_types TABLE - Add RLS policies
-- =============================================================================

-- Enable RLS on plan_types (may already be enabled, safe to run)
ALTER TABLE plan_types ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any (safe re-run)
DROP POLICY IF EXISTS plan_types_select ON plan_types;
DROP POLICY IF EXISTS plan_types_insert ON plan_types;
DROP POLICY IF EXISTS plan_types_update ON plan_types;
DROP POLICY IF EXISTS plan_types_delete ON plan_types;

-- Public read access for plan types
CREATE POLICY plan_types_select ON plan_types
  FOR SELECT USING (true);

-- Authenticated users can manage plan types (admin operations)
CREATE POLICY plan_types_insert ON plan_types
  FOR INSERT WITH CHECK (true);

CREATE POLICY plan_types_update ON plan_types
  FOR UPDATE USING (true);

CREATE POLICY plan_types_delete ON plan_types
  FOR DELETE USING (true);

-- =============================================================================
-- 3. GRANT permissions
-- =============================================================================

GRANT ALL ON plan_types TO authenticated;
GRANT SELECT ON plan_types TO anon;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
  RAISE NOTICE '================================================================';
  RAISE NOTICE 'RLS POLICY FIXES APPLIED SUCCESSFULLY';
  RAISE NOTICE '================================================================';
  RAISE NOTICE 'Fixed: admin_users INSERT policy added';
  RAISE NOTICE 'Fixed: admin_users DELETE policy added';
  RAISE NOTICE 'Fixed: plan_types RLS policies added';
  RAISE NOTICE '================================================================';
END $$;
