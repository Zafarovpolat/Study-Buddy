// frontend/src/components/OnboardingModal.tsx
import { useState } from 'react';
import { Upload, Sparkles, Users, Zap, ChevronRight, ChevronLeft } from 'lucide-react';
import { Button } from './ui';
import { telegram } from '../lib/telegram';

interface OnboardingModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const slides = [
    {
        icon: <Upload className="w-16 h-16 text-blue-500" />,
        title: "Загружай материалы",
        description: "PDF, DOCX, фото конспектов или просто текст. Lecto понимает всё!",
        color: "from-blue-500/20 to-blue-600/20",
    },
    {
        icon: <Sparkles className="w-16 h-16 text-purple-500" />,
        title: "AI создаёт контент",
        description: "Умные конспекты, тесты с 15-20 вопросами, глоссарий и карточки для запоминания",
        color: "from-purple-500/20 to-purple-600/20",
    },
    {
        icon: <Users className="w-16 h-16 text-green-500" />,
        title: "Учись с друзьями",
        description: "Создавай группы, делись материалами и соревнуйся в тестах!",
        color: "from-green-500/20 to-green-600/20",
    },
    {
        icon: <Zap className="w-16 h-16 text-yellow-500" />,
        title: "Готов начать?",
        description: "3 бесплатных материала в день. Загрузи первый прямо сейчас!",
        color: "from-yellow-500/20 to-yellow-600/20",
    },
];

export function OnboardingModal({ isOpen, onClose }: OnboardingModalProps) {
    const [currentSlide, setCurrentSlide] = useState(0);

    if (!isOpen) return null;

    const handleNext = () => {
        telegram.haptic('light');
        if (currentSlide < slides.length - 1) {
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

    const handleComplete = () => {
        localStorage.setItem('lecto_onboarding_completed', 'true');
        telegram.haptic('success');
        onClose();
    };

    const handleSkip = () => {
        localStorage.setItem('lecto_onboarding_completed', 'true');
        telegram.haptic('light');
        onClose();
    };

    const slide = slides[currentSlide];
    const isLastSlide = currentSlide === slides.length - 1;

    return (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
            <div className="bg-tg-bg w-full max-w-sm rounded-3xl overflow-hidden animate-slide-up">
                {/* Skip button */}
                <div className="flex justify-end p-4">
                    <button
                        onClick={handleSkip}
                        className="text-tg-hint text-sm hover:text-tg-text transition-colors"
                    >
                        Пропустить
                    </button>
                </div>

                {/* Content */}
                <div className="px-8 pb-8">
                    {/* Icon */}
                    <div className={`w-32 h-32 mx-auto rounded-full bg-gradient-to-br ${slide.color} flex items-center justify-center mb-6`}>
                        {slide.icon}
                    </div>

                    {/* Text */}
                    <h2 className="text-2xl font-bold text-center mb-3">
                        {slide.title}
                    </h2>
                    <p className="text-tg-hint text-center mb-8">
                        {slide.description}
                    </p>

                    {/* Dots */}
                    <div className="flex justify-center gap-2 mb-6">
                        {slides.map((_, index) => (
                            <button
                                key={index}
                                onClick={() => {
                                    setCurrentSlide(index);
                                    telegram.haptic('light');
                                }}
                                className={`w-2 h-2 rounded-full transition-all ${index === currentSlide
                                        ? 'w-6 bg-tg-button'
                                        : 'bg-tg-hint/30'
                                    }`}
                            />
                        ))}
                    </div>

                    {/* Buttons */}
                    <div className="flex gap-3">
                        {currentSlide > 0 && (
                            <Button
                                variant="secondary"
                                onClick={handlePrev}
                                className="flex-shrink-0"
                            >
                                <ChevronLeft className="w-5 h-5" />
                            </Button>
                        )}

                        <Button
                            onClick={handleNext}
                            className="flex-1"
                            size="lg"
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