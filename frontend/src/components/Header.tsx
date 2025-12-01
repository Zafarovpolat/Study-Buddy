import { useStore } from '../store/useStore';
import { Sparkles, Crown } from 'lucide-react';

export function Header() {
    const { user, limits } = useStore();

    return (
        <header className="sticky top-0 z-10 bg-tg-bg/80 backdrop-blur-lg border-b border-tg-hint/10">
            <div className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Sparkles className="w-6 h-6 text-tg-button" />
                    <h1 className="text-lg font-bold">EduAI</h1>
                </div>

                {user && (
                    <div className="flex items-center gap-2">
                        {user.subscription_tier === 'free' ? (
                            <span className="text-xs px-2 py-1 bg-tg-secondary rounded-full text-tg-hint">
                                {limits?.remaining_today ?? 3}/3 сегодня
                            </span>
                        ) : (
                            <span className="text-xs px-2 py-1 bg-yellow-500/20 text-yellow-600 rounded-full flex items-center gap-1">
                                <Crown className="w-3 h-3" />
                                Pro
                            </span>
                        )}
                    </div>
                )}
            </div>
        </header>
    );
}