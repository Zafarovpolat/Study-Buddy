import { useState } from 'react';
import { FileText, Zap, HelpCircle, BookOpen, Layers, RefreshCw } from 'lucide-react';
import { Button, Card } from './ui';
import { api } from '../lib/api';
import { telegram } from '../lib/telegram';

interface Output {
    id: string;
    format: string;
    content: string;
    created_at: string;
}

interface OutputViewerProps {
    materialId: string;
    outputs: Output[];
    onRefresh: () => void;
}

const formatConfig: Record<string, { icon: typeof FileText; label: string; color: string }> = {
    smart_notes: { icon: FileText, label: 'Конспект', color: 'text-blue-500' },
    tldr: { icon: Zap, label: 'TL;DR', color: 'text-yellow-500' },
    quiz: { icon: HelpCircle, label: 'Тест', color: 'text-green-500' },
    glossary: { icon: BookOpen, label: 'Глоссарий', color: 'text-purple-500' },
    flashcards: { icon: Layers, label: 'Карточки', color: 'text-pink-500' },
};

export function OutputViewer({ materialId, outputs, onRefresh }: OutputViewerProps) {
    const [activeFormat, setActiveFormat] = useState<string>(
        outputs[0]?.format || 'smart_notes'
    );
    const [isRegenerating, setIsRegenerating] = useState(false);

    const activeOutput = outputs.find((o) => o.format === activeFormat);

    const handleRegenerate = async () => {
        try {
            setIsRegenerating(true);
            telegram.haptic('medium');
            await api.regenerateOutput(materialId, activeFormat);
            telegram.haptic('success');
            onRefresh();
        } catch (error) {
            telegram.haptic('error');
            telegram.alert('Ошибка при регенерации');
        } finally {
            setIsRegenerating(false);
        }
    };

    return (
        <div className="space-y-4">
            {/* Format Tabs */}
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                {Object.entries(formatConfig).map(([format, config]) => {
                    const Icon = config.icon;
                    const hasOutput = outputs.some((o) => o.format === format);

                    return (
                        <button
                            key={format}
                            onClick={() => {
                                telegram.haptic('selection');
                                setActiveFormat(format);
                            }}
                            className={`flex items-center gap-2 px-4 py-2 rounded-xl whitespace-nowrap transition-all ${activeFormat === format
                                ? 'bg-tg-button text-tg-button-text'
                                : hasOutput
                                    ? 'bg-tg-secondary text-tg-text'
                                    : 'bg-tg-secondary/50 text-tg-hint'
                                }`}
                        >
                            <Icon className={`w-4 h-4 ${activeFormat === format ? '' : config.color}`} />
                            {config.label}
                        </button>
                    );
                })}
            </div>

            {/* Content */}
            <Card className="min-h-[300px]">
                {activeOutput ? (
                    <div className="space-y-4">
                        {/* Actions */}
                        <div className="flex justify-end">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleRegenerate}
                                isLoading={isRegenerating}
                            >
                                <RefreshCw className="w-4 h-4 mr-1" />
                                Обновить
                            </Button>
                        </div>

                        {/* Render content based on format */}
                        {activeFormat === 'quiz' || activeFormat === 'flashcards' ? (
                            <JsonContentViewer
                                content={activeOutput.content}
                                format={activeFormat}
                            />
                        ) : (
                            <MarkdownViewer content={activeOutput.content} />
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-64 text-tg-hint">
                        <p>Контент не сгенерирован</p>
                        <Button className="mt-4" onClick={handleRegenerate} isLoading={isRegenerating}>
                            Сгенерировать
                        </Button>
                    </div>
                )}
            </Card>
        </div>
    );
}

// Markdown Viewer
function MarkdownViewer({ content }: { content: string }) {
    // Простой рендер markdown (можно заменить на react-markdown)
    const formattedContent = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/## (.*?)$/gm, '<h2 class="text-lg font-bold mt-4 mb-2">$1</h2>')
        .replace(/### (.*?)$/gm, '<h3 class="font-semibold mt-3 mb-1">$1</h3>')
        .replace(/- (.*?)$/gm, '<li class="ml-4">• $1</li>')
        .replace(/\n/g, '<br/>');

    return (
        <div
            className="prose prose-sm max-w-none text-tg-text"
            dangerouslySetInnerHTML={{ __html: formattedContent }}
        />
    );
}

// JSON Content Viewer (Quiz, Flashcards)
function JsonContentViewer({ content, format }: { content: string; format: string }) {
    try {
        const data = JSON.parse(content);

        if (format === 'quiz') {
            return <QuizViewer questions={data.questions || []} />;
        }

        if (format === 'flashcards') {
            return <FlashcardsViewer cards={data.flashcards || []} />;
        }

        return <pre className="text-xs overflow-auto">{content}</pre>;
    } catch {
        return <MarkdownViewer content={content} />;
    }
}

// Quiz Viewer
interface Question {
    id: number;
    question: string;
    options: Record<string, string>;
    correct: string;
    explanation: string;
}

function QuizViewer({ questions }: { questions: Question[] }) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
    const [showResult, setShowResult] = useState(false);
    const [score, setScore] = useState(0);

    const question = questions[currentIndex];
    if (!question) return <p className="text-tg-hint">Нет вопросов</p>;

    const handleAnswer = (answer: string) => {
        if (selectedAnswer) return;

        telegram.haptic('selection');
        setSelectedAnswer(answer);
        setShowResult(true);

        if (answer === question.correct) {
            setScore((s) => s + 1);
            telegram.haptic('success');
        } else {
            telegram.haptic('error');
        }
    };

    const nextQuestion = () => {
        if (currentIndex < questions.length - 1) {
            setCurrentIndex((i) => i + 1);
            setSelectedAnswer(null);
            setShowResult(false);
        }
    };

    const isFinished = currentIndex === questions.length - 1 && showResult;

    return (
        <div className="space-y-4">
            {/* Progress */}
            <div className="flex items-center justify-between text-sm text-tg-hint">
                <span>Вопрос {currentIndex + 1} из {questions.length}</span>
                <span>Счёт: {score}/{questions.length}</span>
            </div>

            {/* Question */}
            <p className="text-lg font-medium">{question.question}</p>

            {/* Options */}
            <div className="space-y-2">
                {Object.entries(question.options).map(([key, value]) => {
                    const isCorrect = key === question.correct;
                    const isSelected = key === selectedAnswer;

                    return (
                        <button
                            key={key}
                            onClick={() => handleAnswer(key)}
                            disabled={showResult}
                            className={`w-full p-4 rounded-xl text-left transition-all ${showResult
                                ? isCorrect
                                    ? 'bg-green-500/20 border-2 border-green-500'
                                    : isSelected
                                        ? 'bg-red-500/20 border-2 border-red-500'
                                        : 'bg-tg-secondary'
                                : 'bg-tg-secondary hover:bg-tg-hint/20'
                                }`}
                        >
                            <span className="font-medium mr-2">{key}.</span>
                            {value}
                        </button>
                    );
                })}
            </div>

            {/* Explanation */}
            {showResult && (
                <Card variant="outlined" className="bg-tg-button/5">
                    <p className="text-sm">
                        <span className="font-semibold">Объяснение:</span> {question.explanation}
                    </p>
                </Card>
            )}

            {/* Next Button */}
            {showResult && !isFinished && (
                <Button className="w-full" onClick={nextQuestion}>
                    Следующий вопрос
                </Button>
            )}

            {/* Final Result */}
            {isFinished && (
                <Card className="text-center bg-tg-button/10">
                    <p className="text-2xl font-bold mb-2">
                        {score === questions.length ? '🎉' : score >= questions.length / 2 ? '👍' : '📚'}
                    </p>
                    <p className="text-lg font-semibold">
                        Результат: {score} из {questions.length}
                    </p>
                    <p className="text-sm text-tg-hint mt-1">
                        {Math.round((score / questions.length) * 100)}% правильных ответов
                    </p>
                </Card>
            )}
        </div>
    );
}

// Flashcards Viewer
interface Flashcard {
    id: number;
    front: string;
    back: string;
}

function FlashcardsViewer({ cards }: { cards: Flashcard[] }) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);

    const card = cards[currentIndex];
    if (!card) return <p className="text-tg-hint">Нет карточек</p>;

    const flip = () => {
        telegram.haptic('light');
        setIsFlipped(!isFlipped);
    };

    const next = () => {
        setCurrentIndex((i) => (i + 1) % cards.length);
        setIsFlipped(false);
        telegram.haptic('selection');
    };

    const prev = () => {
        setCurrentIndex((i) => (i - 1 + cards.length) % cards.length);
        setIsFlipped(false);
        telegram.haptic('selection');
    };

    return (
        <div className="space-y-4">
            {/* Progress */}
            <div className="text-center text-sm text-tg-hint">
                Карточка {currentIndex + 1} из {cards.length}
            </div>

            {/* Card */}
            <div
                onClick={flip}
                className="min-h-[200px] p-6 rounded-2xl bg-gradient-to-br from-tg-button/20 to-tg-button/5 flex items-center justify-center cursor-pointer transition-all hover:scale-[1.02]"
            >
                <p className="text-lg text-center">
                    {isFlipped ? card.back : card.front}
                </p>
            </div>

            <p className="text-center text-xs text-tg-hint">
                Нажмите на карточку, чтобы перевернуть
            </p>

            {/* Navigation */}
            <div className="flex gap-2">
                <Button variant="secondary" className="flex-1" onClick={prev}>
                    ← Назад
                </Button>
                <Button variant="secondary" className="flex-1" onClick={next}>
                    Вперёд →
                </Button>
            </div>
        </div>
    );
}