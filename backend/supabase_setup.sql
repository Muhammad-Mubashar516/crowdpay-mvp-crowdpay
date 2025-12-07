-- Crowdfunding Platform Database Schema
-- Run this in Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Payment Links Table
CREATE TABLE payment_links (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    owner_id UUID, -- Will integrate with Supabase Auth later
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    cover_url TEXT,
    goal_kes DECIMAL(15,2),
    goal_btc DECIMAL(15,8),
    current_amount_kes DECIMAL(15,2) DEFAULT 0,
    current_amount_btc DECIMAL(15,8) DEFAULT 0,
    visibility VARCHAR(20) DEFAULT 'public' CHECK (visibility IN ('public', 'private', 'unlisted')),
    theme JSONB DEFAULT '{}',
    end_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Contributions Table
CREATE TABLE contributions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    link_id UUID NOT NULL REFERENCES payment_links(id) ON DELETE CASCADE,
    amount_kes DECIMAL(15,2) NOT NULL,
    amount_btc DECIMAL(15,8),
    payment_method VARCHAR(50) NOT NULL,
    donor_name VARCHAR(255),
    donor_email VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending', 
        'payment_initiated', 
        'agent_matched', 
        'payment_pending', 
        'payment_confirmed', 
        'processing', 
        'completed', 
        'failed', 
        'disputed', 
        'cancelled'
    )),
    provider_reference TEXT, -- Store swap/invoice ID
    provider_data JSONB, -- Store full provider response
    error_message TEXT,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Webhook Events Table (for idempotency and debugging)
CREATE TABLE webhook_events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    event_type VARCHAR(100),
    payload JSONB NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX idx_payment_links_slug ON payment_links(slug);
CREATE INDEX idx_payment_links_owner_id ON payment_links(owner_id);
CREATE INDEX idx_contributions_link_id ON contributions(link_id);
CREATE INDEX idx_contributions_status ON contributions(status);
CREATE INDEX idx_webhook_events_provider ON webhook_events(provider);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_payment_links_updated_at 
    BEFORE UPDATE ON payment_links 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contributions_updated_at 
    BEFORE UPDATE ON contributions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update payment link totals when contributions change
CREATE OR REPLACE FUNCTION update_payment_link_totals()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the payment link totals
    UPDATE payment_links 
    SET 
        current_amount_kes = (
            SELECT COALESCE(SUM(amount_kes), 0) 
            FROM contributions 
            WHERE link_id = COALESCE(NEW.link_id, OLD.link_id) 
            AND status = 'completed'
        ),
        current_amount_btc = (
            SELECT COALESCE(SUM(amount_btc), 0) 
            FROM contributions 
            WHERE link_id = COALESCE(NEW.link_id, OLD.link_id) 
            AND status = 'completed'
        )
    WHERE id = COALESCE(NEW.link_id, OLD.link_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

CREATE TRIGGER update_payment_link_totals_trigger
    AFTER INSERT OR UPDATE OR DELETE ON contributions
    FOR EACH ROW EXECUTE FUNCTION update_payment_link_totals();

-- Insert sample data for testing
INSERT INTO payment_links (slug, title, description, goal_kes, visibility) VALUES
('help-john-startup', 'Help John Launch His Tech Startup', 'John needs funding to launch his innovative fintech app', 500000.00, 'public'),
('school-fees-mary', 'Mary''s School Fees', 'Help Mary complete her computer science degree', 150000.00, 'public');

COMMENT ON TABLE payment_links IS 'Crowdfunding payment links and campaigns';
COMMENT ON TABLE contributions IS 'Individual contributions to payment links';
COMMENT ON TABLE webhook_events IS 'Webhook events from payment providers for debugging and idempotency';
