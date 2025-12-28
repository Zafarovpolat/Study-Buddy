// frontend/src/components/ProWall.tsx
import { useState } from 'react';
import { X, Zap, Crown, Infinity, Clock, Check } from 'lucide-react';
import { Button } from './ui';
// import { api } from '../lib/api';
import { telegram } from '../lib/telegram';

interface ProWallProps {
    isOpen: boolean;
    onClose: () => void;
    trigger?: 'limit' | 'feature' | 'debate' | 'insights';
}

const PLANS = [
    {
        id: 'standard_month',
        name: 'Standard',
        price: 150,
        period: '/мес',
        icon: Zap,
        features: ['Безлимит материалов', 'Все AI функции', 'Группы до 50 чел.'],
        style: 'default' as const,
        color: 'blue'
    },
    {
        id: 'premium_year',
        name: 'Premium',
        price: 1200,
        originalPrice: 1800,
        period: '/год',
        icon: Crown,
        features: ['Всё из Standard', 'Академические Инсайты', 'Приоритет поддержки'],
        style: 'featured' as const,
        badge: 'Экономия 33%',
        color: 'gold'
    },
    {
        id: 'forever',
        name: 'Forever',
        price: 2500,
        period: '',
        icon: Infinity,
        features: ['Навсегда', 'Все будущие функции', 'VIP статус'],
        style: 'premium' as const,
        color: 'black'
    }
];

const TRIGGER_MESSAGES = {
    limit: 'Вы исчерпали дневной лимит',
    feature: 'Эта функция доступна в Pro',
    debate: 'Сложные дебаты доступны в Pro',
    insights: 'Академические инсайты доступны в Pro',
};

export function ProWall({ isOpen, onClose, trigger = 'feature' }: ProWallProps) {
    const [isLoading, setIsLoading] = useState<string | null>(null);

    if (!isOpen) return null;

    const handlePurchase = async (planId: string, price: number) => {
        setIsLoading(planId);
        telegram.haptic('medium');

        try {
            // Здесь интеграция с Telegram Stars
            telegram.alert(`Оплата ${price}⭐ через Telegram Stars. Напишите /pro боту.`);
        } catch (error) {
            telegram.alert('Ошибка оплаты');
        } finally {
            setIsLoading(null);
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0D1117] rounded-3xl max-w-md w-full max-h-[90vh] overflow-y-auto border border-[#30363D]">
                {/* Header */}
                <div className="p-6 text-center relative">
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 p-2 text-[#8B949E] hover:text-white rounded-full hover:bg-[#21262D]"
                    >
                        <X className="w-5 h-5" />
                    </button>

                    <div className="w-20 h-20 bg-gradient-to-br from-[#FFD700] to-[#FFA500] 
                          rounded-2xl flex items-center justify-center mx-auto mb-4
                          shadow-[0_0_30px_rgba(255,215,0,0.3)]">
                        <Crown className="w-10 h-10 text-black" />
                    </div>

                    <h2 className="text-2xl font-bold mb-2 text-white tracking-tight">
                        Разблокируйте безлимитный интеллект
                    </h2>
                    <p className="text-[#8B949E]">
                        {TRIGGER_MESSAGES[trigger]}
                    </p>
                </div>

                {/* Plans */}
                <div className="p-4 space-y-3">
                    {PLANS.map(plan => (
                        <div
                            key={plan.id}
                            onClick={() => handlePurchase(plan.id, plan.price)}
                            className={`relative rounded-2xl p-4 border-2 transition-all cursor-pointer
                ${plan.style === 'featured'
                                    ? 'bg-gradient-to-r from-[#FFD700]/10 to-[#FFA500]/10 border-[#FFD700] shadow-[0_0_20px_rgba(255,215,0,0.2)]'
                                    : plan.style === 'premium'
                                        ? 'bg-[#161B22] border-[#FFD700]/50 hover:border-[#FFD700]'
                                        : 'bg-[#161B22] border-[#30363D] hover:border-[#484F58]'
                                }
              `}
                        >
                            {plan.badge && (
                                <div className="absolute -top-3 right-4 bg-gradient-to-r from-[#FFD700] to-[#FFA500] 
                                text-black text-xs font-bold px-3 py-1 rounded-full">
                                    {plan.badge}
                                </div>
                            )}

                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-xl ${plan.style === 'featured'
                                    ? 'bg-gradient-to-r from-[#FFD700] to-[#FFA500]'
                                    : plan.style === 'premium'
                                        ? 'bg-black border border-[#FFD700]'
                                        : 'bg-[#21262D]'
                                    }`}>
                                    <plan.icon className={`w-6 h-6 ${plan.style === 'featured' ? 'text-black' : 'text-white'
                                        }`} />
                                </div>

                                <div className="flex-1">
                                    <h3 className="font-semibold text-white">{plan.name}</h3>
                                    <div className="flex items-baseline gap-2">
                                        <span className="text-2xl font-bold text-white">{plan.price}</span>
                                        <span className="text-[#8B949E]">⭐{plan.period}</span>
                                        {plan.originalPrice && (
                                            <span className="text-sm text-[#8B949E] line-through">
                                                {plan.originalPrice}⭐
                                            </span>
                                        )}
                                    </div>
                                </div>

                                <Button
                                    size="sm"
                                    isLoading={isLoading === plan.id}
                                    className={plan.style === 'featured'
                                        ? 'bg-gradient-to-r from-[#FFD700] to-[#FFA500] text-black font-semibold'
                                        : 'bg-[#21262D] border border-[#30363D]'
                                    }
                                >
                                    Выбрать
                                </Button>
                            </div>

                            {/* Features */}
                            <div className="mt-3 pt-3 border-t border-[#30363D]/50">
                                <div className="flex flex-wrap gap-2">
                                    {plan.features.map((feature, i) => (
                                        <span key={i} className="flex items-center gap-1 text-xs text-[#8B949E]">
                                            <Check className="w-3 h-3 text-[#3FB950]" />
                                            {feature}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* SOS */}
                <div className="p-4 pt-0">
                    <button
                        onClick={() => handlePurchase('sos_24h', 75)}
                        className="w-full flex items-center justify-center gap-2 py-3 
                       text-[#8B949E] hover:text-white transition-colors
                       border border-dashed border-[#30363D] rounded-xl
                       hover:border-[#484F58] hover:bg-[#161B22]"
                    >
                        <Clock className="w-4 h-4" />
                        <span>Нужно срочно? <span className="text-white font-medium">24 часа за 75⭐</span></span>
                    </button>
                </div>

                {/* Footer */}
                <div className="p-4 pt-0 text-center">
                    <p className="text-xs text-[#484F58]">
                        Оплата через Telegram Stars • Мгновенная активация
                    </p>
                </div>
            </div>
        </div>
    );
}