// frontend/src/pages/HomePage.tsx - ЗАМЕНИ начало файла (до return)
import { useEffect, useState } from 'react';
import { Plus, Folder, RefreshCw, Upload, Camera, Type } from 'lucide-react';
import { Button, Card, Spinner } from '../components/ui';
import { MaterialCard } from '../components/MaterialCard';
import { UploadModal } from '../components/UploadModal';
import { Header } from '../components/Header';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';

export function HomePage() {
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    const [uploadMode, setUploadMode] = useState<'file' | 'scan' | 'text'>('file');
    const [isLoading, setIsLoading] = useState(true);

    const {
        user,
        setUser,
        limits,
        setLimits,
        materials,
        setMaterials,
        folders,
        setFolders,
        currentFolderId,
        setSelectedMaterial,
    } = useStore();

    useEffect(() => {
        loadData();
    }, [currentFolderId]);

    const loadData = async () => {
        try {
            setIsLoading(true);

            const [userData, limitsData, materialsData, foldersData] = await Promise.all([
                !user ? api.getMe() : Promise.resolve(user),
                api.getMyLimits(),
                api.getMaterials(currentFolderId || undefined),
                api.getFolders(currentFolderId || undefined),
            ]);

            if (!user) setUser(userData);
            setLimits(limitsData);
            setMaterials(materialsData);
            setFolders(foldersData);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleMaterialClick = async (material: any) => {
        if (material.status === 'completed') {
            try {
                const fullMaterial = await api.getMaterial(material.id);
                setSelectedMaterial(fullMaterial);
                window.location.hash = `#/material/${material.id}`;
            } catch (error) {
                telegram.alert('Ошибка загрузки материала');
            }
        } else if (material.status === 'processing') {
            telegram.alert('Материал ещё обрабатывается...');
        } else if (material.status === 'failed') {
            telegram.alert('Ошибка обработки. Попробуйте снова.');
        }
    };

    const openUpload = (mode: 'file' | 'scan' | 'text') => {
        setUploadMode(mode);
        setIsUploadOpen(true);
        telegram.haptic('medium');
    };

    if (isLoading && !materials.length) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Spinner size="lg" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-tg-bg">
            <Header />

            <main className="p-4 pb-24 space-y-4">

                {/* Quick Actions - 3 кнопки */}
                <section>
                    <h2 className="text-sm font-medium text-tg-hint mb-2">Быстрые действия</h2>
                    <div className="grid grid-cols-3 gap-2">
                        <Card
                            className="cursor-pointer active:scale-95 transition-transform text-center py-4"
                            onClick={() => openUpload('scan')}
                        >
                            <Camera className="w-8 h-8 text-tg-button mx-auto mb-1" />
                            <span className="text-sm font-medium">Скан</span>
                        </Card>

                        <Card
                            className="cursor-pointer active:scale-95 transition-transform text-center py-4"
                            onClick={() => openUpload('file')}
                        >
                            <Upload className="w-8 h-8 text-tg-button mx-auto mb-1" />
                            <span className="text-sm font-medium">Файл</span>
                        </Card>

                        <Card
                            className="cursor-pointer active:scale-95 transition-transform text-center py-4"
                            onClick={() => openUpload('text')}
                        >
                            <Type className="w-8 h-8 text-tg-button mx-auto mb-1" />
                            <span className="text-sm font-medium">Текст</span>
                        </Card>
                    </div>
                </section>

                {/* Лимиты */}
                {limits && user?.subscription_tier === 'free' && (
                    <Card className="bg-gradient-to-r from-tg-button/10 to-tg-button/5">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-tg-hint">Осталось сегодня</p>
                                <p className="text-2xl font-bold">{limits.remaining_today}</p>
                            </div>
                            <Button variant="ghost" size="sm">
                                ⭐ Pro
                            </Button>
                        </div>
                    </Card>
                )}

                {/* Папки */}
                {folders.length > 0 && (
                    <section>
                        <h2 className="text-sm font-medium text-tg-hint mb-2">Папки</h2>
                        <div className="grid grid-cols-2 gap-2">
                            {folders.map((folder) => (
                                <Card
                                    key={folder.id}
                                    className="flex items-center gap-2 cursor-pointer active:scale-[0.98]"
                                    onClick={() => {
                                        telegram.haptic('selection');
                                        useStore.getState().setCurrentFolderId(folder.id);
                                    }}
                                >
                                    <Folder className="w-5 h-5 text-tg-button" />
                                    <span className="truncate">{folder.name}</span>
                                </Card>
                            ))}
                        </div>
                    </section>
                )}

                {/* Материалы */}
                <section>
                    <div className="flex items-center justify-between mb-2">
                        <h2 className="text-sm font-medium text-tg-hint">Материалы</h2>
                        <button onClick={loadData} className="p-1 text-tg-hint">
                            <RefreshCw className="w-4 h-4" />
                        </button>
                    </div>

                    {materials.length > 0 ? (
                        <div className="space-y-2">
                            {materials.map((material) => (
                                <MaterialCard
                                    key={material.id}
                                    material={material}
                                    onClick={() => handleMaterialClick(material)}
                                />
                            ))}
                        </div>
                    ) : (
                        <Card className="text-center py-8">
                            <p className="text-tg-hint mb-4">
                                Нет материалов
                            </p>
                            <Button onClick={() => openUpload('file')}>
                                <Plus className="w-4 h-4 mr-2" />
                                Добавить
                            </Button>
                        </Card>
                    )}
                </section>
            </main>

            {/* FAB */}
            <button
                onClick={() => openUpload('file')}
                className="fixed bottom-6 right-6 w-14 h-14 bg-tg-button text-tg-button-text rounded-full shadow-lg flex items-center justify-center active:scale-95 transition-transform"
            >
                <Plus className="w-6 h-6" />
            </button>

            {/* Upload Modal */}
            <UploadModal
                isOpen={isUploadOpen}
                onClose={() => setIsUploadOpen(false)}
                folderId={currentFolderId || undefined}
            />
        </div>
    );
}