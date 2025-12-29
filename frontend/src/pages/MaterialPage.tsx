// frontend/src/pages/MaterialPage.tsx
import { useEffect, useState, useRef } from 'react';
import { ArrowLeft, Trash2, RefreshCw, Loader2 } from 'lucide-react';
import { Button, Card } from '../components/ui';
import { OutputViewer } from '../components/OutputViewer';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';

interface MaterialPageProps {
    materialId: string;
}

export function MaterialPage({ materialId }: MaterialPageProps) {
    const [material, setMaterial] = useState<any>(null);
    const [outputs, setOutputs] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const groupId = material?.group_id;

    const { removeMaterial, user } = useStore();

    useEffect(() => {
        loadMaterial();

        telegram.showBackButton(() => {
            window.location.hash = '#/';
        });

        return () => {
            telegram.hideBackButton();
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
        };
    }, [materialId]);

    // ===== POLLING для processing материалов =====
    useEffect(() => {
        if (material?.status === 'processing' && !pollIntervalRef.current) {
            pollIntervalRef.current = setInterval(async () => {
                try {
                    const updatedMaterial = await api.getMaterial(materialId);
                    setMaterial(updatedMaterial);

                    if (updatedMaterial.outputs?.length > 0) {
                        setOutputs(updatedMaterial.outputs);
                    }

                    if (updatedMaterial.status !== 'processing') {
                        if (pollIntervalRef.current) {
                            clearInterval(pollIntervalRef.current);
                            pollIntervalRef.current = null;
                        }
                        telegram.haptic('success');
                    }
                } catch (err) {
                    console.error('Polling error:', err);
                }
            }, 3000);
        }

        return () => {
            if (pollIntervalRef.current && material?.status !== 'processing') {
                clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = null;
            }
        };
    }, [material?.status, materialId]);

    const loadMaterial = async () => {
        try {
            setIsLoading(true);
            setError(null);

            const materialData = await api.getMaterial(materialId);
            setMaterial(materialData);

            if (materialData.outputs && Array.isArray(materialData.outputs)) {
                setOutputs(materialData.outputs);
            } else {
                try {
                    const outputsData = await api.getMaterialOutputs(materialId);
                    setOutputs(outputsData.outputs || []);
                } catch {
                    console.log('Could not load outputs separately');
                    setOutputs([]);
                }
            }
        } catch (error: any) {
            console.error('Error loading material:', error);
            const detail = error.response?.data?.detail;
            setError(detail || 'Ошибка загрузки материала');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async () => {
        const confirmed = await telegram.confirm('Удалить материал?');
        if (!confirmed) return;

        try {
            await api.deleteMaterial(materialId);
            removeMaterial(materialId);
            telegram.haptic('success');
            window.location.hash = '#/';
        } catch (error: any) {
            telegram.alert(error.response?.data?.detail || 'Ошибка удаления');
        }
    };

    const handleBack = () => {
        window.location.hash = '#/';
    };

    const isOwner = material && user && material.user_id === user.id;

    // ===== Skeleton для первой загрузки =====
    if (isLoading) {
        return (
            <div className="min-h-screen bg-lecto-bg">
                <header className="sticky top-0 z-10 bg-lecto-bg/80 backdrop-blur-lg border-b border-tg-hint/10">
                    <div className="px-4 py-3 flex items-center gap-3">
                        <button onClick={handleBack} className="p-2 -ml-2 text-tg-text">
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div className="flex-1">
                            <div className="h-5 w-48 bg-lecto-secondary rounded animate-pulse" />
                            <div className="h-3 w-24 bg-lecto-secondary rounded animate-pulse mt-1" />
                        </div>
                    </div>
                </header>
                <main className="p-4 space-y-4">
                    <div className="flex gap-2 overflow-x-auto pb-2">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="h-10 w-24 bg-lecto-secondary rounded-lg animate-pulse flex-shrink-0" />
                        ))}
                    </div>
                    <div className="space-y-3">
                        <div className="h-4 bg-lecto-secondary rounded animate-pulse" />
                        <div className="h-4 bg-lecto-secondary rounded animate-pulse w-5/6" />
                        <div className="h-4 bg-lecto-secondary rounded animate-pulse w-4/6" />
                        <div className="h-20 bg-lecto-secondary rounded animate-pulse mt-4" />
                        <div className="h-4 bg-lecto-secondary rounded animate-pulse w-3/4" />
                    </div>
                </main>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-lecto-bg">
                <header className="sticky top-0 z-10 bg-lecto-bg/80 backdrop-blur-lg border-b border-tg-hint/10">
                    <div className="px-4 py-3 flex items-center gap-3">
                        <button onClick={handleBack} className="p-2 -ml-2 text-tg-text">
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <h1 className="font-semibold">Ошибка</h1>
                    </div>
                </header>
                <main className="p-4">
                    <Card className="text-center py-8">
                        <p className="text-red-500 mb-4">{error}</p>
                        <div className="flex gap-2 justify-center">
                            <Button variant="secondary" onClick={handleBack}>
                                Назад
                            </Button>
                            <Button onClick={loadMaterial}>
                                <RefreshCw className="w-4 h-4 mr-2" />
                                Повторить
                            </Button>
                        </div>
                    </Card>
                </main>
            </div>
        );
    }

    if (!material) {
        return null;
    }

    return (
        <div className="min-h-screen bg-lecto-bg">
            {/* Header */}
            <header className="sticky top-0 z-10 bg-lecto-bg/80 backdrop-blur-lg border-b border-tg-hint/10">
                <div className="px-4 py-3 flex items-center gap-3">
                    <button onClick={handleBack} className="p-2 -ml-2 text-tg-text">
                        <ArrowLeft className="w-5 h-5" />
                    </button>

                    <div className="flex-1 min-w-0">
                        <h1 className="font-semibold truncate">{material.title}</h1>
                        <div className="flex items-center gap-2 text-xs text-tg-hint">
                            <span>{new Date(material.created_at).toLocaleDateString('ru-RU')}</span>
                            {material.status === 'processing' && (
                                <span className="flex items-center gap-1 text-yellow-500">
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                    Обработка...
                                </span>
                            )}
                            {material.status === 'failed' && (
                                <span className="text-red-500">❌ Ошибка</span>
                            )}
                        </div>
                    </div>

                    {isOwner && (
                        <button onClick={handleDelete} className="p-2 text-red-500">
                            <Trash2 className="w-5 h-5" />
                        </button>
                    )}
                </div>
            </header>

            {/* Content */}
            <main className="p-4">
                {material.status === 'processing' ? (
                    <div className="space-y-4">
                        {/* Прогресс-бар */}
                        <Card className="overflow-hidden">
                            <div className="p-4">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center">
                                        <Loader2 className="w-5 h-5 text-yellow-500 animate-spin" />
                                    </div>
                                    <div>
                                        <p className="font-medium">AI обрабатывает материал</p>
                                        <p className="text-sm text-tg-hint">Обычно занимает 30-60 секунд</p>
                                    </div>
                                </div>

                                <div className="h-2 bg-lecto-secondary rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-yellow-400 to-yellow-500 rounded-full animate-pulse"
                                        style={{ width: '60%' }}
                                    />
                                </div>

                                <p className="text-xs text-tg-hint mt-3 text-center">
                                    Страница обновится автоматически
                                </p>
                            </div>
                        </Card>

                        {/* Skeleton для будущего контента */}
                        <div className="space-y-3 opacity-50">
                            <div className="flex gap-2">
                                {['Конспект', 'TL;DR', 'Тест', 'Глоссарий', 'Карточки'].map((tab, i) => (
                                    <div key={i} className="px-4 py-2 bg-lecto-secondary rounded-lg text-sm text-tg-hint">
                                        {tab}
                                    </div>
                                ))}
                            </div>
                            <div className="space-y-2">
                                <div className="h-4 bg-lecto-secondary rounded w-full" />
                                <div className="h-4 bg-lecto-secondary rounded w-5/6" />
                                <div className="h-4 bg-lecto-secondary rounded w-4/6" />
                            </div>
                        </div>
                    </div>
                ) : material.status === 'failed' ? (
                    <Card className="text-center py-12">
                        <p className="text-4xl mb-2">😕</p>
                        <p className="text-red-500 font-medium">Ошибка обработки</p>
                        <p className="text-sm text-tg-hint mt-2">
                            Попробуйте загрузить файл заново
                        </p>
                        <Button className="mt-4" onClick={handleBack}>
                            Назад
                        </Button>
                    </Card>
                ) : outputs.length > 0 ? (
                    <OutputViewer
                        materialId={materialId}
                        outputs={outputs}
                        onRefresh={loadMaterial}
                        groupId={groupId}
                        materialTitle={material.title}
                        materialContent={material.raw_content}
                    />
                ) : (
                    <Card className="text-center py-12">
                        <p className="text-tg-hint mb-4">Контент ещё не сгенерирован</p>
                        <Button onClick={loadMaterial}>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Обновить
                        </Button>
                    </Card>
                )}
            </main>
        </div>
    );
}