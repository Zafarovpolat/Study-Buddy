// frontend/src/pages/MaterialPage.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { useEffect, useState } from 'react';
import { ArrowLeft, Trash2 } from 'lucide-react';
import { Spinner } from '../components/ui';
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

    const { removeMaterial } = useStore();

    useEffect(() => {
        loadMaterial();

        // Setup back button
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
            const [materialData, outputsData] = await Promise.all([
                api.getMaterial(materialId),
                api.getMaterialOutputs(materialId),
            ]);
            setMaterial(materialData);
            setOutputs(outputsData.outputs || []);
        } catch (error) {
            telegram.alert('Ошибка загрузки материала');
            window.location.hash = '#/';
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
        } catch (error) {
            telegram.alert('Ошибка удаления');
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Spinner size="lg" />
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
                    <button
                        onClick={() => (window.location.hash = '#/')}
                        className="p-2 -ml-2 text-tg-text"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>

                    <div className="flex-1 min-w-0">
                        <h1 className="font-semibold truncate">{material.title}</h1>
                        <p className="text-xs text-tg-hint">
                            {new Date(material.created_at).toLocaleDateString('ru-RU')}
                        </p>
                    </div>

                    <button
                        onClick={handleDelete}
                        className="p-2 text-red-500"
                    >
                        <Trash2 className="w-5 h-5" />
                    </button>
                </div>
            </header>

            {/* Content */}
            <main className="p-4">
                <OutputViewer
                    materialId={materialId}
                    outputs={outputs}
                    onRefresh={loadMaterial}
                />
            </main>
        </div>
    );
}