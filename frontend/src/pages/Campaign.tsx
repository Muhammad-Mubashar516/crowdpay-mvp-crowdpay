/**
 * Campaign Page - Public view of a single campaign
 *
 * Features:
 * - Campaign details display
 * - Progress tracking
 * - Lightning payment integration via LNbits
 * - Social sharing
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { useCampaigns, mockContributions } from "@/contexts/CampaignsContext";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { Bitcoin, Share2, Sun, Moon, Zap } from "lucide-react";
import { PaymentModal } from "@/components/PaymentModal";

const categoryLabels: Record<string, { label: string; emoji: string }> = {
  education: { label: "Education", emoji: "🎓" },
  medical: { label: "Medical", emoji: "🏥" },
  business: { label: "Business", emoji: "💼" },
  community: { label: "Community", emoji: "🤝" },
  emergency: { label: "Emergency", emoji: "🚨" },
  creative: { label: "Creative", emoji: "🎨" },
  sports: { label: "Sports", emoji: "⚽" },
  charity: { label: "Charity", emoji: "❤️" },
  other: { label: "Other", emoji: "📦" },
};

const Campaign = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { getCampaignBySlug } = useCampaigns();
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);

  // Find campaign from context
  const campaign = getCampaignBySlug(slug || "");

  // Calculate total raised from mock contributions
  const totalRaised = campaign
    ? mockContributions
        .filter((c) => c.campaign_id === campaign.id)
        .reduce((sum, c) => sum + c.amount, 0)
    : 0;

  useEffect(() => {
    if (!slug || !campaign) {
      toast({
        title: "Campaign not found",
        description: "This campaign doesn't exist or has been removed",
        variant: "destructive",
      });
      navigate("/");
    }
  }, [slug, campaign, navigate, toast]);

  const handlePayment = () => {
    setPaymentModalOpen(true);
  };

  const handlePaymentSuccess = (contributionId: string) => {
    toast({
      title: "Thank you!",
      description: "Your contribution has been received.",
    });
    // Optionally refresh campaign data here
  };

  const campaignUrl = `${window.location.origin}/c/${slug}`;

  const shareLink = () => {
    if (navigator.share) {
      navigator.share({
        title: campaign?.title,
        text: campaign?.description || "Support this campaign",
        url: campaignUrl,
      });
    } else {
      navigator.clipboard.writeText(campaignUrl);
      toast({
        title: "Link copied!",
        description: "Share it with your friends",
      });
    }
  };

  if (!campaign) {
    return null;
  }

  const progress =
    campaign.goal_amount > 0
      ? Math.round((totalRaised / campaign.goal_amount) * 100)
      : 0;

  const themeColor = campaign.theme_color || "#F7931A";

  // Dark and light mode toggle
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("theme");
      if (saved) return saved === "dark";
      return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return false;
  });

  // Theme toggle logic
  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [isDark]);

  const toggleTheme = () => setIsDark(!isDark);

  return (
    <>
      <Helmet>
        <title>{campaign.title} - CrowdPay</title>
        <meta
          name="description"
          content={campaign.description || `Support ${campaign.title}`}
        />

        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content={window.location.href} />
        <meta property="og:title" content={`${campaign.title} - CrowdPay`} />
        <meta
          property="og:description"
          content={campaign.description || `Support ${campaign.title}`}
        />
        {campaign.cover_image_url && (
          <meta property="og:image" content={campaign.cover_image_url} />
        )}

        {/* Twitter */}
        <meta property="twitter:card" content="summary_large_image" />
        <meta property="twitter:url" content={window.location.href} />
        <meta property="twitter:title" content={`${campaign.title} - CrowdPay`} />
        <meta
          property="twitter:description"
          content={campaign.description || `Support ${campaign.title}`}
        />
        {campaign.cover_image_url && (
          <meta property="twitter:image" content={campaign.cover_image_url} />
        )}
      </Helmet>

      <div className="min-h-screen bg-background">
        {/* Navigation */}
        <nav className="border-b bg-background">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div
              className="flex items-center gap-2 cursor-pointer"
              onClick={() => navigate("/app")}
            >
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                <Bitcoin className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="font-bold text-xl">CrowdPay</span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={shareLink}>
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </Button>
              <Button
                onClick={toggleTheme}
                variant="secondary"
                size="icon"
                className="backdrop-blur-sm dark:text-white light: hover:bg-white/20"
                aria-label="Toggle theme"
              >
                {isDark ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </nav>

        <div className="container mx-auto px-4 py-8 max-w-2xl">
          <Card className="overflow-hidden">
            {/* Cover Image */}
            {campaign.cover_image_url && (
              <div className="w-full h-64 overflow-hidden">
                <img
                  src={campaign.cover_image_url}
                  alt={campaign.title}
                  className="w-full h-full object-cover"
                />
              </div>
            )}

            <div className="p-6 space-y-6">
              {/* Title & Description */}
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <h1 className="text-3xl font-bold flex-1">{campaign.title}</h1>
                  <Badge variant="secondary" className="shrink-0">
                    {categoryLabels[campaign.category || "other"]?.emoji}{" "}
                    {categoryLabels[campaign.category || "other"]?.label}
                  </Badge>
                </div>
                {campaign.description && (
                  <p className="text-muted-foreground whitespace-pre-wrap">
                    {campaign.description}
                  </p>
                )}
              </div>

              {/* Progress */}
              <div className="space-y-3">
                <div className="flex justify-between items-baseline">
                  <div>
                    <p
                      className="text-3xl font-bold"
                      style={{ color: themeColor }}
                    >
                      {totalRaised.toLocaleString()} sats
                    </p>
                    <p className="text-sm text-muted-foreground">
                      raised of {campaign.goal_amount.toLocaleString()} sats goal
                    </p>
                  </div>
                  <p className="text-2xl font-semibold text-muted-foreground">
                    {progress}%
                  </p>
                </div>
                <Progress value={progress} className="h-3" />
              </div>

              {/* Lightning Payment Info */}
              <div className="bg-muted rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-5 h-5 text-bitcoin" />
                  <span className="font-medium">Lightning Payments Only</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  This campaign accepts Bitcoin via the Lightning Network for
                  instant, low-fee payments. Use any Lightning-compatible wallet
                  to contribute.
                </p>
              </div>

              {/* Payment Button */}
              <div className="pt-4">
                <Button
                  size="lg"
                  className="w-full bg-bitcoin hover:bg-bitcoin/90 text-white gap-2"
                  onClick={handlePayment}
                >
                  <Zap className="w-5 h-5" />
                  Contribute with Lightning
                </Button>
              </div>

              {/* Info Text */}
              <p className="text-xs text-center text-muted-foreground pt-4">
                Powered by CrowdPay • Lightning Network fundraising via LNbits
              </p>
            </div>
          </Card>
        </div>
      </div>

      {/* Payment Modal */}
      <PaymentModal
        open={paymentModalOpen}
        onClose={() => setPaymentModalOpen(false)}
        campaignId={campaign.id}
        campaignTitle={campaign.title}
        onPaymentSuccess={handlePaymentSuccess}
      />
    </>
  );
};

export default Campaign;
