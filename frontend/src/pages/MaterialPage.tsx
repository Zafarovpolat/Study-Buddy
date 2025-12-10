// frontend/src/pages/MaterialPage.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { useEffect, useState } from 'react';
import { ArrowLeft, Trash2, RefreshCw } from 'lucide-react';
import { Spinner, Button, Card } from '../components/ui';
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
    const groupId = material?.group_id;  // ✅ Только если это группа

    const { removeMaterial, user } = useStore();

    useEffect(() => {
        loadMaterial();

        telegram.showBackButton(() => {
            window.location.hash = '#/';
        });

        return () => {
            telegram.hideBackButton();
        };
    }, [materialId]);

    const loadMaterial = async () => {
        try {
            setIsLoading(true);
            setError(null);

            // Загружаем материал (включает outputs)
            const materialData = await api.getMaterial(materialId);
            setMaterial(materialData);

            // Outputs из материала или загружаем отдельно
            if (materialData.outputs && Array.isArray(materialData.outputs)) {
                setOutputs(materialData.outputs);
            } else {
                try {
                    const outputsData = await api.getMaterialOutputs(materialId);
                    setOutputs(outputsData.outputs || []);
                } catch (e) {
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

    // Проверяем, является ли текущий пользователь владельцем
    const isOwner = material && user && material.user_id === user.id;

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-tg-bg">
                <Spinner size="lg" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-tg-bg">
                <header className="sticky top-0 z-10 bg-tg-bg/80 backdrop-blur-lg border-b border-tg-hint/10">
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
        <div className="min-h-screen bg-tg-bg">
            {/* Header */}
            <header className="sticky top-0 z-10 bg-tg-bg/80 backdrop-blur-lg border-b border-tg-hint/10">
                <div className="px-4 py-3 flex items-center gap-3">
                    <button onClick={handleBack} className="p-2 -ml-2 text-tg-text">
                        <ArrowLeft className="w-5 h-5" />
                    </button>

                    <div className="flex-1 min-w-0">
                        <h1 className="font-semibold truncate">{material.title}</h1>
                        <p className="text-xs text-tg-hint">
                            {new Date(material.created_at).toLocaleDateString('ru-RU')}
                            {material.status === 'processing' && ' • ⏳ Обработка...'}
                            {material.status === 'failed' && ' • ❌ Ошибка'}
                        </p>
                    </div>

                    {/* Удалить может только владелец */}
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
                    <Card className="text-center py-12">
                        <Spinner size="lg" />
                        <p className="mt-4 text-tg-hint">Обработка материала...</p>
                        <p className="text-xs text-tg-hint mt-2">Это может занять минуту</p>
                        <Button variant="secondary" className="mt-4" onClick={loadMaterial}>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Проверить статус
                        </Button>
                    </Card>
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
                        groupId={groupId}  // ДОБАВЬ ЭТО
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