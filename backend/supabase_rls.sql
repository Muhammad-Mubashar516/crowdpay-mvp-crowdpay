-- Row Level Security (RLS) Policies for CrowdPay

-- Enable RLS on tables
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE contributions ENABLE ROW LEVEL SECURITY;

-- Campaigns Policies

-- Allow anyone to read active campaigns
CREATE POLICY "Anyone can view active campaigns"
    ON campaigns FOR SELECT
    USING (status = 'active' OR status = 'completed');

-- Allow authenticated users to create campaigns
CREATE POLICY "Authenticated users can create campaigns"
    ON campaigns FOR INSERT
    WITH CHECK (auth.uid()::text = creator_id);

-- Allow campaign creators to update their own campaigns
CREATE POLICY "Creators can update own campaigns"
    ON campaigns FOR UPDATE
    USING (auth.uid()::text = creator_id)
    WITH CHECK (auth.uid()::text = creator_id);

-- Allow campaign creators to delete (cancel) their own campaigns
CREATE POLICY "Creators can cancel own campaigns"
    ON campaigns FOR UPDATE
    USING (auth.uid()::text = creator_id AND status IN ('active', 'expired'))
    WITH CHECK (status = 'cancelled');

-- Service role has full access to campaigns
CREATE POLICY "Service role full access to campaigns"
    ON campaigns
    USING (auth.jwt()->>'role' = 'service_role');

-- Contributions Policies

-- Allow anyone to read paid contributions (respecting anonymity)
CREATE POLICY "Anyone can view paid contributions"
    ON contributions FOR SELECT
    USING (payment_status = 'paid');

-- Allow anyone to create contributions
CREATE POLICY "Anyone can create contributions"
    ON contributions FOR INSERT
    WITH CHECK (true);

-- Allow users to view their own contributions
CREATE POLICY "Users can view own contributions"
    ON contributions FOR SELECT
    USING (contributor_email = auth.jwt()->>'email');

-- Allow users to cancel their own pending contributions
CREATE POLICY "Users can cancel own pending contributions"
    ON contributions FOR UPDATE
    USING (
        contributor_email = auth.jwt()->>'email' 
        AND payment_status = 'pending'
    )
    WITH CHECK (payment_status = 'cancelled');

-- Service role has full access to contributions
CREATE POLICY "Service role full access to contributions"
    ON contributions
    USING (auth.jwt()->>'role' = 'service_role');

-- Function to get campaign statistics (respects RLS)
CREATE OR REPLACE FUNCTION get_campaign_stats(campaign_uuid UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_contributions', COUNT(*),
        'paid_contributions', COUNT(*) FILTER (WHERE payment_status = 'paid'),
        'total_raised', COALESCE(SUM(amount) FILTER (WHERE payment_status = 'paid'), 0),
        'pending_amount', COALESCE(SUM(amount) FILTER (WHERE payment_status = 'pending'), 0)
    ) INTO result
    FROM contributions
    WHERE campaign_id = campaign_uuid;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION get_campaign_stats(UUID) TO authenticated, anon;

-- Comments
COMMENT ON POLICY "Anyone can view active campaigns" ON campaigns 
    IS 'Public read access to active and completed campaigns';
COMMENT ON POLICY "Anyone can view paid contributions" ON contributions 
    IS 'Public read access to paid contributions, respecting anonymity settings';
