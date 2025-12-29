// frontend/src/components/AskLibrary.tsx
import { useState } from 'react';
import { Search, Send, BookOpen, Sparkles, Lock } from 'lucide-react';
import { Card, Button, Spinner } from './ui';
import { api } from '../lib/api';
import { telegram } from '../lib/telegram';
import { useStore } from '../store/useStore';

interface Source {
    material_id: string;
    material_title: string;
    similarity: number;
}

interface AskLibraryProps {
    materialId?: string;  // Если указан — спрашиваем только по этому материалу
}

export function AskLibrary({ materialId }: AskLibraryProps) {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState<string | null>(null);
    const [sources, setSources] = useState<Source[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);

    const { user } = useStore();
    const isPro = user?.subscription_tier !== 'free' && user?.subscription_tier !== undefined;


    const handleAsk = async () => {
        if (!question.trim()) return;

        if (!isPro) {
            telegram.alert('Эта функция доступна только в Pro подписке. Напишите /pro боту.');
            return;
        }

        setIsLoading(true);
        telegram.haptic('medium');

        try {
            const result = await api.askLibrary(question, materialId);
            setAnswer(result.answer);
            setSources(result.sources);
        } catch (error: any) {
            telegram.alert(error.response?.data?.detail || 'Ошибка поиска');
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) {
        return (
            <button
                onClick={() => {
                    setIsOpen(true);
                    telegram.haptic('light');
                }}
                className="fixed bottom-20 right-4 w-14 h-14 bg-gradient-to-br from-purple-500 to-blue-500 text-white rounded-full shadow-lg flex items-center justify-center z-40 active:scale-95 transition-transform"
            >
                <Sparkles className="w-6 h-6" />
            </button>
        );
    }

    return (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-end justify-center">
            <div className="bg-lecto-bg-primary w-full max-w-lg rounded-t-3xl p-4 max-h-[80vh] overflow-hidden flex flex-col animate-slide-up">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h2 className="font-bold">Спроси библиотеку</h2>
                            <p className="text-xs text-tg-hint">
                                {materialId ? 'Поиск по материалу' : 'Поиск по всем материалам'}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="text-tg-hint hover:text-tg-text"
                    >
                        ✕
                    </button>
                </div>

                {!isPro && (
                    <Card className="mb-4 bg-gradient-to-r from-purple-100 to-blue-100">
                        <div className="flex items-center gap-3">
                            <Lock className="w-8 h-8 text-purple-500" />
                            <div>
                                <p className="font-medium">Pro функция</p>
                                <p className="text-sm text-tg-hint">
                                    Напишите /pro боту для подключения
                                </p>
                            </div>
                        </div>
                    </Card>
                )}

                {/* Answer */}
                <div className="flex-1 overflow-y-auto mb-4">
                    {answer ? (
                        <div className="space-y-4">
                            <Card className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20">
                                <p className="whitespace-pre-wrap">{answer}</p>
                            </Card>

                            {sources.length > 0 && (
                                <div>
                                    <p className="text-sm text-tg-hint mb-2">Источники:</p>
                                    <div className="space-y-1">
                                        {sources.map((source, i) => (
                                            <div
                                                key={i}
                                                className="flex items-center gap-2 text-sm text-tg-hint"
                                            >
                                                <BookOpen className="w-4 h-4" />
                                                <span className="truncate">{source.material_title}</span>
                                                <span className="text-xs">
                                                    ({Math.round(source.similarity * 100)}%)
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="text-center py-12 text-tg-hint">
                            <Search className="w-16 h-16 mx-auto mb-4 opacity-50" />
                            <p>Задайте вопрос по вашим материалам</p>
                            <p className="text-sm mt-2">
                                AI найдёт ответ в ваших конспектах
                            </p>
                        </div>
                    )}
                </div>

                {/* Input */}
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                        placeholder="Что такое митохондрия?"
                        className="flex-1 px-4 py-3 bg-lecto-bg-secondary rounded-xl focus:outline-none focus:ring-2 focus:ring-lecto-accent-primary"
                        disabled={isLoading || !isPro}
                    />
                    <Button
                        onClick={handleAsk}
                        disabled={isLoading || !question.trim() || !isPro}
                        className="px-4 bg-lecto-bg-secondary"
                    >
                        {isLoading ? <Spinner size="sm" /> : <Send className="w-5 h-5" />}
                    </Button>
                </div>
            </div>
        </div>
    );
}