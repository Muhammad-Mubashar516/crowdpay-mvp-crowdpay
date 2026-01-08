import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useNavigate, Link } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/MockAuthContext";
import { Helmet } from "react-helmet-async";
import logo from "@/assets/logo.png";

const Auth = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const { toast } = useToast();
  const { signIn, user, loading } = useAuth();

  // Redirect if already logged in
  useEffect(() => {
    if (!loading && user) {
      navigate("/app");
    }
  }, [user, loading, navigate]);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast({
        title: "Error",
        description: "Please fill in all fields",
        variant: "destructive",
      });
      return;
    }

    await signIn(email, password);

    toast({
      title: "Welcome back!",
      description: "This is a UI demo. All data is mock data.",
    });
    
    navigate("/app");
  };

  // Show loading state while checking session
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <>
      <Helmet>
        <title>Sign In - CrowdPay</title>
        <meta name="description" content="Sign in to your CrowdPay account" />
      </Helmet>

      <div className="min-h-screen bg-background">
        {/* Navigation */}
        <nav className="border-b bg-background">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <img src={logo} alt="CrowdPay" className="h-8 w-8 sm:h-10 sm:w-10" />
              <span className="font-bold text-xl">CrowdPay</span>
            </Link>
            <Button variant="ghost" onClick={() => navigate("/")}>
              Back to Home
            </Button>
          </div>
        </nav>

        {/* Sign In Form */}
        <div className="container mx-auto px-4 py-16">
          <Card className="max-w-md mx-auto p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold mb-2">Welcome Back</h1>
              <p className="text-muted-foreground">
                Sign in to manage your payment links
              </p>
            </div>

            <form onSubmit={handleSignIn} className="space-y-4">
              <div>
                <Label className="text-sm font-medium mb-2 block">Email</Label>
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div>
                <Label className="text-sm font-medium mb-2 block">Password</Label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <Button type="submit" className="w-full">
                Sign In
              </Button>

              <div className="text-center text-sm text-muted-foreground">
                <p>
                  Don't have an account?{" "}
                  <Link to="/signup" className="text-primary hover:underline font-medium">
                    Create Account
                  </Link>
                </p>
                <p className="mt-4 p-3 bg-muted/50 rounded-md">
                  💡 <strong>Demo Mode:</strong> Enter any email/password to explore the UI
                </p>
              </div>
            </form>
          </Card>
        </div>

        {/* Footer */}
        <footer className="py-12 px-4 bg-accent mt-16">
          <div className="container mx-auto text-center">
            <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} CrowdPay. Bitcoin-powered crowdfunding platform.
            </p>
          </div>
        </footer>
      </div>
    </>
  );
};

export default Auth;
