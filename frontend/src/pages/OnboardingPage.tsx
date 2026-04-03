import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scale, TrendingUp, Globe, Monitor, Stethoscope, GraduationCap } from 'lucide-react';
import { telegram } from '../lib/telegram';

const STEPS = [
    {
        title: "Lecto — ваш личный академический ассистент",
        image: "https://cdn-icons-png.flaticon.com/512/3135/3135715.png", // Placeholder or use local asset
    },
    {
        title: "Анализируйте лекции и документы за секунды",
        image: "https://cdn-icons-png.flaticon.com/512/3135/3135768.png",
    },
    {
        title: "Создавайте тесты и дебатируйте с AI",
        image: "https://cdn-icons-png.flaticon.com/512/3135/3135823.png",
    },
    {
        title: "Готовы начать путь к отличным оценкам?",
        image: "https://cdn-icons-png.flaticon.com/512/3135/3135789.png",
    }
];

const FIELDS_OF_STUDY = [
    { id: 'law', label: 'Юриспруденция', Icon: Scale },
    { id: 'economics', label: 'Экономика', Icon: TrendingUp },
    { id: 'ir', label: 'Международные отношения', Icon: Globe },
    { id: 'it', label: 'IT и Инженерия', Icon: Monitor },
    { id: 'medicine', label: 'Медицина', Icon: Stethoscope },
    { id: 'other', label: 'Другое', Icon: GraduationCap },
];

export const OnboardingPage = () => {
    const [currentStep, setCurrentStep] = useState(0);
    const [fieldOfStudy, setFieldOfStudy] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleNext = () => {
        if (currentStep < STEPS.length - 1) {
            setCurrentStep(prev => prev + 1);
            // Haptic feedback
            telegram.haptic('light');
        } else {
            handleFinish();
        }
    };

    const handleBack = () => {
        if (currentStep > 0) {
            setCurrentStep(prev => prev - 1);
        }
    };

    const handleFinish = async () => {
        if (!fieldOfStudy) return;

        setIsLoading(true);
        try {
            // Save to backend
            // TODO: Replace with actual API call
            // await api.post('/users/profile', { field_of_study: fieldOfStudy });

            // Save to local storage to skip onboarding next time
            localStorage.setItem('lecto_onboarding_completed', 'true');

            // Redirect to dashboard
            window.location.hash = '#/';
        } catch (error: unknown) {
            console.error('Failed to save profile', error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-lecto-bg-primary text-lecto-text-primary flex flex-col p-6 relative overflow-hidden">
            {/* Background Elements */}
            <div className="absolute top-[-20%] left-[-20%] w-[80%] h-[50%] bg-lecto-accent-gold opacity-10 blur-[100px] rounded-full" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[40%] bg-purple-500 opacity-10 blur-[100px] rounded-full" />

            {/* Stepper */}
            <div className="flex gap-2 mb-8 z-10">
                {STEPS.map((_, index) => (
                    <div
                        key={index}
                        className="h-1 flex-1 rounded-full bg-lecto-bg-tertiary overflow-hidden"
                    >
                        <motion.div
                            className="h-full bg-lecto-accent-gold"
                            initial={{ width: "0%" }}
                            animate={{ width: index <= currentStep ? "100%" : "0%" }}
                            transition={{ duration: 0.3 }}
                        />
                    </div>
                ))}
            </div>

            {/* Content */}
            <div className="flex-1 flex flex-col items-center justify-center z-10">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentStep}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.3 }}
                        className="flex flex-col items-center text-center w-full"
                    >
                        {/* Image Placeholder */}
                        <div className="w-64 h-64 mb-8 relative">
                            <div className="absolute inset-0 bg-gradient-to-tr from-lecto-accent-gold to-orange-500 opacity-20 blur-xl rounded-full animate-pulse" />
                            <img
                                src={STEPS[currentStep].image}
                                alt="Illustration"
                                className="w-full h-full object-contain relative z-10 drop-shadow-2xl"
                            />
                        </div>

                        <h1 className="text-2xl font-semibold tracking-tight-header mb-4">
                            {STEPS[currentStep].title}
                        </h1>

                        {currentStep === 3 && (
                            <div className="w-full mt-4 grid grid-cols-2 gap-3">
                                {FIELDS_OF_STUDY.map((field) => (
                                    <button
                                        key={field.id}
                                        onClick={() => setFieldOfStudy(field.id)}
                                        className={`
                      p-4 rounded-lecto-card border transition-all duration-200 flex flex-col items-center gap-2
                      ${fieldOfStudy === field.id
                                                ? 'bg-lecto-bg-secondary border-lecto-accent-gold shadow-lecto-glow-gold'
                                                : 'bg-lecto-bg-secondary border-lecto-border hover:border-gray-600'}
                    `}
                                    >
                                        <field.Icon className="w-6 h-6" />
                                        <span className="text-sm font-medium">{field.label}</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>

            {/* Actions */}
            <div className="mt-8 z-10 flex flex-col gap-3">
                <button
                    onClick={handleNext}
                    disabled={currentStep === 3 && !fieldOfStudy}
                    className={`
            w-full py-4 rounded-lecto-btn font-semibold shadow-lg transition-all
            ${currentStep === 3 && !fieldOfStudy
                            ? 'bg-lecto-bg-tertiary text-gray-500 cursor-not-allowed'
                            : 'bg-lecto-gradient-gold text-white hover:shadow-lecto-glow-gold active:scale-95'}
          `}
                >
                    {currentStep === 3 ? (isLoading ? 'Загрузка...' : 'Приступить') : 'Далее'}
                </button>

                {currentStep > 0 && (
                    <button
                        onClick={handleBack}
                        className="w-full py-3 text-lecto-text-secondary font-medium active:opacity-70"
                    >
                        Назад
                    </button>
                )}
            </div>
        </div>
    );
};
