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

        const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
        setMessages(newMessages);
        setIsLoading(true);

        try {
            if (!debateStarted) {
                const result = await api.startDebate(
                    userMessage,
                    'ЗА',
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
                const result = await api.continueDebate(
                    messages[0]?.content || materialTitle,
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

    const selectDifficulty = (d: Difficulty) => {
        if (d === 'hard' && !isPro) {
            telegram.alert('Сложный режим доступен в Pro');
            return;
        }
        setDifficulty(d);
        telegram.haptic('light');
    };

    // Результаты дебатов
    if (judgeResult) {
        return (
            <div className="space-y-4">
                <div className={`text-center p-6 rounded-2xl ${judgeResult.winner === 'user'
                        ? 'bg-gradient-to-br from-green-100 to-emerald-50 dark:from-green-900/30 dark:to-emerald-900/20'
                        : judgeResult.winner === 'ai'
                            ? 'bg-gradient-to-br from-red-100 to-orange-50 dark:from-red-900/30 dark:to-orange-900/20'
                            : 'bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-800 dark:to-gray-700'
                    }`}>
                    <Trophy className={`w-12 h-12 mx-auto mb-2 ${judgeResult.winner === 'user' ? 'text-green-500' :
                            judgeResult.winner === 'ai' ? 'text-red-500' : 'text-gray-500'
                        }`} />
                    <h3 className="text-xl font-bold">
                        {judgeResult.winner === 'user' ? '🎉 Вы победили!' :
                            judgeResult.winner === 'ai' ? '🤖 AI победил' : '🤝 Ничья'}
                    </h3>
                    <div className="flex justify-center gap-8 mt-4">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-blue-500">{judgeResult.user_score}/10</div>
                            <div className="text-xs text-tg-hint">Ваш счёт</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-red-500">{judgeResult.ai_score}/10</div>
                            <div className="text-xs text-tg-hint">AI счёт</div>
                        </div>
                    </div>
                </div>

                <Card>
                    <h4 className="font-medium mb-2">📋 Итог</h4>
                    <p className="text-sm text-tg-hint">{judgeResult.summary}</p>
                </Card>

                {judgeResult.tip && (
                    <Card className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                        <h4 className="font-medium mb-1 text-blue-600">💡 Совет</h4>
                        <p className="text-sm text-tg-hint">{judgeResult.tip}</p>
                    </Card>
                )}

                <Button className="w-full" onClick={handleReset}>
                    🔄 Начать новые дебаты
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
        <div className="space-y-4">
            {/* Сложность — показываем только до начала */}
            {!debateStarted && (
                <>
                    {/* Инструкция */}
                    <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl p-4">
                        <div className="flex items-start gap-3">
                            <span className="text-2xl">⚔️</span>
                            <div>
                                <p className="font-medium text-sm">Как играть</p>
                                <p className="text-xs text-tg-hint mt-1">
                                    Напишите утверждение или тезис — AI займёт противоположную позицию и начнёт дебаты!
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Выбор сложности */}
                    <div>
                        <p className="text-sm font-medium text-tg-hint mb-3">Выберите сложность:</p>
                        <div className="grid grid-cols-3 gap-2">
                            {/* Лёгкий */}
                            <button
                                onClick={() => selectDifficulty('easy')}
                                className={`relative p-3 rounded-xl border-2 transition-all ${difficulty === 'easy'
                                        ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                                        : 'border-tg-secondary hover:border-green-300'
                                    }`}
                            >
                                <div className="flex flex-col items-center gap-1">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${difficulty === 'easy' ? 'bg-green-500 text-white' : 'bg-green-100 dark:bg-green-900/30 text-green-500'
                                        }`}>
                                        <GraduationCap className="w-5 h-5" />
                                    </div>
                                    <span className="text-xs font-medium">Лёгкий</span>
                                </div>
                            </button>

                            {/* Средний */}
                            <button
                                onClick={() => selectDifficulty('medium')}
                                className={`relative p-3 rounded-xl border-2 transition-all ${difficulty === 'medium'
                                        ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                                        : 'border-tg-secondary hover:border-yellow-300'
                                    }`}
                            >
                                <div className="flex flex-col items-center gap-1">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${difficulty === 'medium' ? 'bg-yellow-500 text-white' : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600'
                                        }`}>
                                        <Brain className="w-5 h-5" />
                                    </div>
                                    <span className="text-xs font-medium">Средний</span>
                                </div>
                            </button>

                            {/* Сложный */}
                            <button
                                onClick={() => selectDifficulty('hard')}
                                className={`relative p-3 rounded-xl border-2 transition-all ${difficulty === 'hard'
                                        ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                                        : 'border-tg-secondary hover:border-red-300'
                                    } ${!isPro ? 'opacity-60' : ''}`}
                            >
                                <div className="flex flex-col items-center gap-1">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${difficulty === 'hard' ? 'bg-red-500 text-white' : 'bg-red-100 dark:bg-red-900/30 text-red-500'
                                        }`}>
                                        <Zap className="w-5 h-5" />
                                    </div>
                                    <span className="text-xs font-medium">Сложный</span>
                                    {!isPro && (
                                        <Crown className="w-3 h-3 text-yellow-500 absolute top-1 right-1" />
                                    )}
                                </div>
                            </button>
                        </div>
                    </div>
                </>
            )}

            {/* Messages */}
            {messages.length > 0 && (
                <div className="space-y-3 max-h-64 overflow-y-auto rounded-xl bg-tg-secondary/30 p-3">
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[85%] p-3 rounded-2xl ${msg.role === 'user'
                                        ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-md'
                                        : 'bg-white dark:bg-gray-800 text-tg-text rounded-bl-md shadow-sm'
                                    }`}
                            >
                                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            </div>
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="bg-white dark:bg-gray-800 p-3 rounded-2xl rounded-bl-md shadow-sm">
                                <div className="flex gap-1">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            )}

            {/* Счётчик раундов */}
            {debateStarted && (
                <div className="flex items-center justify-between text-xs text-tg-hint px-1">
                    <span>Раунд {Math.floor(messages.length / 2)}</span>
                    <span>{messages.length >= 4 ? '✓ Можно завершить' : `Ещё ${4 - messages.length} сообщ.`}</span>
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
                        className="flex-1 p-3 bg-tg-secondary rounded-xl text-tg-text placeholder-tg-hint focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                    />
                    <Button
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim() || isLoading}
                        className="px-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                    >
                        <Send className="w-5 h-5" />
                    </Button>
                </div>

                {debateStarted && messages.length >= 4 && (
                    <Button
                        variant="secondary"
                        className="w-full border-2 border-dashed border-purple-300 dark:border-purple-700 hover:bg-purple-50 dark:hover:bg-purple-900/20"
                        onClick={handleEndDebate}
                        disabled={isLoading}
                    >
                        <Trophy className="w-4 h-4 mr-2 text-purple-500" />
                        <span className="text-purple-600 dark:text-purple-400">Завершить и узнать результат</span>
                    </Button>
                )}
            </div>
        </div>
    );
}