// frontend/src/components/LeaderboardTab.tsx
import { useEffect, useState } from 'react';
import { Trophy, Medal, User, Target } from 'lucide-react';
import { Card, Spinner } from './ui';
import { api } from '../lib/api';

interface LeaderboardEntry {
    rank: number;
    user_id: string;
    first_name: string;
    username?: string;
    tests_count: number;
    total_score: number;
    total_max_score: number;
    avg_percentage: number;
}

interface LeaderboardTabProps {
    groupId: string;
}

export function LeaderboardTab({ groupId }: LeaderboardTabProps) {
    const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadLeaderboard();
    }, [groupId]);

    const loadLeaderboard = async () => {
        try {
            setIsLoading(true);
            const data = await api.getGroupLeaderboard(groupId);
            setLeaderboard(data);
        } catch (error) {
            console.error('Failed to load leaderboard:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const getRankIcon = (rank: number) => {
        switch (rank) {
            case 1:
                return <span className="text-2xl">🥇</span>;
            case 2:
                return <span className="text-2xl">🥈</span>;
            case 3:
                return <span className="text-2xl">🥉</span>;
            default:
                return (
                    <span className="w-8 h-8 bg-tg-secondary rounded-full flex items-center justify-center text-sm font-medium">
                        {rank}
                    </span>
                );
        }
    };

    const getPercentageColor = (percentage: number) => {
        if (percentage >= 80) return 'text-green-500';
        if (percentage >= 60) return 'text-yellow-500';
        return 'text-red-500';
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
            </div>
        );
    }

    if (leaderboard.length === 0) {
        return (
            <Card className="text-center py-12">
                <Trophy className="w-16 h-16 text-tg-hint mx-auto mb-4" />
                <p className="text-tg-hint font-medium">Рейтинг пока пуст</p>
                <p className="text-sm text-tg-hint mt-1">
                    Пройдите тесты чтобы появиться в рейтинге
                </p>
            </Card>
        );
    }

    return (
        <div className="space-y-3">
            {/* Топ-3 */}
            {leaderboard.length >= 3 && (
                <div className="grid grid-cols-3 gap-2 mb-4">
                    {/* 2 место */}
                    <Card className="text-center py-4 order-1">
                        <span className="text-3xl">🥈</span>
                        <p className="font-medium text-sm mt-2 truncate px-1">
                            {leaderboard[1]?.first_name}
                        </p>
                        <p className={`text-lg font-bold ${getPercentageColor(leaderboard[1]?.avg_percentage)}`}>
                            {leaderboard[1]?.avg_percentage}%
                        </p>
                    </Card>

                    {/* 1 место */}
                    <Card className="text-center py-4 order-0 bg-gradient-to-b from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-200 dark:border-yellow-800">
                        <span className="text-4xl">🥇</span>
                        <p className="font-bold mt-2 truncate px-1">
                            {leaderboard[0]?.first_name}
                        </p>
                        <p className={`text-xl font-bold ${getPercentageColor(leaderboard[0]?.avg_percentage)}`}>
                            {leaderboard[0]?.avg_percentage}%
                        </p>
                    </Card>

                    {/* 3 место */}
                    <Card className="text-center py-4 order-2">
                        <span className="text-3xl">🥉</span>
                        <p className="font-medium text-sm mt-2 truncate px-1">
                            {leaderboard[2]?.first_name}
                        </p>
                        <p className={`text-lg font-bold ${getPercentageColor(leaderboard[2]?.avg_percentage)}`}>
                            {leaderboard[2]?.avg_percentage}%
                        </p>
                    </Card>
                </div>
            )}

            {/* Остальные */}
            <div className="space-y-2">
                {leaderboard.slice(leaderboard.length >= 3 ? 3 : 0).map((entry) => (
                    <Card key={entry.user_id} className="flex items-center gap-3 p-3">
                        {getRankIcon(entry.rank)}

                        <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">
                                {entry.first_name}
                                {entry.username && (
                                    <span className="text-tg-hint ml-1 text-sm">
                                        @{entry.username}
                                    </span>
                                )}
                            </p>
                            <div className="flex items-center gap-3 text-xs text-tg-hint">
                                <span className="flex items-center gap-1">
                                    <Target className="w-3 h-3" />
                                    {entry.tests_count} тестов
                                </span>
                                <span>
                                    {entry.total_score}/{entry.total_max_score} баллов
                                </span>
                            </div>
                        </div>

                        <div className={`text-lg font-bold ${getPercentageColor(entry.avg_percentage)}`}>
                            {entry.avg_percentage}%
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
}