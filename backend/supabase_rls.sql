-- Row Level Security (RLS) Configuration
-- Run this after the main schema setup

-- Enable RLS on sensitive tables
ALTER TABLE payment_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE contributions ENABLE ROW LEVEL SECURITY;

-- Public read access for payment links (for viewing campaigns)
CREATE POLICY "Public payment links are viewable by everyone" 
    ON payment_links FOR SELECT 
    USING (visibility = 'public');

-- Owners can manage their own payment links
CREATE POLICY "Users can insert their own payment links" 
    ON payment_links FOR INSERT 
    WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update their own payment links" 
    ON payment_links FOR UPDATE 
    USING (auth.uid() = owner_id);

-- Anyone can view contributions (for transparency)
CREATE POLICY "Contributions are viewable by everyone" 
    ON contributions FOR SELECT 
    USING (true);

-- Service role can insert contributions (from webhook)
CREATE POLICY "Service role can insert contributions" 
    ON contributions FOR INSERT 
    TO service_role 
    WITH CHECK (true);

-- Service role can update contributions (from webhook)
CREATE POLICY "Service role can update contributions" 
    ON contributions FOR UPDATE 
    TO service_role 
    USING (true);

-- Webhook events are only accessible by service role
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Only service role can access webhook events" 
    ON webhook_events 
    TO service_role 
    USING (true) 
    WITH CHECK (true);
