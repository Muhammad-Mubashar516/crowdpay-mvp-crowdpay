-- CrowdPay Database Setup for Supabase

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Campaigns Table
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    target_amount DECIMAL(15, 2) NOT NULL CHECK (target_amount > 0),
    current_amount DECIMAL(15, 2) NOT NULL DEFAULT 0 CHECK (current_amount >= 0),
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    creator_id VARCHAR(255) NOT NULL,
    creator_email VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled', 'expired')),
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Contributions Table
CREATE TABLE IF NOT EXISTS contributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    contributor_name VARCHAR(100),
    contributor_email VARCHAR(255),
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'failed', 'expired', 'cancelled')),
    bitnob_payment_id VARCHAR(255),
    bitnob_payment_request TEXT,
    bitnob_payment_hash VARCHAR(255),
    bitnob_reference VARCHAR(255),
    transaction_id VARCHAR(255),
    message TEXT,
    is_anonymous BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    paid_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_campaigns_creator_id ON campaigns(creator_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_contributions_campaign_id ON contributions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_contributions_payment_status ON contributions(payment_status);
CREATE INDEX IF NOT EXISTS idx_contributions_bitnob_payment_id ON contributions(bitnob_payment_id);
CREATE INDEX IF NOT EXISTS idx_contributions_bitnob_reference ON contributions(bitnob_reference);
CREATE INDEX IF NOT EXISTS idx_contributions_created_at ON contributions(created_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER update_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to check if campaign goal is reached and update status
CREATE OR REPLACE FUNCTION check_campaign_goal()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.current_amount >= (SELECT target_amount FROM campaigns WHERE id = NEW.id) THEN
        NEW.status = 'completed';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update campaign status when goal is reached
CREATE TRIGGER update_campaign_status_on_goal
    BEFORE UPDATE ON campaigns
    FOR EACH ROW
    WHEN (OLD.current_amount < NEW.current_amount)
    EXECUTE FUNCTION check_campaign_goal();

-- Comments for documentation
COMMENT ON TABLE campaigns IS 'Stores fundraising campaign information';
COMMENT ON TABLE contributions IS 'Stores individual contributions to campaigns';

COMMENT ON COLUMN campaigns.target_amount IS 'Fundraising goal amount';
COMMENT ON COLUMN campaigns.current_amount IS 'Current amount raised';
COMMENT ON COLUMN campaigns.status IS 'Campaign status: active, completed, cancelled, or expired';

COMMENT ON COLUMN contributions.payment_status IS 'Payment status: pending, paid, failed, expired, or cancelled';
COMMENT ON COLUMN contributions.bitnob_payment_id IS 'Bitnob API payment identifier';
COMMENT ON COLUMN contributions.bitnob_reference IS 'Unique reference for payment tracking';
COMMENT ON COLUMN contributions.is_anonymous IS 'Whether the contribution should be displayed anonymously';
