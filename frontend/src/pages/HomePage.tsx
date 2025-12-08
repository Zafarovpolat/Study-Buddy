// frontend/src/pages/HomePage.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { useEffect, useState } from 'react';
import { Plus, Folder, RefreshCw, Upload, Camera, Type, Users, User, ArrowLeft } from 'lucide-react';
import { Button, Card, Spinner } from '../components/ui';
import { MaterialCard } from '../components/MaterialCard';
import { UploadModal } from '../components/UploadModal';
import { Header } from '../components/Header';
import { GroupsTab } from '../components/GroupsTab';
import { InviteBanner } from '../components/InviteBanner';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';

export function HomePage() {
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    const [, setUploadMode] = useState<'file' | 'scan' | 'text'>('file');
    const [isLoading, setIsLoading] = useState(true);
    const [uploadGroupId, setUploadGroupId] = useState<string | undefined>(undefined);

    const {
        user,
        setUser,
        limits,
        setLimits,
        materials,
        setMaterials,
        folders,
        setFolders,
        groups,
        setGroups,
        currentFolderId,
        setCurrentFolderId,
        setSelectedMaterial,
        activeTab,
        setActiveTab,
    } = useStore();

    useEffect(() => {
        loadData();
    }, [currentFolderId, activeTab]);

    const loadData = async () => {
        try {
            setIsLoading(true);

            const promises: Promise<any>[] = [
                !user ? api.getMe() : Promise.resolve(user),
                api.getMyLimits(),
            ];

            if (activeTab === 'personal') {
                promises.push(
                    api.getMaterials(currentFolderId || undefined),
                    api.getFolders(currentFolderId || undefined)
                );
            } else {
                promises.push(api.getMyGroups());
            }

            const results = await Promise.all(promises);

            if (!user) setUser(results[0]);
            setLimits(results[1]);

            if (activeTab === 'personal') {
                setMaterials(results[2]);
                setFolders(results[3]);
            } else {
                setGroups(results[2]);
            }
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

    const openUpload = (mode: 'file' | 'scan' | 'text', groupId?: string) => {
        setUploadMode(mode);
        setUploadGroupId(groupId);
        setIsUploadOpen(true);
        telegram.haptic('medium');
    };

    const handleGetPro = () => {
        telegram.haptic('medium');
        telegram.alert('Для оформления Pro подписки напишите боту команду /pro');
    };

    const handleBackFromFolder = () => {
        setCurrentFolderId(null);
        telegram.haptic('selection');
    };

    if (isLoading && !materials.length && !groups.length) {
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

                {/* Tabs */}
                <div className="flex bg-tg-secondary rounded-lg p-1">
                    <button
                        onClick={() => {
                            setActiveTab('personal');
                            setCurrentFolderId(null);
                            telegram.haptic('selection');
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${activeTab === 'personal'
                            ? 'bg-tg-bg shadow text-tg-text'
                            : 'text-tg-hint'
                            }`}
                    >
                        <User className="w-4 h-4" />
                        Личное
                    </button>
                    <button
                        onClick={() => {
                            setActiveTab('groups');
                            telegram.haptic('selection');
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${activeTab === 'groups'
                            ? 'bg-tg-bg shadow text-tg-text'
                            : 'text-tg-hint'
                            }`}
                    >
                        <Users className="w-4 h-4" />
                        Группы
                    </button>
                </div>

                {activeTab === 'personal' ? (
                    <>
                        {/* Кнопка назад из папки */}
                        {currentFolderId && (
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={handleBackFromFolder}
                                    className="flex items-center gap-2 text-tg-button font-medium py-2"
                                >
                                    <ArrowLeft className="w-5 h-5" />
                                    <span>Назад</span>
                                </button>
                            </div>
                        )}

                        {/* Invite Banner - только на главной, не в папках */}
                        {!currentFolderId && user?.subscription_tier === 'free' && (
                            <InviteBanner />
                        )}

                        {/* Quick Actions - только на главной */}
                        {!currentFolderId && (
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
                        )}

                        {/* Лимиты */}
                        {!currentFolderId && limits && user?.subscription_tier === 'free' && (
                            <Card className="bg-gradient-to-r from-tg-button/10 to-tg-button/5">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-tg-hint">Осталось сегодня</p>
                                        <p className="text-2xl font-bold">
                                            {limits.remaining_today}
                                            <span className="text-sm font-normal text-tg-hint">
                                                /{limits.daily_limit}
                                            </span>
                                        </p>
                                    </div>
                                    <Button variant="ghost" size="sm" onClick={handleGetPro}>
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
                                            className="flex items-center gap-2 cursor-pointer active:scale-[0.98] transition-transform"
                                            onClick={() => {
                                                telegram.haptic('selection');
                                                setCurrentFolderId(folder.id);
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
                                <h2 className="text-sm font-medium text-tg-hint">
                                    {currentFolderId ? 'Материалы в папке' : 'Материалы'}
                                </h2>
                                <button
                                    onClick={loadData}
                                    className="p-1 text-tg-hint hover:text-tg-text transition-colors"
                                >
                                    <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
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
                                        {currentFolderId ? 'В папке нет материалов' : 'Нет материалов'}
                                    </p>
                                    <Button onClick={() => openUpload('file')}>
                                        <Plus className="w-4 h-4 mr-2" />
                                        Добавить
                                    </Button>
                                </Card>
                            )}
                        </section>
                    </>
                ) : (
                    /* Groups Tab */
                    <GroupsTab
                        groups={groups}
                        onRefresh={loadData}
                        onUploadToGroup={(groupId) => {
                            setUploadGroupId(groupId);
                            setIsUploadOpen(true);
                        }}
                    />
                )}
            </main>

            {/* FAB - только для личных материалов */}
            {activeTab === 'personal' && (
                <button
                    onClick={() => openUpload('file')}
                    className="fixed bottom-6 right-6 w-14 h-14 bg-tg-button text-tg-button-text rounded-full shadow-lg flex items-center justify-center active:scale-95 transition-transform z-40"
                >
                    <Plus className="w-6 h-6" />
                </button>
            )}

            {/* Upload Modal */}
            <UploadModal
                isOpen={isUploadOpen}
                onClose={() => {
                    setIsUploadOpen(false);
                    setUploadGroupId(undefined);
                }}
                folderId={currentFolderId || undefined}
                groupId={uploadGroupId}
            />
        </div>
    );
}