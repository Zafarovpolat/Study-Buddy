// frontend/src/pages/GroupResultsPage.tsx - СОЗДАЙ НОВЫЙ ФАЙЛ
import { useEffect, useState } from 'react';
import { ArrowLeft, Trophy, User, FileText, Calendar } from 'lucide-react';
import { Card, Spinner } from '../components/ui';
import { api } from '../lib/api';
import { telegram } from '../lib/telegram';

interface QuizResult {
    id: string;
    user: {
        id: string;
        first_name: string;
        username?: string;
    };
    material: {
        id: string;
        title: string;
    };
    score: number;
    max_score: number;
    percentage: number;
    completed_at: string;
}

export function GroupResultsPage({ groupId }: { groupId: string }) {
    const [results, setResults] = useState<QuizResult[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadResults();
    }, [groupId]);

    const loadResults = async () => {
        try {
            const data = await api.getGroupQuizResults(groupId);
            setResults(data);
        } catch (error: any) {
            telegram.alert(error.response?.data?.detail || 'Ошибка загрузки');
        } finally {
            setIsLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getScoreColor = (percentage: number) => {
        if (percentage >= 80) return 'text-green-500 bg-green-100 dark:bg-green-900/30';
        if (percentage >= 60) return 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/30';
        return 'text-red-500 bg-red-100 dark:bg-red-900/30';
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Spinner size="lg" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-lecto-bg p-4">
            <div className="flex items-center gap-3 mb-6">
                <button
                    onClick={() => window.history.back()}
                    className="p-2 hover:bg-lecto-secondary rounded-lg"
                >
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                    <h1 className="text-xl font-bold">Результаты тестов</h1>
                    <p className="text-sm text-lecto-hint">{results.length} результатов</p>
                </div>
            </div>

            {results.length > 0 ? (
                <div className="space-y-3">
                    {results.map((result) => (
                        <Card key={result.id} className="p-4">
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <User className="w-4 h-4 text-lecto-hint" />
                                        <span className="font-medium">
                                            {result.user.first_name}
                                            {result.user.username && (
                                                <span className="text-lecto-hint ml-1">@{result.user.username}</span>
                                            )}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-lecto-hint">
                                        <FileText className="w-3 h-3" />
                                        <span className="truncate">{result.material.title}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-lecto-hint mt-1">
                                        <Calendar className="w-3 h-3" />
                                        <span>{formatDate(result.completed_at)}</span>
                                    </div>
                                </div>

                                <div className={`px-3 py-2 rounded-xl ${getScoreColor(result.percentage)}`}>
                                    <div className="text-center">
                                        <div className="text-lg font-bold">{result.percentage}%</div>
                                        <div className="text-xs">{result.score}/{result.max_score}</div>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            ) : (
                <Card className="text-center py-12">
                    <Trophy className="w-16 h-16 text-lecto-hint mx-auto mb-4" />
                    <p className="text-lecto-hint">Пока нет результатов</p>
                    <p className="text-sm text-lecto-hint mt-1">
                        Результаты появятся когда участники пройдут тесты
                    </p>
                </Card>
            )}
        </div>
    );
}