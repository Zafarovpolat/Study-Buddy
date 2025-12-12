// frontend/src/components/DebateTab.tsx
import { useState, useRef, useEffect } from 'react';
import { Send, Trophy, Loader2, Zap, Brain, GraduationCap, Crown } from 'lucide-react';
import { Button, Card } from './ui';
import { api } from '../lib/api';
import { telegram } from '../lib/telegram';
import { useStore } from '../store/useStore';

interface DebateTabProps {
    materialId: string;
    materialTitle: string;
    materialContent?: string;
}

type Difficulty = 'easy' | 'medium' | 'hard';

interface Message {
    role: 'user' | 'ai';
    content: string;
}

interface JudgeResult {
    winner: 'user' | 'ai' | 'draw';
    user_score: number;
    ai_score: number;
    summary: string;
    tip: string;
}

const DIFFICULTIES: { value: Difficulty; label: string; icon: React.ReactNode }[] = [
    { value: 'easy', label: 'Лёгкий', icon: <GraduationCap className="w-4 h-4" /> },
    { value: 'medium', label: 'Средний', icon: <Brain className="w-4 h-4" /> },
    { value: 'hard', label: 'Сложный', icon: <Zap className="w-4 h-4" /> },
];

export function DebateTab({ materialId, materialTitle }: DebateTabProps) {
    const { user } = useStore();
    const isPro = user?.subscription_tier === 'pro';

    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [difficulty, setDifficulty] = useState<Difficulty>('medium');
    const [debateStarted, setDebateStarted] = useState(false);
    const [aiPosition, setAiPosition] = useState('');
    const [judgeResult, setJudgeResult] = useState<JudgeResult | null>(null);
    const [isJudging, setIsJudging] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage = inputValue.trim();
        setInputValue('');
        telegram.haptic('light');

        // Добавляем сообщение пользователя
        const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
        setMessages(newMessages);
        setIsLoading(true);

        try {
            if (!debateStarted) {
                // Первое сообщение — начинаем дебаты
                // AI определит тему из сообщения пользователя
                const result = await api.startDebate(
                    userMessage, // Тема = первое сообщение
                    'ЗА', // Пользователь по умолчанию ЗА
                    difficulty,
                    materialId
                );

                if (result.success) {
                    setAiPosition(result.ai_position);
                    setMessages([
                        { role: 'user', content: userMessage },
                        { role: 'ai', content: result.ai_message }
                    ]);
                    setDebateStarted(true);
                    telegram.haptic('success');
                }
            } else {
                // Продолжаем дебаты
                const result = await api.continueDebate(
                    messages[0]?.content || materialTitle, // Тема = первое сообщение
                    aiPosition,
                    difficulty,
                    newMessages,
                    userMessage,
                    materialId
                );

                if (result.success) {
                    setMessages([...newMessages, { role: 'ai', content: result.ai_message }]);
                }
            }
        } catch (error: any) {
            telegram.haptic('error');
            const errorMsg = error.response?.data?.detail || 'Ошибка. Попробуйте ещё раз.';
            setMessages(prev => [...prev, { role: 'ai', content: `⚠️ ${errorMsg}` }]);
        } finally {
            setIsLoading(false);
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    };

    const handleEndDebate = async () => {
        if (messages.length < 4) {
            telegram.alert('Нужно минимум 2 раунда (4 сообщения) для оценки');
            return;
        }

        setIsJudging(true);
        telegram.haptic('medium');

        try {
            const result = await api.judgeDebate(
                messages[0]?.content || materialTitle,
                messages
            );
            setJudgeResult(result);
            telegram.haptic('success');
        } catch (error) {
            telegram.haptic('error');
            telegram.alert('Ошибка оценки дебатов');
        } finally {
            setIsJudging(false);
        }
    };

    const handleReset = () => {
        setMessages([]);
        setDebateStarted(false);
        setAiPosition('');
        setJudgeResult(null);
        telegram.haptic('light');
    };

    // Результаты дебатов
    if (judgeResult) {
        return (
            <div className="space-y-4">
                {/* Winner */}
                <div className={`text-center p-6 rounded-2xl ${judgeResult.winner === 'user'
                        ? 'bg-gradient-to-r from-green-100 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/30'
                        : judgeResult.winner === 'ai'
                            ? 'bg-gradient-to-r from-red-100 to-orange-100 dark:from-red-900/30 dark:to-orange-900/30'
                            : 'bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700'
                    }`}>
                    <Trophy className={`w-12 h-12 mx-auto mb-2 ${judgeResult.winner === 'user' ? 'text-green-500' :
                            judgeResult.winner === 'ai' ? 'text-red-500' : 'text-gray-500'
                        }`} />
                    <h3 className="text-xl font-bold">
                        {judgeResult.winner === 'user' ? '🎉 Вы победили!' :
                            judgeResult.winner === 'ai' ? '🤖 AI победил' : '🤝 Ничья'}
                    </h3>
                    <div className="flex justify-center gap-8 mt-4">
                        <div>
                            <div className="text-2xl font-bold text-blue-500">{judgeResult.user_score}/10</div>
                            <div className="text-xs text-tg-hint">Ваш счёт</div>
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-red-500">{judgeResult.ai_score}/10</div>
                            <div className="text-xs text-tg-hint">AI счёт</div>
                        </div>
                    </div>
                </div>

                {/* Summary */}
                <Card>
                    <h4 className="font-medium mb-2">📋 Итог</h4>
                    <p className="text-sm text-tg-hint">{judgeResult.summary}</p>
                </Card>

                {/* Tip */}
                {judgeResult.tip && (
                    <Card className="bg-blue-50 dark:bg-blue-900/20">
                        <h4 className="font-medium mb-1 text-blue-600">💡 Совет</h4>
                        <p className="text-sm text-tg-hint">{judgeResult.tip}</p>
                    </Card>
                )}

                <Button className="w-full" onClick={handleReset}>
                    Начать новые дебаты
                </Button>
            </div>
        );
    }

    // Judging
    if (isJudging) {
        return (
            <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="w-12 h-12 animate-spin text-purple-500 mb-4" />
                <p className="text-lg font-medium">Судья анализирует...</p>
                <p className="text-sm text-tg-hint">Это займёт несколько секунд</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full">
            {/* Difficulty selector — показываем только до начала */}
            {!debateStarted && (
                <div className="mb-4">
                    <p className="text-sm text-tg-hint mb-2">Сложность AI:</p>
                    <div className="flex gap-2">
                        {DIFFICULTIES.map((d) => (
                            <button
                                key={d.value}
                                onClick={() => {
                                    if (d.value === 'hard' && !isPro) {
                                        telegram.alert('Сложный режим доступен в Pro');
                                        return;
                                    }
                                    setDifficulty(d.value);
                                    telegram.haptic('light');
                                }}
                                className={`flex-1 flex items-center justify-center gap-1 py-2 px-3 rounded-lg border-2 transition-all text-sm ${difficulty === d.value
                                        ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 text-purple-600'
                                        : 'border-tg-secondary text-tg-hint'
                                    } ${d.value === 'hard' && !isPro ? 'opacity-50' : ''}`}
                            >
                                {d.icon}
                                <span>{d.label}</span>
                                {d.value === 'hard' && !isPro && (
                                    <Crown className="w-3 h-3 text-yellow-500" />
                                )}
                            </button>
                        ))}
                    </div>

                    <Card className="mt-3 bg-purple-50 dark:bg-purple-900/20">
                        <p className="text-sm">
                            ⚔️ <strong>Как играть:</strong> Напишите утверждение или тезис.
                            AI займёт противоположную позицию и начнёт дебаты!
                        </p>
                    </Card>
                </div>
            )}

            {/* Messages */}
            {messages.length > 0 && (
                <div className="flex-1 space-y-3 mb-4 max-h-96 overflow-y-auto">
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[85%] p-3 rounded-2xl ${msg.role === 'user'
                                        ? 'bg-blue-500 text-white rounded-br-md'
                                        : 'bg-tg-secondary text-tg-text rounded-bl-md'
                                    }`}
                            >
                                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            </div>
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="bg-tg-secondary p-3 rounded-2xl rounded-bl-md">
                                <Loader2 className="w-5 h-5 animate-spin text-tg-hint" />
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            )}

            {/* Input */}
            <div className="space-y-2">
                <div className="flex gap-2">
                    <input
                        ref={inputRef}
                        type="text"
                        placeholder={debateStarted ? "Ваш аргумент..." : "Напишите тезис для дебатов..."}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        disabled={isLoading}
                        className="flex-1 p-3 bg-tg-secondary rounded-xl text-tg-text placeholder-tg-hint focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                    <Button
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim() || isLoading}
                        className="px-4 bg-purple-500 hover:bg-purple-600"
                    >
                        <Send className="w-5 h-5" />
                    </Button>
                </div>

                {debateStarted && messages.length >= 4 && (
                    <Button
                        variant="secondary"
                        className="w-full"
                        onClick={handleEndDebate}
                        disabled={isLoading}
                    >
                        <Trophy className="w-4 h-4 mr-2" />
                        Завершить и узнать результат
                    </Button>
                )}
            </div>
        </div>
    );
}