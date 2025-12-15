import { createContext, useContext, useState, useEffect } from "react";

interface WalletData {
  lightningAddress: string;
  onchainAddress: string;
  walletType: "blink" | "external" | null;
  btcBalance: number;
}

interface MockUser {
  id: string;
  email: string;
  username?: string;
}

interface AuthContextType {
  user: MockUser | null;
  session: any;
  loading: boolean;
  wallet: WalletData;
  setWallet: (wallet: WalletData) => void;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, username: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const defaultWallet: WalletData = {
  lightningAddress: "demo@crowdpay.me",
  onchainAddress: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
  walletType: "blink",
  btcBalance: 0.0234,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const MockAuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<MockUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [wallet, setWallet] = useState<WalletData>(defaultWallet);

  // Check localStorage for existing session on mount
  useEffect(() => {
    const storedUser = localStorage.getItem("crowdpay_user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const signIn = async (email: string, password: string) => {
    const mockUser = { 
      id: "mock-user-id", 
      email,
      username: email.split("@")[0]
    };
    setUser(mockUser);
    localStorage.setItem("crowdpay_user", JSON.stringify(mockUser));
  };

  const signUp = async (email: string, password: string, username: string) => {
    const mockUser = { 
      id: "mock-user-id", 
      email,
      username
    };
    setUser(mockUser);
    localStorage.setItem("crowdpay_user", JSON.stringify(mockUser));
  };

  const signOut = async () => {
    setUser(null);
    localStorage.removeItem("crowdpay_user");
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      session: user ? {} : null, 
      loading, 
      wallet, 
      setWallet, 
      signIn,
      signUp,
      signOut
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within a MockAuthProvider");
  }
  return context;
};
