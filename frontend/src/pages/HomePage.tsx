// frontend/src/pages/HomePage.tsx
import { useEffect, useState } from 'react';
import { Plus, Folder, RefreshCw, Upload, Camera, Type, Users, User, ArrowLeft, Sparkles, Search, X, Presentation } from 'lucide-react';
import { Button, Card, Spinner } from '../components/ui';
import { MaterialCard } from '../components/MaterialCard';
import { UploadModal } from '../components/UploadModal';
import { Header } from '../components/Header';
import { GroupsTab } from '../components/GroupsTab';
import { InviteBanner } from '../components/InviteBanner';
import { PresentationGenerator } from '../components/PresentationGenerator';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';
import { OnboardingModal } from '../components/OnboardingModal';
import { AskLibrary } from '../components/AskLibrary';


export function HomePage() {
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    const [uploadMode, setUploadMode] = useState<'file' | 'scan' | 'text' | 'topic'>('file');
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [uploadGroupId, setUploadGroupId] = useState<string | undefined>(undefined);
    const [showOnboarding, setShowOnboarding] = useState(() => {
        return !localStorage.getItem('lecto_onboarding_completed');
    });
    const [showPresentationModal, setShowPresentationModal] = useState(false);

    // Поиск
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [showSearch, setShowSearch] = useState(false);

    const {
        user, setUser,
        limits, setLimits,
        materials, setMaterials,
        folders, setFolders,
        groups, setGroups,
        currentFolderId, setCurrentFolderId,
        setSelectedMaterial,
        activeTab, setActiveTab,
        removeMaterial,
    } = useStore();

    // ===== POLLING для обновления статусов материалов =====
    useEffect(() => {
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
    }, [materials, currentFolderId]);

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
    }, []);

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

            setIsSearching(true);
            try {
                const results = await api.searchMaterials(searchQuery.trim());
                setSearchResults(results);
            } catch (error) {
                console.error('Search error:', error);
                setSearchResults([]);
            } finally {
                setIsSearching(false);
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

    const handleGetPro = () => {
        telegram.haptic('medium');
        telegram.alert('Для оформления Pro подписки напишите боту команду /pro');
    };

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
        loadData(false);
    };

    const openPresentationGenerator = () => {
        setShowPresentationModal(true);
        telegram.haptic('medium');
    };

    // ===== Skeleton для первой загрузки =====
    if (isLoading && !materials.length && !groups.length) {
        return (
            <div className="min-h-screen bg-tg-bg">
                <Header />
                <main className="p-4 space-y-4">
                    <div className="h-10 bg-tg-secondary rounded-lg animate-pulse" />
                    <div className="grid grid-cols-4 gap-2">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-20 bg-tg-secondary rounded-xl animate-pulse" />
                        ))}
                    </div>
                    <div className="space-y-2">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-20 bg-tg-secondary rounded-xl animate-pulse" />
                        ))}
                    </div>
                </main>
            </div>
        );
    }

    const isPro = user?.subscription_tier === 'pro';

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
                            clearSearch();
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
                            clearSearch();
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
                        {/* Кнопка назад */}
                        {currentFolderId && (
                            <button
                                onClick={handleBackFromFolder}
                                className="flex items-center gap-2 text-tg-button font-medium py-2"
                            >
                                <ArrowLeft className="w-5 h-5" />
                                <span>Назад</span>
                            </button>
                        )}

                        {/* Поиск */}
                        {!currentFolderId && (
                            <div className="relative">
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-tg-hint" />
                                    <input
                                        type="text"
                                        placeholder="Поиск материалов..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        onFocus={() => setShowSearch(true)}
                                        className="w-full pl-10 pr-10 py-3 bg-tg-secondary rounded-xl text-tg-text placeholder-tg-hint focus:outline-none focus:ring-2 focus:ring-tg-button"
                                    />
                                    {searchQuery && (
                                        <button
                                            onClick={clearSearch}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-tg-hint/20 rounded-full"
                                        >
                                            <X className="w-4 h-4 text-tg-hint" />
                                        </button>
                                    )}
                                </div>

                                {/* Результаты поиска */}
                                {showSearch && searchQuery.trim().length >= 2 && (
                                    <div className="absolute top-full left-0 right-0 mt-2 bg-tg-bg border border-tg-secondary rounded-xl shadow-lg z-50 max-h-80 overflow-y-auto">
                                        {isSearching ? (
                                            <div className="flex items-center justify-center py-8">
                                                <Spinner size="sm" />
                                            </div>
                                        ) : searchResults.length > 0 ? (
                                            <div className="p-2 space-y-1">
                                                {searchResults.map((material) => (
                                                    <button
                                                        key={material.id}
                                                        onClick={() => {
                                                            handleMaterialClick(material);
                                                            clearSearch();
                                                        }}
                                                        className="w-full text-left p-3 hover:bg-tg-secondary rounded-lg transition-colors"
                                                    >
                                                        <div className="font-medium truncate">{material.title}</div>
                                                        <div className="text-xs text-tg-hint flex items-center gap-2 mt-1">
                                                            <span>{material.material_type.toUpperCase()}</span>
                                                            {!material.is_own && (
                                                                <span className="flex items-center gap-1">
                                                                    <Users className="w-3 h-3" />
                                                                    Группа
                                                                </span>
                                                            )}
                                                        </div>
                                                    </button>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="py-8 text-center text-tg-hint">
                                                <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                                <p>Ничего не найдено</p>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Invite Banner */}
                        {!currentFolderId && user?.subscription_tier === 'free' && !showSearch && (
                            <InviteBanner />
                        )}

                        {/* Quick Actions */}
                        {!currentFolderId && !showSearch && (
                            <section>
                                <h2 className="text-sm font-medium text-tg-hint mb-2">Быстрые действия</h2>

                                {/* Первый ряд — 4 кнопки */}
                                <div className="grid grid-cols-4 gap-2 mb-2">
                                    <Card
                                        className="cursor-pointer active:scale-95 transition-transform text-center py-4"
                                        onClick={() => openUpload('scan')}
                                    >
                                        <Camera className="w-6 h-6 text-tg-button mx-auto mb-1" />
                                        <span className="text-xs font-medium">Скан</span>
                                    </Card>
                                    <Card
                                        className="cursor-pointer active:scale-95 transition-transform text-center py-4"
                                        onClick={() => openUpload('file')}
                                    >
                                        <Upload className="w-6 h-6 text-tg-button mx-auto mb-1" />
                                        <span className="text-xs font-medium">Файл</span>
                                    </Card>
                                    <Card
                                        className="cursor-pointer active:scale-95 transition-transform text-center py-4"
                                        onClick={() => openUpload('text')}
                                    >
                                        <Type className="w-6 h-6 text-tg-button mx-auto mb-1" />
                                        <span className="text-xs font-medium">Текст</span>
                                    </Card>
                                    <Card
                                        className="cursor-pointer active:scale-95 transition-transform text-center py-4 bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20"
                                        onClick={() => openUpload('topic')}
                                    >
                                        <Sparkles className="w-6 h-6 text-purple-500 mx-auto mb-1" />
                                        <span className="text-xs font-medium">Тема</span>
                                    </Card>
                                </div>

                                {/* Второй ряд — Генератор презентаций */}
                                <Card
                                    className={`cursor-pointer active:scale-[0.98] transition-all py-4 px-4 overflow-hidden relative ${isPro
                                            ? 'bg-gradient-to-r from-orange-500 via-pink-500 to-purple-500 text-white shadow-lg shadow-orange-500/25'
                                            : 'bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700'
                                        }`}
                                    onClick={openPresentationGenerator}
                                >
                                    {/* Декоративные элементы */}
                                    {isPro && (
                                        <>
                                            <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
                                            <div className="absolute bottom-0 left-10 w-16 h-16 bg-white/10 rounded-full translate-y-1/2" />
                                        </>
                                    )}

                                    <div className="relative flex items-center justify-center gap-3">
                                        <div className={`p-2 rounded-xl ${isPro ? 'bg-white/20' : 'bg-orange-100 dark:bg-orange-900/30'}`}>
                                            <Presentation className={`w-6 h-6 ${isPro ? 'text-white' : 'text-orange-500'}`} />
                                        </div>
                                        <div className="text-left">
                                            <div className="flex items-center gap-2">
                                                <span className={`font-bold ${isPro ? 'text-white' : 'text-tg-text'}`}>
                                                    Генератор презентаций
                                                </span>
                                                {isPro && <Sparkles className="w-4 h-4 text-yellow-300 animate-pulse" />}
                                            </div>
                                            <span className={`text-xs ${isPro ? 'text-white/80' : 'text-tg-hint'}`}>
                                                {isPro ? 'AI создаст слайды за секунды' : 'Доступно в Pro'}
                                            </span>
                                        </div>
                                        {!isPro && (
                                            <span className="ml-auto text-xs bg-gradient-to-r from-yellow-400 to-orange-400 text-white px-3 py-1 rounded-full font-medium shadow-sm">
                                                ⭐ Pro
                                            </span>
                                        )}
                                        {isPro && (
                                            <div className="ml-auto">
                                                <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                                                    <span className="text-white text-lg">→</span>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </Card>
                            </section>
                        )}

                        {/* Лимиты */}
                        {!currentFolderId && limits && user?.subscription_tier === 'free' && !showSearch && (
                            <Card className="bg-gradient-to-r from-tg-button/10 to-tg-button/5">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-tg-hint">Осталось сегодня</p>
                                        <p className="text-2xl font-bold">
                                            {limits.remaining_today}
                                            <span className="text-sm font-normal text-tg-hint">/{limits.daily_limit}</span>
                                        </p>
                                    </div>
                                    <Button variant="ghost" size="sm" onClick={handleGetPro}>
                                        ⭐ Pro
                                    </Button>
                                </div>
                            </Card>
                        )}

                        {/* Папки */}
                        {folders.length > 0 && !showSearch && (
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
                        {!showSearch && (
                            <section>
                                <div className="flex items-center justify-between mb-2">
                                    <h2 className="text-sm font-medium text-tg-hint">
                                        {currentFolderId ? 'Материалы в папке' : 'Материалы'}
                                    </h2>
                                    <button
                                        onClick={handleRefresh}
                                        className="p-1 text-tg-hint hover:text-tg-text transition-colors"
                                    >
                                        <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                                    </button>
                                </div>

                                {materials.length > 0 ? (
                                    <div className="space-y-2">
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
                        )}
                    </>
                ) : (
                    <GroupsTab
                        groups={groups}
                        onRefresh={() => loadData(false)}
                        onUploadToGroup={(groupId) => {
                            setUploadGroupId(groupId);
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
                onClose={() => {
                    setIsUploadOpen(false);
                    setUploadGroupId(undefined);
                    loadData(false);
                }}
                folderId={currentFolderId || undefined}
                groupId={uploadGroupId}
                initialMode={uploadMode}
            />

            {/* Presentation Generator Modal */}
            <PresentationGenerator
                isOpen={showPresentationModal}
                onClose={() => setShowPresentationModal(false)}
            />

            {/* Onboarding */}
            <OnboardingModal
                isOpen={showOnboarding}
                onClose={() => setShowOnboarding(false)}
            />

            {/* Ask Library FAB */}
            <AskLibrary />
        </div>
    );
}