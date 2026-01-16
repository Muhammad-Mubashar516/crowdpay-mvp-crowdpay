import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import logo from "@/assets/logo.png";
import { Moon, Sun } from "lucide-react";


const SubNav: React.FC = () => {
    // Dark and light mode toggle
    const [isDark, setIsDark] = useState(() => {
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem('theme');
            if (saved) return saved === 'dark';
            return window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
        return false;
    });

    // Theme toggle logic
    useEffect(() => {
        const root = document.documentElement;
        if (isDark) {
            root.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            root.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }, [isDark]);

    const toggleTheme = () => setIsDark(!isDark);
    

    return (
        <nav className="border-b bg-background">
            <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                <Link to="/" className="flex items-center gap-2">
                    <img src={logo} alt="CrowdPay" className="h-8 w-8 sm:h-10 sm:w-10" />
                    <span className="font-bold text-xl">CrowdPay</span>
                </Link>
                <div className="flex items-center gap-2">
                    {/* redirect user to home page if clicked */}
                    <Link to="/">
                        <Button variant="ghost">
                            Back to Home
                        </Button>
                    </Link>
                    <Button
                        onClick={toggleTheme}
                        variant="secondary"
                        size="icon"
                        className="backdrop-blur-sm dark:text-white light: hover:bg-white/20"
                        aria-label="Toggle theme"
                    >
                        {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                    </Button>
                </div>
            </div>
        </nav>
    );
};

export default SubNav;