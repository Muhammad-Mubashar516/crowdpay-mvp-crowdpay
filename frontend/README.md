# CrowdPay

A Kenya-focused crowdfunding platform that bridges M-Pesa and Bitcoin/Lightning Network, enabling seamless fundraising with multiple payment options.

🔗 **Live Demo**: [https://crowdpay.netlify.app/](https://crowdpay.netlify.app/)

## Overview

CrowdPay allows users to create customizable fundraising events that accept both local currency (KES via M-Pesa) and Bitcoin (Lightning & On-chain). Event creators receive instant Bitcoin settlement while contributors can pay using their preferred method.

## Tech Stack

- **Frontend**: React 18 + TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query)
- **Animations**: Framer Motion
- **Backend**: Flask Python
- **Bitcoin**: Bitnob API (Lightning Network integration)

## Project Structure

```
src/
├── assets/              # Static assets (logo, images)
├── components/
│   ├── ui/              # Reusable UI components (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── AddContributionDialog.tsx
│   ├── AppLayout.tsx    # Main layout wrapper with sidebar
│   ├── AppSidebar.tsx   # Navigation sidebar
│   ├── ModeControl.tsx  # Campaign mode switcher
│   ├── PaymentModal.tsx # Universal payment modal (M-Pesa/Bitcoin)
│   ├── QRCodeDialog.tsx # QR code display for payments
│   ├── ShareButtons.tsx # Social sharing functionality
│   └── ...
├── contexts/
│   └── AuthContext.tsx  # Authentication state management
├── data/
│   └── demoData.ts      # Demo/sample data
├── hooks/
│   ├── use-mobile.tsx   # Mobile detection hook
│   ├── use-toast.ts     # Toast notifications hook
│   └── useCampaignContributions.tsx
├── integrations/
│   └── supabase/
│       ├── client.ts    # Supabase client configuration
│       └── types.ts     # Auto-generated database types
├── lib/
│   └── utils.ts         # Utility functions (cn, etc.)
├── pages/
│   ├── Auth.tsx         # Sign in/Sign up page
│   ├── Campaign.tsx     # Individual campaign view
│   ├── Contributions.tsx # User's contribution history
│   ├── CreateCampaign.tsx # Campaign creation form
│   ├── Dashboard.tsx    # User dashboard
│   ├── ExploreCampaigns.tsx # Public campaign gallery
│   ├── Landing.tsx      # Public landing page
│   ├── MyLinks.tsx      # User's created campaigns
│   ├── Notifications.tsx # Contribution alerts
│   ├── ProfileSettings.tsx # User profile settings
│   ├── Support.tsx      # Help & support page
│   └── Wallet.tsx       # Bitcoin wallet management
├── App.tsx              # Main app with routing
├── App.css              # Global styles
├── index.css            # Tailwind base + design tokens
└── main.tsx             # App entry point

supabase/
├── config.toml          # Supabase configuration
└── functions/
    ├── create-blink-wallet/   # Edge function for wallet creation
    └── create-lightning-invoice/ # Edge function for invoices

public/
├── favicon.ico
├── robots.txt
└── placeholder.svg
```

## Key Features

### Campaign Modes
- **Mode A (Merchant/POS)**: Offline point-of-sale with real-time payment tracking
- **Mode B (Event/Social)**: Event invitations with ticket/potluck functionality
- **Mode C (Activism)**: Privacy-focused with anonymous donations

### Payment Options
- M-Pesa (KES) with automatic BTC conversion via Bitnob API
- Bitcoin Lightning Network (instant)
- Bitcoin On-chain

### Event Features
- Custom slugs (crowdpay.me/your-campaign)
- Cover images and theme colors
- Category filtering and search
- Progress tracking with real-time updates
- Social sharing with Open Graph meta tags

### User Features
- Dashboard with campaign overview
- Wallet management (Blink integration)
- Contribution history
- Notification system
- Profile customization

## Design System

The app uses a consistent design system defined in:
- `src/index.css` - CSS custom properties (HSL colors, gradients, shadows)
- `tailwind.config.ts` - Tailwind configuration with semantic tokens

### Color Palette
- **Primary**: Bitcoin Orange (`#F7931A`)
- **Secondary**: M-Pesa Green (`#4CAF50`)
- **Semantic tokens**: `--background`, `--foreground`, `--primary`, `--muted`, etc.

### Themes
- Light and dark mode support via `next-themes`
- All colors use HSL format for consistency

## Getting Started

### Prerequisites
- Node.js 18+
- npm or bun

### Installation

```bash
# Clone the repository
git clone https://github.com/DadaDevelopers/crowdpay-mvp-crowdpay

# Navigate to project directory
cd crowdpay-mvp-crowdpay


# Install dependencies
npm install

# Start development server
npm run dev
```

### Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

## Architecture Decisions

1. **Component-Based**: Small, focused components for reusability
2. **Design System First**: All styling through semantic tokens
3. **Type Safety**: Full TypeScript with auto-generated Supabase types
4. **Mobile-First**: Responsive design with mobile detection hooks
5. **SEO Optimized**: React Helmet for meta tags and Open Graph

## Contributing

1. Follow the existing code style and patterns
2. Use semantic color tokens, never direct colors
3. Keep components small and focused
4. Write TypeScript with proper types
5. Test on both light and dark themes






|||||||||||||||||
---

## 🌍 Why CrowdPay?

In Kenya, **M-Pesa** is the lifeblood of daily transactions, but **Bitcoin** is the future of global borderless finance. CrowdPay isn't just a tool; it's a bridge. 

We are building a world where a local merchant in Nairobi can start a fundraiser and receive support from someone in Tokyo or New York instantly, with zero friction.

### ⚡ Project Status: Building the Future
![GitHub contributors](https://img.shields.io/github/contributors/DadaDevelopers/crowdpay-mvp-crowdpay?style=for-the-badge)
![GitHub issues](https://img.shields.io/github/issues/DadaDevelopers/crowdpay-mvp-crowdpay?style=for-the-badge)
![GitHub stars](https://img.shields.io/github/stars/DadaDevelopers/crowdpay-mvp-crowdpay?style=for-the-badge)

- **Current Focus:** Moving from Mock Data to Real-time Backend State.
- **Next Milestone:** Full M-Pesa STK Push integration via Bitnob.
- **Vision:** To become the #1 Lightning-enabled crowdfunding platform in Africa.

---

## 🤝 Join the Movement

We believe in the power of open source. Whether you are a Bitcoin maximalist, a frontend wizard, or someone who just wants to help the Kenyan community, there is a place for you here.

1. **Star** this repository to show your support.
2. **Fork** it and start building.
3. **Join** our discussions and help us shape the roadmap.

---

### Credits & Acknowledgments
Built with ❤️ by the **Dada Developers** team. Special thanks to the Lightning Network community and everyone pushing for financial inclusion in Africa.

> *"Fix the Money, Fix the World."* ₿

---
---

## 🛠 Detailed Feature Breakdown

### 1. Unified Payment Interface (The Bridge)
CrowdPay's core innovation is the ability to handle two vastly different financial ecosystems in one UI:
- **Fiat Path (KES):** Integrates with M-Pesa via Bitnob API. When a user pays in KES, the backend triggers an exchange to Bitcoin, ensuring the campaigner receives hard money.
- **Lightning Path (SATS):** Instant, near-zero-fee transactions. We use **LNbits** and **Blink** to generate BOLT11 invoices. The UI polls the backend every 3 seconds to detect payment confirmation without the user needing to refresh.

### 2. Campaign Governance Modes
We realized that a "one size fits all" approach doesn't work for fundraising. 
- **Mode A (Point of Sale):** Designed for physical merchants. The UI simplifies the donation to a "Checkout" experience.
- **Mode B (Social/Invitational):** Perfect for weddings (Chamas) or parties. It includes "Ticket" logic where a specific amount is required for entry.
- **Mode C (Anonymous/Activist):** No names, no tracking. Only the transaction hash is recorded, protecting both the donor and the receiver.

---

## 🏗 System Architecture & Data Flow

Understanding how data moves through CrowdPay is crucial for contributors:

1.  **Initiation:** A user creates a campaign. This is stored in **Supabase** in the `campaigns` table.
2.  **Contribution:** A donor selects a campaign and enters an amount. 
    - If **Bitcoin** is selected, a request is sent to the `/api/invoice/create` endpoint.
    - Our backend communicates with **LNbits/Bitnob** to get a `payment_request` (invoice string).
3.  **Real-time Updates:** 
    - The frontend enters a "polling state" using a custom React hook.
    - Once the payment is detected on the blockchain/Lightning network, the `contributions` table in Supabase is updated with `is_paid: true`.
4.  **Settlement:** The campaign balance is updated using a database trigger, ensuring data integrity.

---

## 💻 Technical Implementation Details

### Environment Variables Required
To run this project locally, you need to set up a `.env` file with the following keys:
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_key
VITE_API_URL=http://localhost:5000
VITE_BITNOB_API_KEY=your_bitnob_key
VITE_LNBITS_WEB_URL=your_lnbits_instance
📈 Future Roadmap (The "Vision 2026")
We are moving beyond a simple MVP. Our goals for the next year include:
NFC Integration: Allow "Tap to Pay" via Bolt Cards for offline Mode A campaigns.
Multi-Sig Vaults: For large community projects (Chamas), require 3 out of 5 elders to sign a transaction before funds are withdrawn.
L-USD Support: Stablecoin integration for those who want to avoid Bitcoin's volatility while keeping the funds in the Lightning ecosystem.
Localized Languages: Adding Swahili support to make the platform accessible to every Kenyan.
❓ Frequently Asked Questions (FAQ)
Q: Why Bitcoin for a Kenyan platform?
A: Bitcoin allows for instant settlement and global reach. M-Pesa is great locally, but Bitcoin connects Kenya to the world's liquidity without high bank fees.
Q: Is the M-Pesa integration live?
A: We are currently in the "Sandbox" phase. Real M-Pesa STK Pushes are being tested with a limited group of merchants.
Q: How do I withdraw my funds?
A: Once a campaign hits its target or the owner decides to withdraw, they can send the balance to any Lightning Address (e.g., user@getalby.com or user@blink.sv).

## License

MIT
