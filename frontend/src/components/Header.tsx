// frontend/src/components/Header.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { Crown, Flame } from 'lucide-react';
import { api } from '../lib/api';

export function Header() {
    const { user, limits } = useStore();
    const [streak, setStreak] = useState<number>(0);

    useEffect(() => {
        loadStreak();
    }, []);

    const loadStreak = async () => {
        try {
            const data = await api.getMyStreak();
            setStreak(data.current_streak || 0);
        } catch (e) {
            console.error('Failed to load streak:', e);
        }
    };

    return (
        <header className="sticky top-0 z-10 bg-tg-bg/80 backdrop-blur-lg border-b border-tg-hint/10">
            <div className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {/* ЛОГО - замени src на свой путь */}
                    <img
                        src="/lecto-logo.png"
                        alt="Lecto"
                        className="w-8 h-8 rounded-lg"
                    />
                    <h1 className="text-lg font-bold">Lecto</h1>
                </div>

                <div className="flex items-center gap-3">
                    {streak > 0 && (
                        <div className="flex items-center gap-1 px-2 py-1 bg-orange-500/20 rounded-full">
                            <Flame className="w-4 h-4 text-orange-500" />
                            <span className="text-sm font-medium text-orange-500">{streak}</span>
                        </div>
                    )}

                    {user && (
                        user.subscription_tier === 'free' ? (
                            <span className="text-xs px-2 py-1 bg-tg-secondary rounded-full text-tg-hint">
                                {limits?.remaining_today ?? '?'}/{limits?.daily_limit ?? '?'}
                            </span>
                        ) : (
                            <span className="text-xs px-2 py-1 bg-yellow-500/20 text-yellow-600 rounded-full flex items-center gap-1">
                                <Crown className="w-3 h-3" />
                                Pro
                            </span>
                        )
                    )}
                </div>
            </div>
        </header>
    );
}