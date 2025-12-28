// frontend/src/components/OnboardingModal.tsx
import { useState } from 'react';
import { Sparkles, Users, Zap, ChevronRight, ChevronLeft, Check, GraduationCap, Scale, TrendingUp, Globe, Code, Stethoscope, BookOpen } from 'lucide-react';
import { Button, ProgressBar } from './ui';
import { api } from '../lib/api';
import { telegram } from '../lib/telegram';

interface OnboardingModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const FIELDS_OF_STUDY = [
    { id: 'law', name: 'Юриспруденция', icon: Scale, color: 'text-blue-500' },
    { id: 'economics', name: 'Экономика', icon: TrendingUp, color: 'text-green-500' },
    { id: 'ir', name: 'Международные отношения', icon: Globe, color: 'text-purple-500' },
    { id: 'it', name: 'IT и технологии', icon: Code, color: 'text-orange-500' },
    { id: 'medicine', name: 'Медицина', icon: Stethoscope, color: 'text-red-500' },
    { id: 'other', name: 'Другое', icon: BookOpen, color: 'text-gray-500' },
];

const SLIDES = [
    {
        id: 'welcome',
        icon: GraduationCap,
        title: "Lecto",
        subtitle: "Ваш личный академический ассистент",
        color: "from-blue-500/20 to-indigo-600/20",
    },
    {
        id: 'analyze',
        icon: Sparkles,
        title: "Анализ за секунды",
        subtitle: "Загружайте лекции и документы — получайте конспекты, тесты, карточки",
        color: "from-purple-500/20 to-pink-600/20",
    },
    {
        id: 'debate',
        icon: Zap,
        title: "Дебатируй с AI",
        subtitle: "Проверяйте знания в интерактивном споре. Зарабатывайте Intellect Points!",
        color: "from-yellow-500/20 to-orange-600/20",
    },
    {
        id: 'personalize',
        icon: Users,
        title: "Настройка",
        subtitle: "Выберите ваше направление обучения для персонализированного контента",
        color: "from-green-500/20 to-emerald-600/20",
        action: 'select_field'
    },
];

export function OnboardingModal({ isOpen, onClose }: OnboardingModalProps) {
    const [currentSlide, setCurrentSlide] = useState(0);
    const [selectedField, setSelectedField] = useState<string | null>(null);
    const [selectedRegion, setSelectedRegion] = useState<'global' | 'uz'>('global');
    const [isLoading, setIsLoading] = useState(false);

    if (!isOpen) return null;

    const slide = SLIDES[currentSlide];
    const isLastSlide = currentSlide === SLIDES.length - 1;
    const isPersonalizeStep = slide.action === 'select_field';

    const handleNext = () => {
        telegram.haptic('light');
        if (currentSlide < SLIDES.length - 1) {
            setCurrentSlide(currentSlide + 1);
        } else {
            handleComplete();
        }
    };

    const handlePrev = () => {
        telegram.haptic('light');
        if (currentSlide > 0) {
            setCurrentSlide(currentSlide - 1);
        }
    };

    const handleComplete = async () => {
        if (isPersonalizeStep && !selectedField) {
            telegram.alert('Выберите направление обучения');
            return;
        }

        setIsLoading(true);

        try {
            // Сохраняем персонализацию
            await api.updatePreferences({
                field_of_study: selectedField || undefined,  // ← добавь || undefined
                region: selectedRegion,
            });

            localStorage.setItem('lecto_onboarding_completed', 'true');
            telegram.haptic('success');
            onClose();
        } catch (error) {
            console.error('Failed to save preferences:', error);
            // Всё равно закрываем — можно настроить позже
            localStorage.setItem('lecto_onboarding_completed', 'true');
            onClose();
        } finally {
            setIsLoading(false);
        }
    };

    const handleSkip = () => {
        localStorage.setItem('lecto_onboarding_completed', 'true');
        telegram.haptic('light');
        onClose();
    };

    const Icon = slide.icon;

    return (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0D1117] w-full max-w-md rounded-3xl overflow-hidden animate-slide-up border border-[#30363D]">
                {/* Progress Bar */}
                <div className="px-6 pt-6">
                    <ProgressBar
                        value={currentSlide + 1}
                        max={SLIDES.length}
                        variant="gold"
                        size="sm"
                    />
                </div>

                {/* Skip */}
                <div className="flex justify-end px-6 pt-2">
                    <button
                        onClick={handleSkip}
                        className="text-[#8B949E] text-sm hover:text-white transition-colors"
                    >
                        Пропустить
                    </button>
                </div>

                {/* Content */}
                <div className="px-8 pb-8">
                    {!isPersonalizeStep ? (
                        <>
                            {/* Icon */}
                            <div className={`w-32 h-32 mx-auto rounded-3xl bg-gradient-to-br ${slide.color} flex items-center justify-center mb-6`}>
                                <Icon className="w-16 h-16 text-white" />
                            </div>

                            {/* Text */}
                            <h2 className="text-2xl font-bold text-center mb-3 text-white tracking-tight">
                                {slide.title}
                            </h2>
                            <p className="text-[#8B949E] text-center leading-relaxed">
                                {slide.subtitle}
                            </p>
                        </>
                    ) : (
                        <>
                            {/* Personalization Step */}
                            <h2 className="text-xl font-bold text-center mb-2 text-white tracking-tight">
                                Твоё направление?
                            </h2>
                            <p className="text-[#8B949E] text-center text-sm mb-6">
                                Это поможет показывать релевантный контент
                            </p>

                            {/* Fields Grid */}
                            <div className="grid grid-cols-2 gap-3 mb-6">
                                {FIELDS_OF_STUDY.map((field) => {
                                    const FieldIcon = field.icon;
                                    const isSelected = selectedField === field.id;

                                    return (
                                        <button
                                            key={field.id}
                                            onClick={() => {
                                                setSelectedField(field.id);
                                                telegram.haptic('selection');
                                            }}
                                            className={`p-4 rounded-2xl border-2 transition-all ${isSelected
                                                ? 'border-[#FFD700] bg-[#FFD700]/10'
                                                : 'border-[#30363D] bg-[#161B22] hover:border-[#484F58]'
                                                }`}
                                        >
                                            <FieldIcon className={`w-8 h-8 mx-auto mb-2 ${field.color}`} />
                                            <span className="text-sm font-medium text-white block text-center">
                                                {field.name}
                                            </span>
                                            {isSelected && (
                                                <Check className="w-4 h-4 text-[#FFD700] mx-auto mt-2" />
                                            )}
                                        </button>
                                    );
                                })}
                            </div>

                            {/* Region Toggle */}
                            <div className="flex bg-[#161B22] rounded-xl p-1 mb-4">
                                <button
                                    onClick={() => { setSelectedRegion('global'); telegram.haptic('light'); }}
                                    className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${selectedRegion === 'global'
                                        ? 'bg-[#21262D] text-white'
                                        : 'text-[#8B949E]'
                                        }`}
                                >
                                    🌍 Мир
                                </button>
                                <button
                                    onClick={() => { setSelectedRegion('uz'); telegram.haptic('light'); }}
                                    className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${selectedRegion === 'uz'
                                        ? 'bg-[#21262D] text-white'
                                        : 'text-[#8B949E]'
                                        }`}
                                >
                                    🇺🇿 Узбекистан
                                </button>
                            </div>
                        </>
                    )}

                    {/* Dots */}
                    {!isPersonalizeStep && (
                        <div className="flex justify-center gap-2 my-6">
                            {SLIDES.map((_, index) => (
                                <button
                                    key={index}
                                    onClick={() => {
                                        setCurrentSlide(index);
                                        telegram.haptic('light');
                                    }}
                                    className={`h-2 rounded-full transition-all ${index === currentSlide
                                        ? 'w-6 bg-gradient-to-r from-[#FFD700] to-[#FFA500]'
                                        : 'w-2 bg-[#30363D]'
                                        }`}
                                />
                            ))}
                        </div>
                    )}

                    {/* Buttons */}
                    <div className="flex gap-3 mt-6">
                        {currentSlide > 0 && (
                            <Button
                                variant="secondary"
                                onClick={handlePrev}
                                className="flex-shrink-0 bg-[#21262D] border-[#30363D]"
                            >
                                <ChevronLeft className="w-5 h-5" />
                            </Button>
                        )}

                        <Button
                            onClick={handleNext}
                            className="flex-1 bg-gradient-to-r from-[#FFD700] to-[#FFA500] text-black font-semibold"
                            size="lg"
                            isLoading={isLoading}
                            disabled={isPersonalizeStep && !selectedField}
                        >
                            {isLastSlide ? (
                                <>🚀 Начать</>
                            ) : (
                                <>
                                    Далее
                                    <ChevronRight className="w-5 h-5 ml-1" />
                                </>
                            )}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}