// frontend/src/pages/ProPage.tsx
import { useState } from 'react';
import { ArrowLeft, Check, Star, Zap, Crown, Infinity } from 'lucide-react';
import { Button, Spinner } from '../components/ui';
import { telegram } from '../lib/telegram';

interface PriceCardProps {
    title: string;
    price: number;
    period: string;
    features: string[];
    isPopular?: boolean;
    icon: React.ReactNode;
    onBuy: () => void;
    isLoading?: boolean;
}

function PriceCard({ title, price, period, features, isPopular, icon, onBuy, isLoading }: PriceCardProps) {
    return (
        <div className={`relative p-6 rounded-2xl border-2 transition-all ${isPopular
            ? 'bg-gradient-to-br from-lecto-bg-secondary to-lecto-bg-tertiary border-lecto-accent-gold shadow-lg shadow-lecto-accent-gold/10 scale-105 z-10'
            : 'bg-lecto-bg-secondary border-transparent opacity-90'
            }`}>
            {isPopular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-lecto-accent-gold text-black text-xs font-bold px-3 py-1 rounded-full">
                    POPULAR
                </div>
            )}

            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl ${isPopular ? 'bg-lecto-accent-gold/20 text-lecto-accent-gold' : 'bg-lecto-bg-tertiary text-lecto-text-secondary'}`}>
                    {icon}
                </div>
                <div className="text-right">
                    <div className="flex items-center justify-end gap-1 text-lecto-text-primary font-bold text-xl">
                        {price} <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                    </div>
                    <div className="text-xs text-lecto-text-secondary">{period}</div>
                </div>
            </div>

            <h3 className="text-lg font-bold text-lecto-text-primary mb-4">{title}</h3>

            <ul className="space-y-3 mb-6">
                {features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-3 text-sm text-lecto-text-secondary">
                        <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                        <span>{feature}</span>
                    </li>
                ))}
            </ul>

            <Button
                className={`w-full ${isPopular
                    ? 'bg-lecto-accent-gold text-black hover:bg-yellow-400'
                    : 'bg-lecto-bg-tertiary text-lecto-text-primary hover:bg-lecto-border'
                    }`}
                onClick={onBuy}
                disabled={isLoading}
            >
                {isLoading ? <Spinner size="sm" /> : 'Choose Plan'}
            </Button>
        </div>
    );
}

export function ProPage() {
    const [isLoading, setIsLoading] = useState<string | null>(null);

    const handleBack = () => {
        window.location.hash = '#/';
        telegram.haptic('selection');
    };

    const handleBuy = async (tier: string, _price: number) => {
        setIsLoading(tier);
        telegram.haptic('medium');
        try {
            // In a real app, this would initiate the invoice
            // const invoiceLink = await api.createInvoice(tier);
            // telegram.openInvoice(invoiceLink);

            // Mock for now
            await new Promise(resolve => setTimeout(resolve, 1500));
            telegram.alert(`Payment for ${tier} initiated! (Mock)`);
        } catch (error) {
            telegram.alert('Payment failed');
        } finally {
            setIsLoading(null);
        }
    };

    return (
        <div className="min-h-screen bg-lecto-bg-primary text-lecto-text-primary pb-12">
            {/* Header */}
            <header className="sticky top-0 z-10 bg-lecto-bg-primary/80 backdrop-blur-md border-b border-lecto-border px-4 py-3 flex items-center justify-between">
                <button onClick={handleBack} className="p-2 -ml-2 text-lecto-text-secondary">
                    <ArrowLeft className="w-6 h-6" />
                </button>
                <h1 className="font-bold text-lg flex items-center gap-2">
                    Lecto <span className="bg-lecto-accent-gold text-black text-xs px-1.5 py-0.5 rounded">PRO</span>
                </h1>
                <div className="w-10" /> {/* Spacer */}
            </header>

            <main className="p-4 space-y-8">
                <div className="text-center space-y-2">
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                        Unlock Academic Superpowers
                    </h2>
                    <p className="text-lecto-text-secondary">
                        Unlimited access to AI analysis, debates, and more.
                    </p>
                </div>

                <div className="space-y-4">
                    <PriceCard
                        title="Monthly"
                        price={150}
                        period="per month"
                        icon={<Zap className="w-6 h-6" />}
                        features={[
                            "Unlimited AI Analysis",
                            "Advanced Debates (Hard Mode)",
                            "Priority Processing",
                            "No Ads"
                        ]}
                        onBuy={() => handleBuy('monthly', 150)}
                        isLoading={isLoading === 'monthly'}
                    />

                    <PriceCard
                        title="Yearly"
                        price={1000}
                        period="per year"
                        isPopular={true}
                        icon={<Crown className="w-6 h-6" />}
                        features={[
                            "Everything in Monthly",
                            "Save 45%",
                            "Exclusive 'Pro' Badge",
                            "Early Access to new features"
                        ]}
                        onBuy={() => handleBuy('yearly', 1000)}
                        isLoading={isLoading === 'yearly'}
                    />

                    <PriceCard
                        title="Forever"
                        price={2500}
                        period="one-time payment"
                        icon={<Infinity className="w-6 h-6" />}
                        features={[
                            "Lifetime Access",
                            "Pay once, own forever",
                            "VIP Support",
                            "Founder Status"
                        ]}
                        onBuy={() => handleBuy('forever', 2500)}
                        isLoading={isLoading === 'forever'}
                    />
                </div>

                <div className="text-center text-xs text-lecto-text-secondary opacity-60">
                    Payments are processed securely via Telegram Stars.
                    <br />
                    You can cancel anytime.
                </div>
            </main>
        </div>
    );
}
