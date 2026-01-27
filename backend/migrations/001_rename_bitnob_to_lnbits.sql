-- Migration: Rename Bitnob columns to LNbits
-- Date: 2024
-- Description: Renames payment-related columns from bitnob_* to lnbits_*
--              for the LNbits Lightning payment integration

-- IMPORTANT: Run this migration AFTER deploying the new code
-- The new code is backward-compatible with old column names during transition

-- Step 1: Add new columns (if they don't exist)
-- This allows both old and new code to work during transition

ALTER TABLE contributions
ADD COLUMN IF NOT EXISTS lnbits_payment_hash VARCHAR(255);

ALTER TABLE contributions
ADD COLUMN IF NOT EXISTS lnbits_payment_request TEXT;

ALTER TABLE contributions
ADD COLUMN IF NOT EXISTS lnbits_checking_id VARCHAR(255);

-- Step 2: Copy data from old columns to new columns
UPDATE contributions
SET lnbits_payment_hash = bitnob_payment_hash
WHERE bitnob_payment_hash IS NOT NULL
  AND lnbits_payment_hash IS NULL;

UPDATE contributions
SET lnbits_payment_request = bitnob_payment_request
WHERE bitnob_payment_request IS NOT NULL
  AND lnbits_payment_request IS NULL;

UPDATE contributions
SET lnbits_checking_id = bitnob_payment_id
WHERE bitnob_payment_id IS NOT NULL
  AND lnbits_checking_id IS NULL;

-- Step 3: Create indexes on new columns
CREATE INDEX IF NOT EXISTS idx_contributions_lnbits_payment_hash
ON contributions(lnbits_payment_hash);

CREATE INDEX IF NOT EXISTS idx_contributions_lnbits_checking_id
ON contributions(lnbits_checking_id);

-- Step 4: Update column comments
COMMENT ON COLUMN contributions.lnbits_payment_hash IS 'LNbits payment hash - unique identifier for Lightning payment';
COMMENT ON COLUMN contributions.lnbits_payment_request IS 'BOLT11 Lightning invoice string';
COMMENT ON COLUMN contributions.lnbits_checking_id IS 'LNbits checking ID for payment status';

-- ============================================
-- OPTIONAL: Remove old columns after migration
-- ============================================
-- IMPORTANT: Only run this AFTER confirming new code is stable
-- and all data has been migrated

-- DROP INDEX IF EXISTS idx_contributions_bitnob_payment_id;
-- DROP INDEX IF EXISTS idx_contributions_bitnob_reference;

-- ALTER TABLE contributions DROP COLUMN IF EXISTS bitnob_payment_id;
-- ALTER TABLE contributions DROP COLUMN IF EXISTS bitnob_payment_request;
-- ALTER TABLE contributions DROP COLUMN IF EXISTS bitnob_payment_hash;
-- ALTER TABLE contributions DROP COLUMN IF EXISTS bitnob_reference;

-- ============================================
-- Rollback script (if needed)
-- ============================================
-- ALTER TABLE contributions DROP COLUMN IF EXISTS lnbits_payment_hash;
-- ALTER TABLE contributions DROP COLUMN IF EXISTS lnbits_payment_request;
-- ALTER TABLE contributions DROP COLUMN IF EXISTS lnbits_checking_id;
-- DROP INDEX IF EXISTS idx_contributions_lnbits_payment_hash;
-- DROP INDEX IF EXISTS idx_contributions_lnbits_checking_id;
