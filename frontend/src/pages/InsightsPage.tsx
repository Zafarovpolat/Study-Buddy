// frontend/src/pages/InsightsPage.tsx
import { useState, useEffect } from 'react';
import { ArrowLeft, Globe, MapPin, Sparkles, BookOpen, Settings, X, Check } from 'lucide-react';
import { telegram } from '../lib/telegram';
import { Card, Spinner, Button } from '../components/ui';
import { useStore } from '../store/useStore';
import { api } from '../lib/api';

interface Insight {
    id: string;
    title: string;
    summary: string;
    importance: number;
    importance_reason: string;
    academic_link: string;
    published_at: string;
    source_name: string;
    region: 'uz' | 'global';
}

export function InsightsPage() {
    const [insights, setInsights] = useState<Insight[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [region, setRegion] = useState<'uz' | 'global'>('global');
    const [showSetup, setShowSetup] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    // Setup Modal State
    const { user, setUser } = useStore();
    const [selectedField, setSelectedField] = useState(user?.field_of_study || 'Law');
    const [selectedRegion, setSelectedRegion] = useState(user?.region || 'uz');
    const [isSavingSetup, setIsSavingSetup] = useState(false);

    useEffect(() => {
        loadInsights();
    }, [region]);

    const loadInsights = async () => {
        setIsLoading(true);
        try {
            // Mock data for now if API is not ready
            // const data = await api.getInsights(region);
            const data = [
                {
                    id: '1',
                    title: 'Изменения в Налоговом кодексе РУз 2025',
                    summary: 'Введены новые льготы для IT-сектора и изменены ставки НДС для импортеров.',
                    importance: 9,
                    importance_reason: 'Критично для понимания фискальной политики.',
                    academic_link: 'Налоговое право, Глава 4',
                    published_at: new Date().toISOString(),
                    source_name: 'Gazeta.uz',
                    region: 'uz'
                },
                {
                    id: '2',
                    title: 'Global Inflation Trends 2025',
                    summary: 'Analysis of how energy prices are affecting global inflation rates.',
                    importance: 8,
                    importance_reason: 'Relevant for Macroeconomics exam.',
                    academic_link: 'Macroeconomics, Chapter 12',
                    published_at: new Date().toISOString(),
                    source_name: 'Bloomberg',
                    region: 'global'
                }
            ].filter(i => i.region === region) as Insight[];

            setInsights(data);
        } catch (error) {
            console.error('Failed to load insights', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleBack = () => {
        window.location.hash = '#/';
        telegram.haptic('selection');
    };

    const handleGenerateDetail = async (_insight: Insight) => {
        setIsGenerating(true);
        telegram.haptic('medium');
        try {
            // await api.generateInsightDetail(insight.id);
            await new Promise(resolve => setTimeout(resolve, 2000)); // Mock
            telegram.alert('Конспект сгенерирован и добавлен в библиотеку!');
        } catch (error) {
            telegram.alert('Ошибка генерации');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSaveSetup = async () => {
        setIsSavingSetup(true);
        try {
            await api.updatePreferences({
                field_of_study: selectedField,
                region: selectedRegion
            });

            // Update local user
            if (user) {
                setUser({
                    ...user,
                    field_of_study: selectedField,
                    region: selectedRegion
                });
            }

            setShowSetup(false);
            telegram.haptic('success');
            loadInsights(); // Reload with new settings
        } catch (error) {
            telegram.alert('Ошибка сохранения настроек');
        } finally {
            setIsSavingSetup(false);
        }
    };

    return (
        <div className="min-h-screen bg-lecto-bg-primary text-lecto-text-primary pb-24">
            {/* Header */}
            <header className="sticky top-0 z-20 bg-lecto-bg-primary/80 backdrop-blur-md border-b border-lecto-border px-4 py-3 flex items-center justify-between">
                <button onClick={handleBack} className="p-2 -ml-2 text-lecto-text-secondary">
                    <ArrowLeft className="w-6 h-6" />
                </button>
                <h1 className="font-semibold text-lg">Академические Инсайты</h1>
                <button onClick={() => setShowSetup(true)} className="p-2 -mr-2 text-lecto-text-secondary">
                    <Settings className="w-6 h-6" />
                </button>
            </header>

            <main className="p-4 space-y-6">
                {/* Region Switch */}
                <div className="flex bg-lecto-bg-secondary rounded-lg p-1">
                    <button
                        onClick={() => setRegion('global')}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${region === 'global' ? 'bg-lecto-bg-tertiary shadow text-lecto-text-primary' : 'text-lecto-text-secondary'
                            }`}
                    >
                        <Globe className="w-4 h-4" />
                        Global
                    </button>
                    <button
                        onClick={() => setRegion('uz')}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${region === 'uz' ? 'bg-lecto-bg-tertiary shadow text-lecto-text-primary' : 'text-lecto-text-secondary'
                            }`}
                    >
                        <MapPin className="w-4 h-4" />
                        Uzbekistan
                    </button>
                </div>

                {/* Feed */}
                {isLoading ? (
                    <div className="flex justify-center py-12">
                        <Spinner />
                    </div>
                ) : (
                    <div className="space-y-4">
                        {insights.map((insight) => (
                            <Card key={insight.id} className="p-5 border-lecto-border bg-lecto-bg-secondary">
                                <div className="flex justify-between items-start mb-3">
                                    <span className="text-xs font-medium text-lecto-text-secondary bg-lecto-bg-tertiary px-2 py-1 rounded">
                                        {insight.source_name}
                                    </span>
                                    {insight.importance >= 8 && (
                                        <span className="text-xs font-bold text-red-400 flex items-center gap-1">
                                            🔥 High Priority
                                        </span>
                                    )}
                                </div>

                                <h3 className="text-lg font-semibold mb-2 leading-tight">
                                    {insight.title}
                                </h3>

                                <p className="text-lecto-text-secondary text-sm mb-4 line-clamp-3">
                                    {insight.summary}
                                </p>

                                <div className="bg-lecto-bg-tertiary/50 rounded-lg p-3 mb-4 border border-lecto-border/50">
                                    <div className="flex items-center gap-2 text-xs text-lecto-accent-gold font-medium mb-1">
                                        <BookOpen className="w-3 h-3" />
                                        Связь с теорией
                                    </div>
                                    <p className="text-xs text-lecto-text-primary">
                                        {insight.academic_link}
                                    </p>
                                </div>

                                <Button
                                    className="w-full bg-lecto-bg-tertiary hover:bg-lecto-border text-lecto-text-primary border border-lecto-border"
                                    onClick={() => handleGenerateDetail(insight)}
                                    disabled={isGenerating}
                                >
                                    {isGenerating ? (
                                        <Spinner size="sm" className="mr-2" />
                                    ) : (
                                        <Sparkles className="w-4 h-4 mr-2 text-lecto-accent-gold" />
                                    )}
                                    Изучить детально
                                </Button>
                            </Card>
                        ))}
                    </div>
                )}
            </main>

            {/* Setup Modal */}
            {showSetup && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <Card className="w-full max-w-sm bg-lecto-bg-secondary border-lecto-border p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold">Настройки ленты</h2>
                            <button onClick={() => setShowSetup(false)} className="p-1 text-lecto-text-secondary">
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="space-y-4 mb-6">
                            <div>
                                <label className="block text-sm font-medium text-lecto-text-secondary mb-2">
                                    Направление обучения
                                </label>
                                <select
                                    value={selectedField}
                                    onChange={(e) => setSelectedField(e.target.value)}
                                    className="w-full bg-lecto-bg-tertiary border border-lecto-border rounded-xl px-4 py-3 text-lecto-text-primary focus:outline-none focus:ring-2 focus:ring-lecto-accent-gold"
                                >
                                    <option value="Law">Юриспруденция</option>
                                    <option value="Economics">Экономика</option>
                                    <option value="IR">Международные отношения</option>
                                    <option value="IT">IT и Программирование</option>
                                    <option value="Medicine">Медицина</option>
                                    <option value="Other">Другое</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-lecto-text-secondary mb-2">
                                    Регион новостей
                                </label>
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        onClick={() => setSelectedRegion('uz')}
                                        className={`py-3 rounded-xl border transition-all ${selectedRegion === 'uz'
                                            ? 'bg-lecto-bg-tertiary border-lecto-accent-gold text-lecto-text-primary'
                                            : 'bg-lecto-bg-tertiary border-transparent text-lecto-text-secondary opacity-60'
                                            }`}
                                    >
                                        🇺🇿 Узбекистан
                                    </button>
                                    <button
                                        onClick={() => setSelectedRegion('global')}
                                        className={`py-3 rounded-xl border transition-all ${selectedRegion === 'global'
                                            ? 'bg-lecto-bg-tertiary border-lecto-accent-gold text-lecto-text-primary'
                                            : 'bg-lecto-bg-tertiary border-transparent text-lecto-text-secondary opacity-60'
                                            }`}
                                    >
                                        🌍 Global
                                    </button>
                                </div>
                            </div>
                        </div>

                        <Button
                            className="w-full py-3 text-base font-medium"
                            onClick={handleSaveSetup}
                            disabled={isSavingSetup}
                        >
                            {isSavingSetup ? <Spinner size="sm" /> : <Check className="w-5 h-5 mr-2" />}
                            Сохранить
                        </Button>
                    </Card>
                </div>
            )}
        </div>
    );
}
