import React from 'react';
import { Button } from "@/components/ui/button";
import logo from "@/assets/logo.png";
import { Twitter, Instagram, Mail } from "lucide-react";


const Footer: React.FC = () => {
    return (
        <footer id="footer" className="py-12 px-4 bg-slate-200 dark:bg-slate-900 text-foreground dark:text-white">
            <div className="container mx-auto max-w-6xl flex flex-col md:flex-row justify-between items-center gap-8">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 flex items-center justify-center">
                        <img src={logo} alt="CrowdPay" className="w-6 h-6" />
                    </div>
                    <span className="font-bold text-2xl">CrowdPay</span>
                </div>
                <div className="flex gap-6 text-sm text-muted-foreground">
                    {["Browse Events", "Features", "How it Works"].map(item => (
                        <a key={item} href="#" className="hover:text-foreground transition-colors">{item}</a>
                    ))}
                </div>
                <div className="flex gap-4">
                    <a href="https://x.com/crowdpay_ke" target="_blank" rel="noopener noreferrer">
                        <Button size="icon" variant="ghost" className="text-muted-foreground hover:text-foreground"><Twitter className="w-5 h-5" /></Button>
                    </a>
                    <a href="https://www.instagram.com/crowd.pay" target="_blank" rel="noopener noreferrer">
                        <Button size="icon" variant="ghost" className="text-muted-foreground hover:text-foreground"><Instagram className="w-5 h-5" /></Button>
                    </a>
                    <a href="mailto:crowdpay2026@gmail.com" target="_blank" rel="noopener noreferrer">
                        <Button size="icon" variant="ghost" className="text-muted-foreground hover:text-foreground"><Mail className="w-5 h-5" /></Button>
                    </a>
                </div>
            </div>
            <div className="text-center mt-8 text-muted-foreground text-sm">
                © {new Date().getFullYear()} CrowdPay. Bitcoin-powered crowdfunding.
            </div>
        </footer>
    );
};

export default Footer;