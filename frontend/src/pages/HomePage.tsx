// frontend/src/pages/HomePage.tsx
import { useEffect, useState, useCallback } from 'react';
import { Plus, Folder, RefreshCw, Camera, Type, Users, User, ArrowLeft, Sparkles, Search, X, Lightbulb, FileText, Presentation } from 'lucide-react';
import { Button, Card } from '../components/ui';
import { MaterialCard } from '../components/MaterialCard';
import { UploadModal } from '../components/UploadModal';
import { Header } from '../components/Header';
import { GroupsTab } from '../components/GroupsTab';
import { PresentationGenerator } from '../components/PresentationGenerator';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';
import { AskLibrary } from '../components/AskLibrary';


export function HomePage() {
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    const [uploadMode, setUploadMode] = useState<'file' | 'scan' | 'text' | 'topic'>('file');
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [uploadGroupId, setUploadGroupId] = useState<string | undefined>(undefined);
    const [showPresentationModal, setShowPresentationModal] = useState(false);

    // Поиск
    const [searchQuery, setSearchQuery] = useState('');
    const [_searchResults, setSearchResults] = useState<any[]>([]);
    const [showSearch, setShowSearch] = useState(false);

    const {
        user, setUser,
        setLimits,
        materials, setMaterials,
        folders, setFolders,
        groups, setGroups,
        currentFolderId, setCurrentFolderId,
        setSelectedMaterial,
        activeTab, setActiveTab,
        removeMaterial,
    } = useStore();

    // ===== Функция обновления данных =====
    const refreshData = useCallback(async () => {
        try {
            setIsRefreshing(true);

            if (activeTab === 'personal') {
                const [materialsData, foldersData] = await Promise.all([
                    api.getMaterials(currentFolderId || undefined),
                    api.getFolders(currentFolderId || undefined),
                ]);
                setMaterials(materialsData);
                setFolders(foldersData);
            } else {
                const groupsData = await api.getMyGroups();
                setGroups(groupsData);
            }

            // Обновляем лимиты
            const limitsData = await api.getMyLimits();
            setLimits(limitsData);
        } catch (error) {
            console.error('Refresh error:', error);
        } finally {
            setIsRefreshing(false);
        }
    }, [activeTab, currentFolderId, setMaterials, setFolders, setGroups, setLimits]);

    // ===== POLLING для обновления статусов материалов =====
    useEffect(() => {
        if (!Array.isArray(materials)) return;
        const processingMaterials = materials.filter(m => m.status === 'processing');

        if (processingMaterials.length === 0) return;

        const pollInterval = setInterval(async () => {
            try {
                const updatedMaterials = await api.getMaterials(currentFolderId || undefined);
                setMaterials(updatedMaterials);

                // Если все обработаны — останавливаем
                const stillProcessing = updatedMaterials.filter((m: any) => m.status === 'processing');
                if (stillProcessing.length === 0) {
                    clearInterval(pollInterval);
                    telegram.haptic('success');
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 3000);

        return () => clearInterval(pollInterval);
    }, [materials, currentFolderId, setMaterials]);

    // Загрузка групп при старте
    useEffect(() => {
        const loadGroups = async () => {
            try {
                const groupsData = await api.getMyGroups();
                setGroups(groupsData);
            } catch (error) {
                console.error('Failed to load groups:', error);
            }
        };
        loadGroups();
    }, [setGroups]);

    // Загрузка данных при смене вкладки/папки
    useEffect(() => {
        loadData();
    }, [currentFolderId, activeTab]);

    // Поиск с debounce
    useEffect(() => {
        if (!searchQuery.trim()) {
            setSearchResults([]);
            return;
        }

        const timer = setTimeout(async () => {
            if (searchQuery.trim().length < 2) return;

            try {
                const results = await api.searchMaterials(searchQuery.trim());
                setSearchResults(results);
            } catch (error) {
                console.error('Search error:', error);
                setSearchResults([]);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [searchQuery]);

    const loadData = async (showLoader = true) => {
        try {
            if (showLoader && !materials.length) setIsLoading(true);
            setIsRefreshing(true);

            const [userData, limitsData] = await Promise.all([
                !user ? api.getMe() : Promise.resolve(user),
                api.getMyLimits(),
            ]);

            if (!user) setUser(userData);
            setLimits(limitsData);

            if (activeTab === 'personal') {
                const [materialsData, foldersData] = await Promise.all([
                    api.getMaterials(currentFolderId || undefined),
                    api.getFolders(currentFolderId || undefined),
                ]);
                setMaterials(materialsData);
                setFolders(foldersData);
            } else {
                const groupsData = await api.getMyGroups();
                setGroups(groupsData);
            }
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setIsLoading(false);
            setIsRefreshing(false);
        }
    };

    const handleMaterialClick = async (material: any) => {
        try {
            const fullMaterial = await api.getMaterial(material.id);
            setSelectedMaterial(fullMaterial);
            window.location.hash = `#/material/${material.id}`;
        } catch (error) {
            telegram.alert('Ошибка загрузки материала');
        }
    };

    const handleMaterialUpdate = () => {
        loadData(false);
    };

    const handleMaterialDelete = (materialId: string) => {
        removeMaterial(materialId);
        telegram.haptic('success');
    };

    const openUpload = (mode: 'file' | 'scan' | 'text' | 'topic', groupId?: string) => {
        setUploadMode(mode);
        setUploadGroupId(groupId);
        setIsUploadOpen(true);
        telegram.haptic('medium');
    };

    const handleUploadClose = useCallback(async () => {
        setIsUploadOpen(false);
        setUploadGroupId(undefined);

        // Небольшая задержка чтобы сервер успел обработать
        await new Promise(resolve => setTimeout(resolve, 500));

        // Обновляем данные
        await refreshData();
    }, [refreshData]);

    const handleBackFromFolder = () => {
        setCurrentFolderId(null);
        telegram.haptic('selection');
    };

    const clearSearch = () => {
        setSearchQuery('');
        setSearchResults([]);
        setShowSearch(false);
        telegram.haptic('light');
    };

    const handleRefresh = () => {
        telegram.haptic('light');
        refreshData();
    };

    const openPresentationGenerator = () => {
        setShowPresentationModal(true);
        telegram.haptic('medium');
    };

    // ===== Skeleton для первой загрузки =====
    if (isLoading && !materials.length && !groups.length) {
        return (
            <div className="min-h-screen bg-lecto-bg-primary">
                <Header />
                <main className="p-4 space-y-4">
                    <div className="h-20 bg-lecto-bg-secondary rounded-xl animate-pulse" />
                    <div className="grid grid-cols-4 gap-2">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-20 bg-lecto-bg-secondary rounded-xl animate-pulse" />
                        ))}
                    </div>
                    <div className="space-y-2">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-20 bg-lecto-bg-secondary rounded-xl animate-pulse" />
                        ))}
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-lecto-bg-primary pb-24 text-lecto-text-primary">
            <Header />

            <main className="p-4 space-y-6">
                {/* Tabs */}
                <div className="flex bg-lecto-bg-secondary rounded-lg p-1">
                    <button
                        onClick={() => {
                            setActiveTab('personal');
                            setCurrentFolderId(null);
                            clearSearch();
                            telegram.haptic('selection');
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${activeTab === 'personal'
                            ? 'bg-lecto-bg-tertiary shadow text-lecto-text-primary'
                            : 'text-lecto-text-secondary'
                            }`}
                    >
                        <User className="w-4 h-4" />
                        Личное
                    </button>
                    <button
                        onClick={() => {
                            setActiveTab('groups');
                            clearSearch();
                            telegram.haptic('selection');
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${activeTab === 'groups'
                            ? 'bg-lecto-bg-tertiary shadow text-lecto-text-primary'
                            : 'text-lecto-text-secondary'
                            }`}
                    >
                        <Users className="w-4 h-4" />
                        Группы
                    </button>
                </div>

                {activeTab === 'personal' ? (
                    <>
                        {/* Кнопка назад */}
                        {currentFolderId && (
                            <button
                                onClick={handleBackFromFolder}
                                className="flex items-center gap-2 text-lecto-text-secondary hover:text-lecto-text-primary font-medium py-2"
                            >
                                <ArrowLeft className="w-5 h-5" />
                                <span>Назад</span>
                            </button>
                        )}

                        {/* Поиск */}
                        {!currentFolderId && (
                            <div className="relative">
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-lecto-text-secondary" />
                                    <input
                                        type="text"
                                        placeholder="Поиск материалов..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        onFocus={() => setShowSearch(true)}
                                        className="w-full pl-10 pr-10 py-3 bg-lecto-bg-secondary rounded-xl text-lecto-text-primary placeholder-lecto-text-secondary focus:outline-none focus:ring-1 focus:ring-lecto-accent-gold"
                                    />
                                    {searchQuery && (
                                        <button
                                            onClick={clearSearch}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-lecto-bg-tertiary rounded-full"
                                        >
                                            <X className="w-4 h-4 text-lecto-text-secondary" />
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Quick Actions */}
                        {!currentFolderId && !showSearch && (
                            <section>
                                <h2 className="text-sm font-medium text-lecto-text-secondary mb-3">Быстрые действия</h2>

                                <div className="grid grid-cols-4 gap-3">
                                    <button
                                        className="flex flex-col items-center gap-2 active:scale-95 transition-transform"
                                        onClick={() => openUpload('scan')}
                                    >
                                        <div className="w-14 h-14 rounded-2xl bg-lecto-bg-secondary flex items-center justify-center shadow-sm border border-lecto-border">
                                            <Camera className="w-6 h-6 text-lecto-accent-primary" />
                                        </div>
                                        <span className="text-xs font-medium text-lecto-text-secondary">Камера</span>
                                    </button>

                                    <button
                                        className="flex flex-col items-center gap-2 active:scale-95 transition-transform"
                                        onClick={() => openUpload('file')}
                                    >
                                        <div className="w-14 h-14 rounded-2xl bg-lecto-bg-secondary flex items-center justify-center shadow-sm border border-lecto-border">
                                            <FileText className="w-6 h-6 text-lecto-accent-primary" />
                                        </div>
                                        <span className="text-xs font-medium text-lecto-text-secondary">Документ</span>
                                    </button>

                                    <button
                                        className="flex flex-col items-center gap-2 active:scale-95 transition-transform"
                                        onClick={() => openUpload('text')}
                                    >
                                        <div className="w-14 h-14 rounded-2xl bg-lecto-bg-secondary flex items-center justify-center shadow-sm border border-lecto-border">
                                            <Type className="w-6 h-6 text-lecto-accent-primary" />
                                        </div>
                                        <span className="text-xs font-medium text-lecto-text-secondary">Заметка</span>
                                    </button>

                                    <button
                                        className="flex flex-col items-center gap-2 active:scale-95 transition-transform"
                                        onClick={() => openUpload('topic')}
                                    >
                                        <div className="w-14 h-14 rounded-2xl bg-lecto-bg-secondary flex items-center justify-center shadow-sm border border-lecto-border">
                                            <Lightbulb className="w-6 h-6 text-lecto-accent-primary" />
                                        </div>
                                        <span className="text-xs font-medium text-lecto-text-secondary">Идея</span>
                                    </button>
                                </div>
                            </section>
                        )}

                        {/* AI Presentations Banner */}
                        {!currentFolderId && !showSearch && (
                            <section>
                                <div
                                    onClick={openPresentationGenerator}
                                    className="relative w-full h-32 rounded-2xl overflow-hidden cursor-pointer active:scale-[0.98] transition-all shadow-lg"
                                >
                                    {/* Background with gradient */}
                                    <div className="absolute inset-0 bg-gradient-to-r from-[#9452ea] to-[#152886]" />

                                    {/* Decorative elements */}
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-2xl" />
                                    <div className="absolute bottom-0 left-10 w-20 h-20 bg-white/10 rounded-full translate-y-1/2 blur-xl" />

                                    {/* Content */}
                                    <div className="relative h-full flex items-center justify-between px-6">
                                        <div className="flex flex-col gap-1">
                                            <div className="flex items-center gap-2">
                                                <Sparkles className="w-5 h-5 text-yellow-300 animate-pulse" />
                                                <span className="text-white font-bold text-lg">AI Презентации</span>
                                            </div>
                                            <p className="text-white/80 text-sm max-w-[200px]">
                                                Создавайте слайды за секунды
                                            </p>
                                        </div>

                                        <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                                            <Presentation className="w-6 h-6 text-white" />
                                        </div>
                                    </div>
                                </div>
                            </section>
                        )}

                        {/* Папки */}
                        {Array.isArray(folders) && folders.length > 0 && !showSearch && (
                            <section>
                                <h2 className="text-sm font-medium text-lecto-text-secondary mb-2">Папки</h2>
                                <div className="grid grid-cols-2 gap-2">
                                    {folders.map((folder) => (
                                        <Card
                                            key={folder.id}
                                            className="flex items-center gap-2 cursor-pointer active:scale-[0.98] transition-transform bg-lecto-bg-secondary border-lecto-border"
                                            onClick={() => {
                                                telegram.haptic('selection');
                                                setCurrentFolderId(folder.id);
                                            }}
                                        >
                                            <Folder className="w-5 h-5 text-lecto-text-secondary" />
                                            <span className="truncate text-lecto-text-primary">{folder.name}</span>
                                        </Card>
                                    ))}
                                </div>
                            </section>
                        )}

                        {/* Материалы */}
                        {!showSearch && (
                            <section>
                                <div className="flex items-center justify-between mb-2">
                                    <h2 className="text-sm font-medium text-lecto-text-secondary">
                                        {currentFolderId ? 'Материалы в папке' : 'Лента материалов'}
                                    </h2>
                                    <button
                                        onClick={handleRefresh}
                                        className="p-1 text-lecto-text-secondary hover:text-lecto-text-primary transition-colors"
                                    >
                                        <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                                    </button>
                                </div>

                                {Array.isArray(materials) && materials.length > 0 ? (
                                    <div className="space-y-3">
                                        {materials.map((material) => (
                                            <MaterialCard
                                                key={material.id}
                                                material={material}
                                                onClick={() => handleMaterialClick(material)}
                                                onUpdate={handleMaterialUpdate}
                                                onDelete={() => handleMaterialDelete(material.id)}
                                                showActions={true}
                                            />
                                        ))}
                                    </div>
                                ) : (
                                    <Card className="text-center py-8 bg-lecto-bg-secondary border-lecto-border">
                                        <div className="w-12 h-12 bg-lecto-bg-tertiary rounded-full flex items-center justify-center mx-auto mb-3">
                                            <FileText className="w-6 h-6 text-lecto-text-secondary" />
                                        </div>
                                        <p className="text-lecto-text-secondary mb-4">
                                            {currentFolderId ? 'В папке нет материалов' : 'Нет материалов'}
                                        </p>
                                        <Button onClick={() => openUpload('file')}>
                                            <Plus className="w-4 h-4 mr-2" />
                                            Добавить
                                        </Button>
                                    </Card>
                                )}
                            </section>
                        )}
                    </>
                ) : (
                    <GroupsTab
                        groups={groups}
                        onRefresh={refreshData}
                        onUploadToGroup={(groupId) => {
                            setUploadGroupId(groupId);
                            setUploadMode('file');
                            setIsUploadOpen(true);
                        }}
                    />
                )}
            </main>

            {/* Overlay для закрытия поиска */}
            {showSearch && searchQuery && (
                <div className="fixed inset-0 z-40" onClick={clearSearch} />
            )}

            {/* Upload Modal */}
            <UploadModal
                isOpen={isUploadOpen}
                onClose={handleUploadClose}
                folderId={currentFolderId || undefined}
                groupId={uploadGroupId}
                initialMode={uploadMode}
            />

            {/* Presentation Generator Modal */}
            <PresentationGenerator
                isOpen={showPresentationModal}
                onClose={() => setShowPresentationModal(false)}
            />

            {/* Ask Library FAB */}
            <AskLibrary />
        </div>
    );
}