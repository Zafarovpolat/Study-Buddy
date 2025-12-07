// frontend/src/components/InviteBanner.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { useState, useEffect } from 'react';
import { Gift, Copy, Check, Share2 } from 'lucide-react';
import { Card, Button } from './ui';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';

export function InviteBanner() {
    const { referralStats, setReferralStats } = useStore();
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        loadReferralStats();
    }, []);

    const loadReferralStats = async () => {
        try {
            const stats = await api.getReferralStats();
            setReferralStats(stats);
        } catch (error) {
            console.error('Failed to load referral stats:', error);
        }
    };

    const handleCopy = async () => {
        if (!referralStats) return;

        const text = `📚 Присоединяйся к Study Buddy!\n${referralStats.referral_link}`;
        await navigator.clipboard.writeText(text);
        setCopied(true);
        telegram.haptic('success');
        setTimeout(() => setCopied(false), 2000);
    };

    const handleShare = () => {
        if (!referralStats) return;

        const text = `📚 Присоединяйся к Study Buddy — ИИ-помощник для учёбы!`;
        const url = referralStats.referral_link;

        window.open(
            `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`,
            '_blank'
        );

        telegram.haptic('medium');
    };

    if (!referralStats || referralStats.pro_granted) {
        return null;
    }

    const progress = (referralStats.referral_count / referralStats.threshold) * 100;
    const remaining = referralStats.referrals_needed;

    return (
        <Card className="bg-gradient-to-r from-purple-600 to-pink-600 text-white border-0">
            <div className="flex items-start gap-3">
                <div className="p-2 bg-white/20 rounded-full flex-shrink-0">
                    <Gift className="w-6 h-6 text-white" />
                </div>

                <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-white">
                        Пригласи {remaining} друзей — получи Pro!
                    </h3>

                    <div className="mt-2 mb-3">
                        <div className="flex justify-between text-xs text-white/80 mb-1">
                            <span>{referralStats.referral_count} из {referralStats.threshold}</span>
                            <span>{Math.round(progress)}%</span>
                        </div>
                        <div className="h-2 bg-white/30 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-white transition-all duration-500"
                                style={{ width: `${Math.min(progress, 100)}%` }}
                            />
                        </div>
                    </div>

                    <div className="flex gap-2">
                        <Button
                            size="sm"
                            onClick={handleShare}
                            className="flex-1 bg-transparent border border-white text-purple-600 hover:bg-white"
                        >
                            <Share2 className="w-4 h-4 mr-1" />
                            Поделиться
                        </Button>
                        <Button
                            size="sm"
                            variant="secondary"
                            onClick={handleCopy}
                            className="px-3 bg-white/20 hover:bg-white/30 text-white border-0"
                        >
                            {copied ? (
                                <Check className="w-4 h-4" />
                            ) : (
                                <Copy className="w-4 h-4" />
                            )}
                        </Button>
                    </div>
                </div>
            </div>
        </Card>
    );
}