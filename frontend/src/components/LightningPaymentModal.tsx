/**
 * Lightning Payment Modal for CrowdPay
 *
 * This component handles the Lightning Network payment flow:
 * 1. User enters amount in satoshis (or KES with conversion)
 * 2. Backend creates LNbits invoice
 * 3. Display QR code with BOLT11 invoice
 * 4. Poll backend for payment confirmation
 * 5. Show success/error state
 */

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Copy, Check, Loader2, CheckCircle, XCircle, Zap } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { useBtcRate, kesToSats } from "@/hooks/useBtcRate";
import bitcoinLogo from "@/assets/bitcoin-logo.png";

// API configuration
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

interface LightningPaymentModalProps {
  open: boolean;
  onClose: () => void;
  campaignId: string;
  campaignTitle: string;
  onPaymentSuccess?: (contributionId: string) => void;
}

type PaymentState = "input" | "invoice" | "processing" | "success" | "error";

interface ContributionResponse {
  contribution: {
    id: string;
    amount: number;
    currency: string;
    payment_status: string;
  };
  payment_request: string;
  payment_hash: string;
}

export const LightningPaymentModal = ({
  open,
  onClose,
  campaignId,
  campaignTitle,
  onPaymentSuccess,
}: LightningPaymentModalProps) => {
  const [paymentState, setPaymentState] = useState<PaymentState>("input");
  const [amount, setAmount] = useState("1000");
  const [contributorName, setContributorName] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [copied, setCopied] = useState(false);
  const [invoice, setInvoice] = useState("");
  const [paymentHash, setPaymentHash] = useState("");
  const [contributionId, setContributionId] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { toast } = useToast();
  const { kesToSats: kesToSatsRate, btcToKes, loading: rateLoading } = useBtcRate();

  const kesAmount = parseInt(amount) || 0;
  const satAmount = kesAmount > 0 ? kesToSats(kesAmount, kesToSatsRate) : 0;

  // Reset state when modal opens
  useEffect(() => {
    if (open) {
      setPaymentState("input");
      setAmount("1000");
      setContributorName("");
      setIsAnonymous(false);
      setInvoice("");
      setPaymentHash("");
      setContributionId("");
      setError("");
    }
  }, [open]);

  // Poll for payment status
  const pollPaymentStatus = useCallback(async () => {
    if (!contributionId) return;

    try {
      const response = await fetch(
        `${API_URL}/api/contributions/${contributionId}/status`
      );
      const data = await response.json();

      if (data.is_paid) {
        setPaymentState("success");
        toast({
          title: "Payment Successful!",
          description: `Thank you for your ${satAmount.toLocaleString()} sats contribution!`,
        });
        onPaymentSuccess?.(contributionId);
        return true;
      }

      if (data.payment_status === "expired" || data.payment_status === "failed") {
        setPaymentState("error");
        setError("Payment expired or failed. Please try again.");
        return true;
      }

      return false;
    } catch (err) {
      console.error("Error polling payment status:", err);
      return false;
    }
  }, [contributionId, satAmount, toast, onPaymentSuccess]);

  // Start polling when invoice is displayed
  useEffect(() => {
    if (paymentState !== "invoice" || !contributionId) return;

    const pollInterval = setInterval(async () => {
      const isDone = await pollPaymentStatus();
      if (isDone) {
        clearInterval(pollInterval);
      }
    }, 3000); // Poll every 3 seconds

    // Stop polling after 10 minutes
    const timeout = setTimeout(() => {
      clearInterval(pollInterval);
      if (paymentState === "invoice") {
        setPaymentState("error");
        setError("Invoice expired. Please create a new payment.");
      }
    }, 600000);

    return () => {
      clearInterval(pollInterval);
      clearTimeout(timeout);
    };
  }, [paymentState, contributionId, pollPaymentStatus]);

  const handleCopy = () => {
    navigator.clipboard.writeText(invoice);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast({
      title: "Copied!",
      description: "Lightning invoice copied to clipboard",
    });
  };

  const createInvoice = async () => {
    if (satAmount < 100) {
      toast({
        title: "Invalid amount",
        description: "Minimum contribution is 100 satoshis",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/contributions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          campaign_id: campaignId,
          amount: satAmount,
          currency: "SATS",
          contributor_name: isAnonymous ? null : contributorName || null,
          is_anonymous: isAnonymous,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to create invoice");
      }

      const data: ContributionResponse = await response.json();

      setInvoice(data.payment_request);
      setPaymentHash(data.payment_hash);
      setContributionId(data.contribution.id);
      setPaymentState("invoice");

      toast({
        title: "Invoice Created",
        description: "Scan the QR code with your Lightning wallet",
      });
    } catch (err) {
      console.error("Error creating invoice:", err);
      setError(err instanceof Error ? err.message : "Failed to create invoice");
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to create invoice",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (paymentState === "invoice") {
      // Warn user about pending payment
      if (!confirm("Your payment is still pending. Are you sure you want to close?")) {
        return;
      }
    }
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-bitcoin" />
            Lightning Payment
          </DialogTitle>
        </DialogHeader>

        <AnimatePresence mode="wait">
          {/* Input State */}
          {paymentState === "input" && (
            <motion.div
              key="input"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label htmlFor="contributor-name">Your Name (optional)</Label>
                <Input
                  id="contributor-name"
                  type="text"
                  value={contributorName}
                  onChange={(e) => setContributorName(e.target.value)}
                  placeholder="Enter your name"
                  disabled={isAnonymous}
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="anonymous"
                  checked={isAnonymous}
                  onChange={(e) => setIsAnonymous(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <Label htmlFor="anonymous" className="text-sm cursor-pointer">
                  Contribute anonymously
                </Label>
              </div>

              <div className="space-y-2">
                <Label htmlFor="amount">Amount (KES)</Label>
                <Input
                  id="amount"
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="1000"
                  min="1"
                />
              </div>

              <div className="bg-muted rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Amount in Bitcoin</span>
                  <motion.span
                    className="font-bold text-bitcoin"
                    animate={{ opacity: [0.7, 1, 0.7] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    {satAmount.toLocaleString()} sats
                  </motion.span>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {rateLoading ? (
                    "Loading live rate..."
                  ) : (
                    `1 BTC = ${btcToKes.toLocaleString()} KES`
                  )}
                </p>
              </div>

              <p className="text-xs text-muted-foreground">
                Contributing to: <strong>{campaignTitle}</strong>
              </p>

              {error && (
                <p className="text-sm text-red-500">{error}</p>
              )}

              <Button
                onClick={createInvoice}
                disabled={isLoading || satAmount < 100}
                className="w-full bg-bitcoin hover:bg-bitcoin/90 text-white gap-2"
                size="lg"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating Invoice...
                  </>
                ) : (
                  <>
                    <motion.img
                      src={bitcoinLogo}
                      alt="Bitcoin"
                      className="w-5 h-5"
                      whileHover={{ scale: 1.15, rotate: 360 }}
                      transition={{ type: "spring", stiffness: 300 }}
                    />
                    Generate Lightning Invoice
                  </>
                )}
              </Button>
            </motion.div>
          )}

          {/* Invoice State - Show QR Code */}
          {paymentState === "invoice" && (
            <motion.div
              key="invoice"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <div className="flex flex-col items-center space-y-4 p-4 bg-muted rounded-lg">
                <p className="text-sm text-center text-muted-foreground">
                  Scan with your Lightning wallet to pay{" "}
                  <strong>{satAmount.toLocaleString()} sats</strong>
                </p>

                <div className="bg-white p-4 rounded-xl shadow-lg">
                  <QRCodeSVG
                    value={invoice}
                    size={220}
                    level="M"
                    includeMargin={false}
                  />
                </div>

                <div className="w-full space-y-2">
                  <Label className="text-xs">Lightning Invoice</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      value={invoice}
                      readOnly
                      className="font-mono text-xs"
                    />
                    <Button
                      size="icon"
                      variant="outline"
                      onClick={handleCopy}
                    >
                      {copied ? (
                        <Check className="w-4 h-4 text-green-500" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Waiting for payment...
                </div>
              </div>

              <Button
                variant="outline"
                onClick={() => setPaymentState("input")}
                className="w-full"
              >
                Cancel & Start Over
              </Button>
            </motion.div>
          )}

          {/* Success State */}
          {paymentState === "success" && (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center space-y-4 py-8"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
              >
                <CheckCircle className="w-20 h-20 text-green-500" />
              </motion.div>

              <h3 className="text-xl font-bold text-green-600">Payment Successful!</h3>
              <p className="text-center text-muted-foreground">
                Thank you for your contribution of{" "}
                <strong>{satAmount.toLocaleString()} sats</strong> to {campaignTitle}!
              </p>

              <Button
                onClick={onClose}
                className="w-full bg-green-500 hover:bg-green-600"
              >
                Done
              </Button>
            </motion.div>
          )}

          {/* Error State */}
          {paymentState === "error" && (
            <motion.div
              key="error"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center space-y-4 py-8"
            >
              <XCircle className="w-20 h-20 text-red-500" />
              <h3 className="text-xl font-bold text-red-600">Payment Failed</h3>
              <p className="text-center text-muted-foreground">{error}</p>

              <div className="flex gap-2 w-full">
                <Button
                  variant="outline"
                  onClick={onClose}
                  className="flex-1"
                >
                  Close
                </Button>
                <Button
                  onClick={() => setPaymentState("input")}
                  className="flex-1"
                >
                  Try Again
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
};

export default LightningPaymentModal;
