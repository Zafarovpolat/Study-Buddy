// frontend/src/components/OutputViewer.tsx
import { useState } from 'react';
import { FileText, Zap, HelpCircle, BookOpen, Layers, RefreshCw, ChevronDown, ChevronUp, Swords, File } from 'lucide-react';
import { Button, Card } from './ui';
import { DebateTab } from './DebateTab';
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
    groupId?: string;
    materialTitle?: string;
    materialContent?: string;
}

const formatConfig: Record<string, { icon: typeof FileText; label: string; color: string }> = {
    source: { icon: File, label: 'Источник', color: 'text-gray-500' },
    smart_notes: { icon: FileText, label: 'Конспект', color: 'text-blue-500' },
    quiz: { icon: HelpCircle, label: 'Тест', color: 'text-green-500' },
    debate: { icon: Swords, label: 'Дебаты', color: 'text-red-500' },
    flashcards: { icon: Layers, label: 'Карточки', color: 'text-pink-500' },
    tldr: { icon: Zap, label: 'TL;DR', color: 'text-yellow-500' },
    glossary: { icon: BookOpen, label: 'Глоссарий', color: 'text-purple-500' },
};

export function OutputViewer({ materialId, outputs, onRefresh, groupId, materialTitle, materialContent }: OutputViewerProps) {
    const [activeFormat, setActiveFormat] = useState<string>(
        'source' // Default to Source
    );
    const [isRegenerating, setIsRegenerating] = useState(false);

    const activeOutput = outputs.find((o) => o.format === activeFormat);
    const isDebateTab = activeFormat === 'debate';
    const isSourceTab = activeFormat === 'source';

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

    // Define tab order
    const tabOrder = ['source', 'smart_notes', 'quiz', 'debate', 'flashcards', 'tldr', 'glossary'];

    return (
        <div className="space-y-4">
            {/* Format Tabs */}
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                {tabOrder.map((format) => {
                    const config = formatConfig[format];
                    if (!config) return null;

                    const Icon = config.icon;
                    // Source and Debate are always available (if logic allows), others depend on outputs
                    const hasOutput = format === 'source' || format === 'debate' || outputs.some((o) => o.format === format);

                    // If it's a generated format but doesn't exist, we still show it but dimmed? 
                    // Or maybe we only show if it exists OR if it's one of the core tabs we want to encourage?
                    // Let's show all core tabs, but dim if not generated.

                    return (
                        <button
                            key={format}
                            onClick={() => {
                                telegram.haptic('selection');
                                setActiveFormat(format);
                            }}
                            className={`flex items-center gap-2 px-4 py-2 rounded-xl whitespace-nowrap transition-all ${activeFormat === format
                                ? format === 'debate'
                                    ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white'
                                    : 'bg-lecto-button text-lecto-button-text'
                                : hasOutput
                                    ? 'bg-lecto-secondary text-lecto-text'
                                    : 'bg-lecto-secondary/50 text-lecto-hint'
                                }`}
                        >
                            <Icon className={`w-4 h-4 ${activeFormat === format ? '' : config.color}`} />
                            {config.label}
                        </button>
                    );
                })}
            </div>

            {/* Content */}
            <Card className="min-h-[300px] overflow-hidden">
                {isSourceTab ? (
                    <div className="prose prose-sm max-w-none text-lecto-text leading-relaxed whitespace-pre-wrap">
                        {materialContent || 'Нет содержимого'}
                    </div>
                ) : isDebateTab ? (
                    <DebateTab
                        materialId={materialId}
                        materialTitle={materialTitle || 'Материал'}
                        materialContent={materialContent}
                    />
                ) : activeOutput ? (
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
                            materialId={materialId}
                            groupId={groupId}
                        />
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-64 text-lecto-hint">
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
function ContentRenderer({
    content,
    format,
    materialId,
    groupId
}: {
    content: string;
    format: string;
    materialId: string;
    groupId?: string;
}) {
    try {
        const data = JSON.parse(content);

        switch (format) {
            case 'quiz':
                return <QuizViewer data={data} materialId={materialId} groupId={groupId} />;
            case 'flashcards':
                return <FlashcardsViewer data={data} />;
            case 'glossary':
                return <GlossaryViewer data={data} />;
            default:
                return <MarkdownViewer content={content} />;
        }
    } catch {
        return <MarkdownViewer content={content} />;
    }
}

// ============ MARKDOWN VIEWER ============
function MarkdownViewer({ content }: { content: string }) {
    let html = content
        .replace(/```[\s\S]*?```/g, (match) => {
            const code = match.replace(/```\w*\n?/g, '').trim();
            return `<pre class="bg-lecto-secondary p-3 rounded-lg text-sm overflow-x-auto my-2 whitespace-pre-wrap break-words">${code}</pre>`;
        })
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.*?)__/g, '<strong>$1</strong>')
        .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
        .replace(/(?<!_)_([^_]+)_(?!_)/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code class="bg-lecto-secondary px-1 rounded text-sm break-all">$1</code>')
        .replace(/^### (.*?)$/gm, '<h3 class="font-semibold text-base mt-3 mb-1">$1</h3>')
        .replace(/^## (.*?)$/gm, '<h2 class="font-bold text-lg mt-4 mb-2">$1</h2>')
        .replace(/^# (.*?)$/gm, '<h1 class="font-bold text-xl mt-4 mb-2">$1</h1>')
        .replace(/^- (.*?)$/gm, '<li class="ml-4 list-disc">$1</li>')
        .replace(/^\* (.*?)$/gm, '<li class="ml-4 list-disc">$1</li>')
        .replace(/^\d+\. (.*?)$/gm, '<li class="ml-4 list-decimal">$1</li>')
        .replace(/\n\n/g, '</p><p class="mt-2">')
        .replace(/\n/g, '<br/>');

    html = `<p>${html}</p>`;
    html = html.replace(/(<li class="ml-4 list-disc">.*?<\/li>)+/g, '<ul class="my-2">$&</ul>');
    html = html.replace(/(<li class="ml-4 list-decimal">.*?<\/li>)+/g, '<ol class="my-2">$&</ol>');

    return (
        <div
            className="prose prose-sm max-w-none text-lecto-text leading-relaxed overflow-x-hidden break-words"
            style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}
            dangerouslySetInnerHTML={{ __html: html }}
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
        return <p className="text-lecto-hint text-center">Термины не найдены</p>;
    }

    return (
        <div className="space-y-2">
            <p className="text-sm text-lecto-hint mb-3">
                📚 {terms.length} терминов
            </p>

            {terms.map((item, index) => (
                <div
                    key={index}
                    className="border border-lecto-hint/20 rounded-xl overflow-hidden"
                >
                    <button
                        onClick={() => {
                            setExpandedIndex(expandedIndex === index ? null : index);
                            telegram.haptic('selection');
                        }}
                        className="w-full p-4 flex items-center justify-between text-left bg-lecto-secondary/50 hover:bg-lecto-secondary transition-colors"
                    >
                        <span className="font-medium text-purple-600 break-words">{item.term}</span>
                        {expandedIndex === index ? (
                            <ChevronUp className="w-4 h-4 text-lecto-hint flex-shrink-0 ml-2" />
                        ) : (
                            <ChevronDown className="w-4 h-4 text-lecto-hint flex-shrink-0 ml-2" />
                        )}
                    </button>

                    {expandedIndex === index && (
                        <div className="p-4 bg-lecto-bg border-t border-lecto-hint/20">
                            <p className="text-sm break-words">{item.definition}</p>
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
    difficulty?: string;
}

interface QuizViewerProps {
    data: any;
    materialId: string;
    groupId?: string;
}

function QuizViewer({ data, materialId, groupId }: QuizViewerProps) {
    const questions: Question[] = data.questions || [];
    const [currentIndex, setCurrentIndex] = useState(0);
    const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
    const [showResult, setShowResult] = useState(false);
    const [score, setScore] = useState(0);
    const [isFinished, setIsFinished] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    if (questions.length === 0) {
        return <p className="text-lecto-hint text-center">Вопросы не найдены</p>;
    }

    const question = questions[currentIndex];

    const options: string[] = Array.isArray(question.options)
        ? question.options
        : Object.values(question.options || {});

    const correctIndex = typeof question.correct === 'number'
        ? question.correct
        : parseInt(question.correct) || 0;

    const handleAnswer = (index: number) => {
        if (selectedAnswer !== null) return;

        telegram.haptic('selection');
        setSelectedAnswer(index);
        setShowResult(true);

        const newScore = index === correctIndex ? score + 1 : score;
        if (index === correctIndex) {
            setScore(newScore);
            telegram.haptic('success');
        } else {
            telegram.haptic('error');
        }

        if (currentIndex === questions.length - 1) {
            handleFinish(newScore);
        }
    };

    const handleFinish = async (finalScore: number) => {
        setIsFinished(true);

        if (groupId) {
            setIsSaving(true);
            try {
                await api.saveQuizResult(groupId, materialId, finalScore, questions.length);
            } catch (error) {
                console.error('Failed to save quiz result:', error);
            } finally {
                setIsSaving(false);
            }
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
        setIsFinished(false);
    };

    const showFinalResult = isFinished && showResult;

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between text-sm text-lecto-hint">
                <span>Вопрос {currentIndex + 1} из {questions.length}</span>
                <span>Счёт: {score}/{currentIndex + (showResult ? 1 : 0)}</span>
            </div>

            <div className="h-1 bg-lecto-secondary rounded-full overflow-hidden">
                <div
                    className="h-full bg-lecto-button transition-all"
                    style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
                />
            </div>

            {question.difficulty && (
                <span className={`text-xs px-2 py-1 rounded-full ${question.difficulty === 'hard'
                    ? 'bg-red-100 text-red-600'
                    : question.difficulty === 'medium'
                        ? 'bg-yellow-100 text-yellow-600'
                        : 'bg-green-100 text-green-600'
                    }`}>
                    {question.difficulty === 'hard' ? '🔥 Сложный' :
                        question.difficulty === 'medium' ? '📝 Средний' : '✅ Лёгкий'}
                </span>
            )}

            <p className="text-lg font-medium break-words">{question.question}</p>

            <div className="space-y-2">
                {options.map((option, index) => {
                    const isCorrect = index === correctIndex;
                    const isSelected = index === selectedAnswer;
                    const cleanOption = option.replace(/^[A-D]\)\s*/, '');

                    return (
                        <button
                            key={index}
                            onClick={() => handleAnswer(index)}
                            disabled={showResult}
                            className={`w-full p-4 rounded-xl text-left transition-all break-words ${showResult
                                ? isCorrect
                                    ? 'bg-green-500/20 border-2 border-green-500'
                                    : isSelected
                                        ? 'bg-red-500/20 border-2 border-red-500'
                                        : 'bg-lecto-secondary'
                                : 'bg-lecto-secondary hover:bg-lecto-hint/20'
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

            {showResult && question.explanation && (
                <Card variant="outlined" className="bg-lecto-button/5">
                    <p className="text-sm break-words">
                        <span className="font-semibold">💡 </span>
                        {question.explanation}
                    </p>
                </Card>
            )}

            {showResult && !showFinalResult && (
                <Button className="w-full" onClick={nextQuestion}>
                    Следующий вопрос →
                </Button>
            )}

            {showFinalResult && (
                <Card className="text-center bg-gradient-to-br from-lecto-button/20 to-lecto-button/5">
                    <p className="text-4xl mb-2">
                        {score === questions.length ? '🎉' : score >= questions.length * 0.7 ? '👍' : score >= questions.length * 0.5 ? '📚' : '💪'}
                    </p>
                    <p className="text-xl font-bold">
                        {score} из {questions.length}
                    </p>
                    <p className="text-sm text-lecto-hint mt-1">
                        {Math.round((score / questions.length) * 100)}% правильных
                    </p>

                    {isSaving && (
                        <p className="text-xs text-lecto-hint mt-2">Сохранение результата...</p>
                    )}

                    {groupId && !isSaving && (
                        <p className="text-xs text-green-600 mt-2">✓ Результат сохранён</p>
                    )}

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
    const cards: Flashcard[] = data.cards || data.flashcards || [];
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);
    const [known, setKnown] = useState<Set<number>>(new Set());

    if (cards.length === 0) {
        return <p className="text-lecto-hint text-center">Карточки не найдены</p>;
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
            <div className="flex items-center justify-between text-sm text-lecto-hint">
                <span>Карточка {currentIndex + 1} из {cards.length}</span>
                <span>Выучено: {known.size}/{cards.length}</span>
            </div>

            <div
                onClick={flip}
                className={`min-h-[200px] p-6 rounded-2xl flex items-center justify-center cursor-pointer transition-all transform hover:scale-[1.02] ${isFlipped
                    ? 'bg-gradient-to-br from-green-500/20 to-green-500/5'
                    : 'bg-gradient-to-br from-lecto-button/20 to-lecto-button/5'
                    } ${known.has(currentIndex) ? 'ring-2 ring-green-500' : ''}`}
            >
                <div className="text-center">
                    <p className="text-xs text-lecto-hint mb-2">
                        {isFlipped ? '← Ответ' : 'Вопрос →'}
                    </p>
                    <p className="text-lg font-medium break-words">
                        {isFlipped ? card.back : card.front}
                    </p>
                </div>
            </div>

            <p className="text-center text-xs text-lecto-hint">
                👆 Нажмите, чтобы перевернуть
            </p>

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