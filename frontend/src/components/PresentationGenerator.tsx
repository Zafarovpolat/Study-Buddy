// frontend/src/components/PresentationGenerator.tsx
import { useState } from 'react';
import {
    X,
    Presentation,
    Sparkles,
    Download,
    ChevronLeft,
    ChevronRight,
    Briefcase,
    GraduationCap,
    Palette,
    Minus,
    Crown,
} from 'lucide-react';
import { Button, Input, Card } from './ui';
import { api } from '../lib/api';
import { telegram } from '../lib/telegram';
import { useStore } from '../store/useStore';

interface PresentationGeneratorProps {
    isOpen: boolean;
    onClose: () => void;
}

type Style = 'professional' | 'educational' | 'creative' | 'minimal';
type Theme = 'blue' | 'green' | 'purple' | 'orange';

interface SlidePreview {
    type: string;
    title?: string;
    subtitle?: string;
    bullets?: string[];
    quote?: string;
    author?: string;
    left_title?: string;
    right_title?: string;
    call_to_action?: string;
}

interface PresentationPreview {
    title: string;
    subtitle?: string;
    slides_count: number;
    slides: SlidePreview[];
}

const STYLES: { value: Style; label: string; icon: React.ReactNode; desc: string }[] = [
    { value: 'professional', label: 'Деловой', icon: <Briefcase className="w-5 h-5" />, desc: 'Факты и данные' },
    { value: 'educational', label: 'Учебный', icon: <GraduationCap className="w-5 h-5" />, desc: 'Простые объяснения' },
    { value: 'creative', label: 'Креативный', icon: <Palette className="w-5 h-5" />, desc: 'Метафоры и идеи' },
    { value: 'minimal', label: 'Минимал', icon: <Minus className="w-5 h-5" />, desc: 'Только тезисы' },
];

const THEMES: { value: Theme; label: string; color: string }[] = [
    { value: 'blue', label: 'Синий', color: 'bg-blue-500' },
    { value: 'green', label: 'Зелёный', color: 'bg-green-500' },
    { value: 'purple', label: 'Фиолетовый', color: 'bg-purple-500' },
    { value: 'orange', label: 'Оранжевый', color: 'bg-orange-500' },
];

export function PresentationGenerator({ isOpen, onClose }: PresentationGeneratorProps) {
    const { user } = useStore();

    const [step, setStep] = useState<'form' | 'preview'>('form');
    const [topic, setTopic] = useState('');
    const [numSlides, setNumSlides] = useState(10);
    const [style, setStyle] = useState<Style>('professional');
    const [theme, setTheme] = useState<Theme>('blue');

    const [isGenerating, setIsGenerating] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const [preview, setPreview] = useState<PresentationPreview | null>(null);
    const [currentSlide, setCurrentSlide] = useState(0);

    if (!isOpen) return null;

    const isPro = user?.subscription_tier === 'pro';

    const handleGenerate = async () => {
        if (!topic.trim()) {
            telegram.alert('Введите тему презентации');
            return;
        }

        if (!isPro) {
            telegram.alert('Генератор презентаций доступен только для Pro пользователей');
            return;
        }

        setIsGenerating(true);
        telegram.haptic('medium');

        try {
            const result = await api.generatePresentationPreview(topic, numSlides, style);
            setPreview(result);
            setCurrentSlide(0);
            setStep('preview');
            telegram.haptic('success');
        } catch (error: any) {
            console.error('Generation error:', error);
            telegram.haptic('error');
            telegram.alert(error.response?.data?.detail || 'Ошибка генерации');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleDownload = async () => {
        setIsDownloading(true);
        telegram.haptic('medium');

        try {
            await api.downloadPresentation(topic, numSlides, style, theme);
            telegram.haptic('success');
            telegram.alert('Презентация скачана!');
        } catch (error: any) {
            console.error('Download error:', error);
            telegram.haptic('error');
            telegram.alert('Ошибка скачивания');
        } finally {
            setIsDownloading(false);
        }
    };

    const handleClose = () => {
        setStep('form');
        setTopic('');
        setPreview(null);
        setCurrentSlide(0);
        onClose();
    };

    const renderSlidePreview = (slide: SlidePreview, index: number) => {
        const themeColors = {
            blue: 'from-blue-600 to-blue-400',
            green: 'from-green-600 to-green-400',
            purple: 'from-purple-600 to-purple-400',
            orange: 'from-orange-600 to-orange-400',
        };

        return (
            <div className="bg-white rounded-lg shadow-lg aspect-video p-4 flex flex-col">
                {/* Header */}
                <div className={`bg-gradient-to-r ${themeColors[theme]} rounded-t-lg px-3 py-2 -mx-4 -mt-4 mb-3`}>
                    <p className="text-white font-bold text-sm truncate">
                        {slide.title || slide.quote?.slice(0, 50) || `Слайд ${index + 1}`}
                    </p>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden">
                    {slide.type === 'title' && (
                        <div className="h-full flex flex-col items-center justify-center text-center">
                            <p className="font-bold text-gray-800 text-lg">{slide.title}</p>
                            {slide.subtitle && (
                                <p className="text-gray-500 text-sm mt-1">{slide.subtitle}</p>
                            )}
                        </div>
                    )}

                    {slide.type === 'content' && slide.bullets && (
                        <ul className="space-y-1 text-xs text-gray-700">
                            {slide.bullets.slice(0, 4).map((bullet, i) => (
                                <li key={i} className="flex items-start gap-1">
                                    <span className="text-blue-500">•</span>
                                    <span className="line-clamp-2">{bullet}</span>
                                </li>
                            ))}
                            {slide.bullets.length > 4 && (
                                <li className="text-gray-400 text-xs">+{slide.bullets.length - 4} ещё</li>
                            )}
                        </ul>
                    )}

                    {slide.type === 'two_columns' && (
                        <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>
                                <p className="font-medium text-gray-800 mb-1">{slide.left_title}</p>
                            </div>
                            <div>
                                <p className="font-medium text-gray-800 mb-1">{slide.right_title}</p>
                            </div>
                        </div>
                    )}

                    {slide.type === 'quote' && (
                        <div className="h-full flex flex-col items-center justify-center text-center px-2">
                            <p className="text-gray-600 italic text-xs line-clamp-3">"{slide.quote}"</p>
                            {slide.author && (
                                <p className="text-gray-400 text-xs mt-2">— {slide.author}</p>
                            )}
                        </div>
                    )}

                    {slide.type === 'conclusion' && (
                        <div className="space-y-1">
                            {slide.bullets?.slice(0, 3).map((bullet, i) => (
                                <p key={i} className="text-xs text-gray-700 flex items-start gap-1">
                                    <span className="text-green-500">✓</span>
                                    <span className="line-clamp-1">{bullet}</span>
                                </p>
                            ))}
                        </div>
                    )}
                </div>

                {/* Slide number */}
                <div className="text-center text-xs text-gray-400 mt-2">
                    {index + 1} / {preview?.slides.length}
                </div>
            </div>
        );
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-end justify-center">
            <div className="bg-tg-bg w-full max-w-lg rounded-t-3xl max-h-[90vh] overflow-hidden animate-slide-up flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-tg-secondary">
                    <div className="flex items-center gap-2">
                        {step === 'preview' && (
                            <button
                                onClick={() => setStep('form')}
                                className="p-1 hover:bg-tg-secondary rounded-full"
                            >
                                <ChevronLeft className="w-5 h-5" />
                            </button>
                        )}
                        <Presentation className="w-6 h-6 text-purple-500" />
                        <h2 className="text-lg font-bold">
                            {step === 'form' ? 'Генератор презентаций' : 'Превью'}
                        </h2>
                    </div>
                    <button
                        onClick={handleClose}
                        className="p-2 hover:bg-tg-secondary rounded-full"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-4">
                    {step === 'form' ? (
                        <div className="space-y-5">
                            {/* Pro Badge */}
                            {!isPro && (
                                <div className="bg-gradient-to-r from-yellow-100 to-orange-100 dark:from-yellow-900/30 dark:to-orange-900/30 rounded-xl p-4 flex items-center gap-3">
                                    <Crown className="w-8 h-8 text-yellow-500" />
                                    <div>
                                        <p className="font-bold text-yellow-700 dark:text-yellow-400">Только для Pro</p>
                                        <p className="text-sm text-yellow-600 dark:text-yellow-500">
                                            Оформите подписку для доступа
                                        </p>
                                    </div>
                                </div>
                            )}

                            {/* Topic Input */}
                            <div>
                                <Input
                                    label="Тема презентации"
                                    placeholder="Например: Искусственный интеллект в медицине"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    disabled={!isPro}
                                />
                            </div>

                            {/* Number of Slides */}
                            <div>
                                <label className="block text-sm font-medium text-tg-hint mb-2">
                                    Количество слайдов: {numSlides}
                                </label>
                                <input
                                    type="range"
                                    min="5"
                                    max="20"
                                    value={numSlides}
                                    onChange={(e) => setNumSlides(Number(e.target.value))}
                                    disabled={!isPro}
                                    className="w-full h-2 bg-tg-secondary rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <div className="flex justify-between text-xs text-tg-hint mt-1">
                                    <span>5</span>
                                    <span>20</span>
                                </div>
                            </div>

                            {/* Style Selection */}
                            <div>
                                <label className="block text-sm font-medium text-tg-hint mb-2">
                                    Стиль презентации
                                </label>
                                <div className="grid grid-cols-2 gap-2">
                                    {STYLES.map((s) => (
                                        <button
                                            key={s.value}
                                            onClick={() => isPro && setStyle(s.value)}
                                            disabled={!isPro}
                                            className={`p-3 rounded-xl border-2 transition-all ${style === s.value
                                                ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                                                : 'border-tg-secondary hover:border-purple-300'
                                                } ${!isPro ? 'opacity-50' : ''}`}
                                        >
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className={style === s.value ? 'text-purple-500' : 'text-tg-hint'}>
                                                    {s.icon}
                                                </span>
                                                <span className="font-medium text-sm">{s.label}</span>
                                            </div>
                                            <p className="text-xs text-tg-hint">{s.desc}</p>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Theme Selection */}
                            <div>
                                <label className="block text-sm font-medium text-tg-hint mb-2">
                                    Цветовая тема
                                </label>
                                <div className="flex gap-3">
                                    {THEMES.map((t) => (
                                        <button
                                            key={t.value}
                                            onClick={() => isPro && setTheme(t.value)}
                                            disabled={!isPro}
                                            className={`flex-1 p-3 rounded-xl border-2 transition-all ${theme === t.value
                                                ? 'border-gray-800 dark:border-white'
                                                : 'border-transparent'
                                                } ${!isPro ? 'opacity-50' : ''}`}
                                        >
                                            <div className={`w-full h-8 rounded-lg ${t.color} mb-2`} />
                                            <p className="text-xs font-medium">{t.label}</p>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Info */}
                            <div className="bg-tg-secondary/50 rounded-xl p-3">
                                <p className="text-xs text-tg-hint">
                                    ✨ AI создаст структурированную презентацию с заголовками,
                                    пунктами, цитатами и заметками докладчика
                                </p>
                            </div>
                        </div>
                    ) : (
                        /* Preview Step */
                        <div className="space-y-4">
                            {/* Title */}
                            <div className="text-center">
                                <h3 className="font-bold text-lg">{preview?.title}</h3>
                                {preview?.subtitle && (
                                    <p className="text-tg-hint text-sm">{preview.subtitle}</p>
                                )}
                                <p className="text-purple-500 text-sm mt-1">
                                    {preview?.slides_count} слайдов
                                </p>
                            </div>

                            {/* Slide Preview */}
                            {preview && preview.slides.length > 0 && (
                                <div className="relative">
                                    {renderSlidePreview(preview.slides[currentSlide], currentSlide)}

                                    {/* Navigation */}
                                    <div className="flex items-center justify-center gap-4 mt-4">
                                        <button
                                            onClick={() => setCurrentSlide(Math.max(0, currentSlide - 1))}
                                            disabled={currentSlide === 0}
                                            className="p-2 rounded-full bg-tg-secondary disabled:opacity-30"
                                        >
                                            <ChevronLeft className="w-5 h-5" />
                                        </button>

                                        {/* Dots */}
                                        <div className="flex gap-1">
                                            {preview.slides.slice(0, 10).map((_, i) => (
                                                <button
                                                    key={i}
                                                    onClick={() => setCurrentSlide(i)}
                                                    className={`w-2 h-2 rounded-full transition-all ${i === currentSlide
                                                        ? 'bg-purple-500 w-4'
                                                        : 'bg-tg-secondary'
                                                        }`}
                                                />
                                            ))}
                                            {preview.slides.length > 10 && (
                                                <span className="text-xs text-tg-hint ml-1">
                                                    +{preview.slides.length - 10}
                                                </span>
                                            )}
                                        </div>

                                        <button
                                            onClick={() => setCurrentSlide(Math.min(preview.slides.length - 1, currentSlide + 1))}
                                            disabled={currentSlide === preview.slides.length - 1}
                                            className="p-2 rounded-full bg-tg-secondary disabled:opacity-30"
                                        >
                                            <ChevronRight className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Slides List */}
                            <div className="mt-4">
                                <p className="text-sm font-medium text-tg-hint mb-2">Все слайды:</p>
                                <div className="space-y-2 max-h-40 overflow-y-auto">
                                    {preview?.slides.map((slide, i) => (
                                        <button
                                            key={i}
                                            onClick={() => setCurrentSlide(i)}
                                            className={`w-full text-left p-2 rounded-lg text-sm transition-colors ${i === currentSlide
                                                ? 'bg-purple-100 dark:bg-purple-900/30'
                                                : 'bg-tg-secondary/50 hover:bg-tg-secondary'
                                                }`}
                                        >
                                            <span className="text-purple-500 font-medium mr-2">{i + 1}.</span>
                                            <span className="text-tg-text">
                                                {slide.title || slide.quote?.slice(0, 40) || `Слайд ${i + 1}`}
                                            </span>
                                            <span className="text-xs text-tg-hint ml-2">({slide.type})</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-tg-secondary">
                    {step === 'form' ? (
                        <Button
                            className="w-full"
                            size="lg"
                            onClick={handleGenerate}
                            isLoading={isGenerating}
                            disabled={!topic.trim() || !isPro || isGenerating}
                        >
                            <Sparkles className="w-5 h-5 mr-2" />
                            {isGenerating ? 'Генерация...' : 'Сгенерировать превью'}
                        </Button>
                    ) : (
                        <Button
                            className="w-full bg-green-500 hover:bg-green-600"
                            size="lg"
                            onClick={handleDownload}
                            isLoading={isDownloading}
                            disabled={isDownloading}
                        >
                            <Download className="w-5 h-5 mr-2" />
                            {isDownloading ? 'Скачивание...' : 'Скачать PPTX'}
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
}