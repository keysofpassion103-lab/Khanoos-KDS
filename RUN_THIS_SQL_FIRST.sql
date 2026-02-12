-- =============================================================================
-- CRITICAL: RUN THIS IN SUPABASE SQL EDITOR FIRST!
-- =============================================================================
-- Go to: Supabase Dashboard → SQL Editor → New Query
-- Copy this entire file and click RUN
-- =============================================================================

-- Add auth_user_id columns to link with Supabase Auth
ALTER TABLE admin_users
ADD COLUMN IF NOT EXISTS auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE single_outlets
ADD COLUMN IF NOT EXISTS auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE chain_outlets
ADD COLUMN IF NOT EXISTS auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Make password_hash nullable (for migration period)
ALTER TABLE admin_users
ALTER COLUMN password_hash DROP NOT NULL;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_admin_users_auth_user_id ON admin_users(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_single_outlets_auth_user_id ON single_outlets(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_chain_outlets_auth_user_id ON chain_outlets(auth_user_id);

-- Add unique constraints
CREATE UNIQUE INDEX IF NOT EXISTS admin_users_auth_user_id_unique
ON admin_users(auth_user_id) WHERE auth_user_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS single_outlets_auth_user_id_unique
ON single_outlets(auth_user_id) WHERE auth_user_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS chain_outlets_auth_user_id_unique
ON chain_outlets(auth_user_id) WHERE auth_user_id IS NOT NULL;

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'SQL Migration Complete! Now update the code.';
END $$;
