// frontend/src/components/OutputViewer.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { useState } from 'react';
import { FileText, Zap, HelpCircle, BookOpen, Layers, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
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
                        <ContentRenderer
                            content={activeOutput.content}
                            format={activeFormat}
                        />
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

// Универсальный рендерер контента
function ContentRenderer({ content, format }: { content: string; format: string }) {
    // Пробуем распарсить JSON
    try {
        const data = JSON.parse(content);

        switch (format) {
            case 'quiz':
                return <QuizViewer data={data} />;
            case 'flashcards':
                return <FlashcardsViewer data={data} />;
            case 'glossary':
                return <GlossaryViewer data={data} />;
            default:
                return <MarkdownViewer content={content} />;
        }
    } catch {
        // Если не JSON - рендерим как markdown
        return <MarkdownViewer content={content} />;
    }
}

// Markdown Viewer
function MarkdownViewer({ content }: { content: string }) {
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

// ============ GLOSSARY VIEWER ============
interface Term {
    term: string;
    definition: string;
}

function GlossaryViewer({ data }: { data: any }) {
    const terms: Term[] = data.terms || [];
    const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

    if (terms.length === 0) {
        return <p className="text-tg-hint text-center">Термины не найдены</p>;
    }

    return (
        <div className="space-y-2">
            <p className="text-sm text-tg-hint mb-3">
                📚 {terms.length} терминов
            </p>

            {terms.map((item, index) => (
                <div
                    key={index}
                    className="border border-tg-hint/20 rounded-xl overflow-hidden"
                >
                    <button
                        onClick={() => {
                            setExpandedIndex(expandedIndex === index ? null : index);
                            telegram.haptic('selection');
                        }}
                        className="w-full p-4 flex items-center justify-between text-left bg-tg-secondary/50 hover:bg-tg-secondary transition-colors"
                    >
                        <span className="font-medium text-purple-600">{item.term}</span>
                        {expandedIndex === index ? (
                            <ChevronUp className="w-4 h-4 text-tg-hint" />
                        ) : (
                            <ChevronDown className="w-4 h-4 text-tg-hint" />
                        )}
                    </button>

                    {expandedIndex === index && (
                        <div className="p-4 bg-tg-bg border-t border-tg-hint/20">
                            <p className="text-sm">{item.definition}</p>
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}

// ============ QUIZ VIEWER ============
interface Question {
    question: string;
    options: string[] | Record<string, string>;
    correct: number | string;
    explanation?: string;
}

function QuizViewer({ data }: { data: any }) {
    const questions: Question[] = data.questions || [];
    const [currentIndex, setCurrentIndex] = useState(0);
    const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
    const [showResult, setShowResult] = useState(false);
    const [score, setScore] = useState(0);

    if (questions.length === 0) {
        return <p className="text-tg-hint text-center">Вопросы не найдены</p>;
    }

    const question = questions[currentIndex];

    // Нормализуем options в массив
    const options: string[] = Array.isArray(question.options)
        ? question.options
        : Object.values(question.options || {});

    // Нормализуем correct в индекс
    const correctIndex = typeof question.correct === 'number'
        ? question.correct
        : parseInt(question.correct) || 0;

    const handleAnswer = (index: number) => {
        if (selectedAnswer !== null) return;

        telegram.haptic('selection');
        setSelectedAnswer(index);
        setShowResult(true);

        if (index === correctIndex) {
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

    const restart = () => {
        setCurrentIndex(0);
        setSelectedAnswer(null);
        setShowResult(false);
        setScore(0);
    };

    const isFinished = currentIndex === questions.length - 1 && showResult;

    return (
        <div className="space-y-4">
            {/* Progress */}
            <div className="flex items-center justify-between text-sm text-tg-hint">
                <span>Вопрос {currentIndex + 1} из {questions.length}</span>
                <span>Счёт: {score}/{questions.length}</span>
            </div>

            {/* Progress bar */}
            <div className="h-1 bg-tg-secondary rounded-full overflow-hidden">
                <div
                    className="h-full bg-tg-button transition-all"
                    style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
                />
            </div>

            {/* Question */}
            <p className="text-lg font-medium">{question.question}</p>

            {/* Options */}
            <div className="space-y-2">
                {options.map((option, index) => {
                    const isCorrect = index === correctIndex;
                    const isSelected = index === selectedAnswer;

                    // Убираем префикс типа "A) " если есть
                    const cleanOption = option.replace(/^[A-D]\)\s*/, '');

                    return (
                        <button
                            key={index}
                            onClick={() => handleAnswer(index)}
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
                            <span className="font-medium mr-2">
                                {String.fromCharCode(65 + index)}.
                            </span>
                            {cleanOption}
                        </button>
                    );
                })}
            </div>

            {/* Explanation */}
            {showResult && question.explanation && (
                <Card variant="outlined" className="bg-tg-button/5">
                    <p className="text-sm">
                        <span className="font-semibold">💡 </span>
                        {question.explanation}
                    </p>
                </Card>
            )}

            {/* Next Button */}
            {showResult && !isFinished && (
                <Button className="w-full" onClick={nextQuestion}>
                    Следующий вопрос →
                </Button>
            )}

            {/* Final Result */}
            {isFinished && (
                <Card className="text-center bg-gradient-to-br from-tg-button/20 to-tg-button/5">
                    <p className="text-4xl mb-2">
                        {score === questions.length ? '🎉' : score >= questions.length / 2 ? '👍' : '📚'}
                    </p>
                    <p className="text-xl font-bold">
                        {score} из {questions.length}
                    </p>
                    <p className="text-sm text-tg-hint mt-1">
                        {Math.round((score / questions.length) * 100)}% правильных
                    </p>
                    <Button className="mt-4" variant="secondary" onClick={restart}>
                        Пройти заново
                    </Button>
                </Card>
            )}
        </div>
    );
}

// ============ FLASHCARDS VIEWER ============
interface Flashcard {
    front: string;
    back: string;
}

function FlashcardsViewer({ data }: { data: any }) {
    // Поддерживаем оба формата: cards и flashcards
    const cards: Flashcard[] = data.cards || data.flashcards || [];
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);
    const [known, setKnown] = useState<Set<number>>(new Set());

    if (cards.length === 0) {
        return <p className="text-tg-hint text-center">Карточки не найдены</p>;
    }

    const card = cards[currentIndex];

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

    const markKnown = () => {
        const newKnown = new Set(known);
        if (known.has(currentIndex)) {
            newKnown.delete(currentIndex);
        } else {
            newKnown.add(currentIndex);
        }
        setKnown(newKnown);
        telegram.haptic('success');
    };

    return (
        <div className="space-y-4">
            {/* Progress */}
            <div className="flex items-center justify-between text-sm text-tg-hint">
                <span>Карточка {currentIndex + 1} из {cards.length}</span>
                <span>Выучено: {known.size}/{cards.length}</span>
            </div>

            {/* Card */}
            <div
                onClick={flip}
                className={`min-h-[200px] p-6 rounded-2xl flex items-center justify-center cursor-pointer transition-all transform hover:scale-[1.02] ${isFlipped
                        ? 'bg-gradient-to-br from-green-500/20 to-green-500/5'
                        : 'bg-gradient-to-br from-tg-button/20 to-tg-button/5'
                    } ${known.has(currentIndex) ? 'ring-2 ring-green-500' : ''}`}
            >
                <div className="text-center">
                    <p className="text-xs text-tg-hint mb-2">
                        {isFlipped ? '← Ответ' : 'Вопрос →'}
                    </p>
                    <p className="text-lg font-medium">
                        {isFlipped ? card.back : card.front}
                    </p>
                </div>
            </div>

            <p className="text-center text-xs text-tg-hint">
                👆 Нажмите, чтобы перевернуть
            </p>

            {/* Actions */}
            <div className="flex gap-2">
                <Button variant="secondary" className="flex-1" onClick={prev}>
                    ←
                </Button>
                <Button
                    variant={known.has(currentIndex) ? "primary" : "secondary"}
                    className="flex-1"
                    onClick={markKnown}
                >
                    {known.has(currentIndex) ? '✓ Выучено' : 'Знаю'}
                </Button>
                <Button variant="secondary" className="flex-1" onClick={next}>
                    →
                </Button>
            </div>
        </div>
    );
}