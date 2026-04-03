// frontend/src/components/GroupsTab.tsx
import { useState, useEffect } from 'react';
import { Users, Plus, Link, Copy, Check, LogOut, Trash2, Crown, ChevronRight, ArrowLeft, Search, SortAsc, SortDesc, FileText, Trophy, RefreshCw } from 'lucide-react';
import { Card, Button, Spinner } from './ui';
import { api } from '../lib/api';
import { telegram } from '../lib/telegram';
import { MaterialCard } from './MaterialCard';
import { LeaderboardTab } from './LeaderboardTab';

interface Group {
    id: string;
    name: string;
    description?: string;
    invite_code: string;
    role: 'owner' | 'admin' | 'member';
    member_count: number;
    max_members: number;
    is_owner: boolean;
}

interface Material {
    id: string;
    title: string;
    material_type: string;
    status: string;
    created_at: string;
}

interface GroupsTabProps {
    groups: Group[];
    onRefresh: () => void;
    onUploadToGroup?: (groupId: string) => void;
}

type SortOption = 'date_desc' | 'date_asc' | 'name_asc' | 'name_desc';
type GroupView = 'materials' | 'leaderboard';

// ✅ Добавляем значение по умолчанию для groups
export function GroupsTab({ groups = [], onRefresh, onUploadToGroup }: GroupsTabProps) {
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [isJoinOpen, setIsJoinOpen] = useState(false);
    const [copiedId, setCopiedId] = useState<string | null>(null);

    const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
    const [groupMaterials, setGroupMaterials] = useState<Material[]>([]);
    const [isLoadingMaterials, setIsLoadingMaterials] = useState(false);
    const [isRefreshingMaterials, setIsRefreshingMaterials] = useState(false);

    const [groupView, setGroupView] = useState<GroupView>('materials');

    const [searchQuery, setSearchQuery] = useState('');
    const [sortOption, setSortOption] = useState<SortOption>('date_desc');
    const [showSortMenu, setShowSortMenu] = useState(false);

    // ✅ Гарантируем, что groups всегда массив
    const safeGroups = Array.isArray(groups) ? groups : [];

    // ✅ Используем safeGroups в useEffect
    useEffect(() => {
        if (selectedGroup && safeGroups.length > 0) {
            const updatedGroup = safeGroups.find(g => g.id === selectedGroup.id);
            if (updatedGroup) {
                setSelectedGroup(updatedGroup);
            }
        }
    }, [safeGroups, selectedGroup]);

    const handleCopyInvite = async (e: React.MouseEvent, group: Group) => {
        e.stopPropagation();
        const inviteText = `📚 Присоединяйся к группе "${group.name}" в Lecto!\n\n🔑 Код: ${group.invite_code}`;
        await navigator.clipboard.writeText(inviteText);
        setCopiedId(group.id);
        telegram.haptic('success');
        setTimeout(() => setCopiedId(null), 2000);
    };

    const handleLeaveGroup = async (e: React.MouseEvent, group: Group) => {
        e.stopPropagation();
        if (!confirm(`Покинуть группу "${group.name}"?`)) return;

        try {
            await api.leaveGroup(group.id);
            telegram.haptic('success');
            onRefresh();
        } catch (error: unknown) {
            telegram.alert((error as any).response?.data?.detail || 'Ошибка');
        }
    };

    const handleDeleteGroup = async (e: React.MouseEvent, group: Group) => {
        e.stopPropagation();
        if (!confirm(`Удалить группу "${group.name}"?`)) return;

        try {
            await api.deleteGroup(group.id);
            telegram.haptic('success');
            onRefresh();
        } catch (error: unknown) {
            telegram.alert((error as any).response?.data?.detail || 'Ошибка');
        }
    };

    const loadGroupMaterials = async (groupId: string) => {
        try {
            const materials = await api.getGroupMaterials(groupId);
            setGroupMaterials(Array.isArray(materials) ? materials : []);
        } catch (error: unknown) {
            console.error('Failed to load group materials:', error);
            setGroupMaterials([]);
        }
    };

    const openGroup = async (group: Group) => {
        setSelectedGroup(group);
        setIsLoadingMaterials(true);
        setSearchQuery('');
        setGroupView('materials');
        telegram.haptic('selection');

        try {
            await loadGroupMaterials(group.id);
        } finally {
            setIsLoadingMaterials(false);
        }
    };

    const closeGroup = () => {
        setSelectedGroup(null);
        setGroupMaterials([]);
        setSearchQuery('');
        setGroupView('materials');
    };

    const refreshGroupMaterials = async () => {
        if (!selectedGroup) return;

        setIsRefreshingMaterials(true);
        telegram.haptic('light');

        try {
            await loadGroupMaterials(selectedGroup.id);
        } finally {
            setIsRefreshingMaterials(false);
        }
    };

    const handleUploadToGroup = (groupId: string) => {
        telegram.haptic('medium');
        if (onUploadToGroup) {
            onUploadToGroup(groupId);
        }
    };

    const getFilteredAndSortedMaterials = () => {
        let filtered = [...groupMaterials];

        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(m =>
                m.title.toLowerCase().includes(query)
            );
        }

        filtered.sort((a, b) => {
            switch (sortOption) {
                case 'date_desc':
                    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
                case 'date_asc':
                    return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
                case 'name_asc':
                    return a.title.localeCompare(b.title, 'ru');
                case 'name_desc':
                    return b.title.localeCompare(a.title, 'ru');
                default:
                    return 0;
            }
        });

        return filtered;
    };

    const sortOptions = [
        { value: 'date_desc', label: 'Сначала новые', icon: <SortDesc className="w-4 h-4" /> },
        { value: 'date_asc', label: 'Сначала старые', icon: <SortAsc className="w-4 h-4" /> },
        { value: 'name_asc', label: 'По названию А-Я', icon: <FileText className="w-4 h-4" /> },
        { value: 'name_desc', label: 'По названию Я-А', icon: <FileText className="w-4 h-4" /> },
    ];

    // Если открыта группа
    if (selectedGroup) {
        const filteredMaterials = getFilteredAndSortedMaterials();

        return (
            <section className="space-y-4">
                {/* Шапка группы */}
                <div className="flex items-center gap-3">
                    <button
                        onClick={closeGroup}
                        className="p-2 hover:bg-tg-secondary rounded-lg"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div className="flex-1">
                        <h2 className="font-semibold">{selectedGroup.name}</h2>
                        <p className="text-sm text-tg-hint">
                            {selectedGroup.member_count} участников • Код: {selectedGroup.invite_code}
                        </p>
                    </div>

                    <button
                        onClick={refreshGroupMaterials}
                        className="p-2 hover:bg-lecto-bg-secondary rounded-lg"
                        disabled={isRefreshingMaterials}
                    >
                        <RefreshCw className={`w-5 h-5 text-lecto-hint ${isRefreshingMaterials ? 'animate-spin' : ''}`} />
                    </button>

                    {onUploadToGroup && (
                        <button
                            onClick={() => handleUploadToGroup(selectedGroup.id)}
                            className="p-2 bg-lecto-button text-lecto-button-text rounded-lg"
                        >
                            <Plus className="w-5 h-5" />
                        </button>
                    )}
                </div>

                {/* Вкладки: Материалы / Рейтинг */}
                <div className="flex bg-lecto-bg-secondary rounded-lg p-1">
                    <button
                        onClick={() => {
                            setGroupView('materials');
                            telegram.haptic('selection');
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${groupView === 'materials'
                            ? 'bg-lecto-bg-secondary shadow text-lecto-text'
                            : 'text-lecto-hint'
                            }`}
                    >
                        <FileText className="w-4 h-4" />
                        Материалы
                    </button>
                    <button
                        onClick={() => {
                            setGroupView('leaderboard');
                            telegram.haptic('selection');
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${groupView === 'leaderboard'
                            ? 'bg-lecto-bg-secondary shadow text-lecto-text'
                            : 'text-lecto-hint'
                            }`}
                    >
                        <Trophy className="w-4 h-4" />
                        Рейтинг
                    </button>
                </div>

                {/* Кнопка результатов тестов для owner */}
                {selectedGroup.is_owner && groupView === 'materials' && (
                    <Button
                        variant="primary"
                        className="w-full"
                        onClick={() => {
                            telegram.haptic('medium');
                            window.location.hash = `#/group/${selectedGroup.id}/results`;
                        }}
                    >
                        📊 Результаты тестов участников
                    </Button>
                )}

                {/* Контент в зависимости от вкладки */}
                {groupView === 'leaderboard' ? (
                    <LeaderboardTab groupId={selectedGroup.id} />
                ) : (
                    <>
                        {/* Поиск и сортировка */}
                        <div className="flex gap-2">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tg-hint" />
                                <input
                                    type="text"
                                    placeholder="Поиск материалов..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 bg-lecto-bg-secondary rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-lecto-button"
                                />
                            </div>

                            <div className="relative">
                                <button
                                    onClick={() => setShowSortMenu(!showSortMenu)}
                                    className="p-2 bg-lecto-bg-secondary rounded-xl hover:bg-lecto-hint/20 transition-colors"
                                >
                                    <SortAsc className="w-5 h-5 text-lecto-hint" />
                                </button>

                                {showSortMenu && (
                                    <>
                                        <div
                                            className="fixed inset-0 z-40"
                                            onClick={() => setShowSortMenu(false)}
                                        />
                                        <div className="absolute right-0 top-full mt-2 bg-tg-bg border border-tg-secondary rounded-xl shadow-lg z-50 py-1 min-w-[180px]">
                                            {sortOptions.map((option) => (
                                                <button
                                                    key={option.value}
                                                    onClick={() => {
                                                        setSortOption(option.value as SortOption);
                                                        setShowSortMenu(false);
                                                        telegram.haptic('light');
                                                    }}
                                                    className={`w-full flex items-center gap-3 px-4 py-2 hover:bg-tg-secondary transition-colors ${sortOption === option.value ? 'text-tg-button' : ''
                                                        }`}
                                                >
                                                    {option.icon}
                                                    <span className="text-sm">{option.label}</span>
                                                    {sortOption === option.value && (
                                                        <Check className="w-4 h-4 ml-auto" />
                                                    )}
                                                </button>
                                            ))}
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* Материалы */}
                        {isLoadingMaterials ? (
                            <div className="flex justify-center py-8">
                                <Spinner size="lg" />
                            </div>
                        ) : filteredMaterials.length > 0 ? (
                            <div className="space-y-2">
                                {filteredMaterials.map((material) => (
                                    <MaterialCard
                                        key={material.id}
                                        material={material}
                                        onClick={() => {
                                            window.location.hash = `#/material/${material.id}`;
                                        }}
                                        showActions={false}
                                    />
                                ))}
                            </div>
                        ) : (
                            <Card className="text-center py-8">
                                {searchQuery ? (
                                    <>
                                        <Search className="w-12 h-12 text-tg-hint mx-auto mb-2" />
                                        <p className="text-tg-hint">Ничего не найдено</p>
                                        <p className="text-sm text-tg-hint mt-1">Попробуйте изменить запрос</p>
                                    </>
                                ) : (
                                    <>
                                        <Users className="w-12 h-12 text-tg-hint mx-auto mb-2" />
                                        <p className="text-tg-hint mb-2">В группе пока нет материалов</p>
                                        {onUploadToGroup && (
                                            <Button
                                                onClick={() => handleUploadToGroup(selectedGroup.id)}
                                                className="mt-2"
                                            >
                                                <Plus className="w-4 h-4 mr-2" />
                                                Добавить материал
                                            </Button>
                                        )}
                                    </>
                                )}
                            </Card>
                        )}
                    </>
                )}
            </section>
        );
    }

    // ✅ Список групп - используем safeGroups
    return (
        <section className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
                <Button
                    onClick={() => setIsCreateOpen(true)}
                    className="flex items-center justify-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Создать
                </Button>
                <Button
                    variant="primary"
                    onClick={() => setIsJoinOpen(true)}
                    className="flex items-center justify-center gap-2"
                >
                    <Link className="w-4 h-4" />
                    Вступить
                </Button>
            </div>

            {safeGroups.length > 0 ? (
                <div className="space-y-2">
                    {safeGroups.map((group) => (
                        <Card
                            key={group.id}
                            className="p-4 cursor-pointer hover:bg-tg-secondary/50 transition-colors"
                            onClick={() => openGroup(group)}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-medium truncate">{group.name}</h3>
                                        {group.is_owner && (
                                            <Crown className="w-4 h-4 text-yellow-500 flex-shrink-0" />
                                        )}
                                    </div>
                                    <div className="flex items-center gap-3 mt-1 text-sm text-tg-hint">
                                        <span className="flex items-center gap-1">
                                            <Users className="w-3 h-3" />
                                            {group.member_count}
                                        </span>
                                        <span>{group.role}</span>
                                    </div>
                                </div>

                                <div className="flex items-center gap-1">
                                    <button
                                        onClick={(e) => handleCopyInvite(e, group)}
                                        className="p-2 hover:bg-tg-secondary rounded-lg"
                                    >
                                        {copiedId === group.id ? (
                                            <Check className="w-4 h-4 text-green-500" />
                                        ) : (
                                            <Copy className="w-4 h-4 text-tg-hint" />
                                        )}
                                    </button>

                                    {group.is_owner ? (
                                        <button
                                            onClick={(e) => handleDeleteGroup(e, group)}
                                            className="p-2 hover:bg-red-100 rounded-lg"
                                        >
                                            <Trash2 className="w-4 h-4 text-red-500" />
                                        </button>
                                    ) : (
                                        <button
                                            onClick={(e) => handleLeaveGroup(e, group)}
                                            className="p-2 hover:bg-red-100 rounded-lg"
                                        >
                                            <LogOut className="w-4 h-4 text-red-500" />
                                        </button>
                                    )}

                                    <ChevronRight className="w-4 h-4 text-tg-hint" />
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            ) : (
                <Card className="text-center py-8">
                    <Users className="w-12 h-12 text-tg-hint mx-auto mb-2" />
                    <p className="text-tg-hint mb-4">У вас пока нет групп</p>
                </Card>
            )}

            <CreateGroupModal
                isOpen={isCreateOpen}
                onClose={() => setIsCreateOpen(false)}
                onCreated={onRefresh}
            />
            <JoinGroupModal
                isOpen={isJoinOpen}
                onClose={() => setIsJoinOpen(false)}
                onJoined={onRefresh}
            />
        </section>
    );
}

function CreateGroupModal({ isOpen, onClose, onCreated }: {
    isOpen: boolean;
    onClose: () => void;
    onCreated: () => void;
}) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    if (!isOpen) return null;

    const handleCreate = async () => {
        if (!name.trim()) {
            telegram.alert('Введите название');
            return;
        }
        setIsLoading(true);
        try {
            await api.createGroup(name.trim(), description.trim() || undefined);
            telegram.haptic('success');

            // ✅ Сначала сбрасываем форму
            setName('');
            setDescription('');

            // ✅ Закрываем модалку
            onClose();

            // ✅ Потом обновляем данные (с небольшой задержкой)
            setTimeout(() => {
                onCreated();
            }, 300);

        } catch (error: unknown) {
            telegram.haptic('error');
            telegram.alert((error as any).response?.data?.detail || 'Ошибка создания группы');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 mt-0" style={{ marginTop: '0' }}>
            <Card variant="modal" className="w-full max-w-md p-6">
                <h2 className="text-lg font-semibold mb-4">Создать группу</h2>
                <div className="space-y-4">
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Название группы"
                        className="w-full px-3 py-2 border rounded-lg lecto-bg-secondary focus:outline-none focus:ring-2 focus:ring-lecto-accent-primary transition-all bg-lecto-bg-secondary"
                        autoFocus
                    />
                    <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Описание (опционально)"
                        className="w-full px-3 py-2 border rounded-lg lecto-bg-secondary resize-none focus:outline-none focus:ring-2 focus:ring-lecto-accent-primary transition-all bg-lecto-bg-secondary"
                        rows={3}
                    />
                </div>
                <div className="flex gap-2 mt-6">
                    <Button variant="primary" onClick={onClose} className="flex-1" disabled={isLoading}>
                        Отмена
                    </Button>
                    <Button onClick={handleCreate} disabled={isLoading || !name.trim()} className="flex-1">
                        {isLoading ? <Spinner size="sm" /> : 'Создать'}
                    </Button>
                </div>
            </Card>
        </div>
    );
}

function JoinGroupModal({ isOpen, onClose, onJoined }: {
    isOpen: boolean;
    onClose: () => void;
    onJoined: () => void;
}) {
    const [code, setCode] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    if (!isOpen) return null;

    const handleJoin = async () => {
        if (!code.trim()) {
            telegram.alert('Введите код');
            return;
        }
        setIsLoading(true);
        try {
            const result = await api.joinGroup(code.trim());
            telegram.haptic('success');

            // ✅ Сбрасываем форму
            setCode('');

            // ✅ Закрываем модалку
            onClose();

            // ✅ Показываем сообщение
            telegram.alert(`Вы вступили в "${result.group.name}"!`);

            // ✅ Обновляем данные
            setTimeout(() => {
                onJoined();
            }, 300);

        } catch (error: unknown) {
            telegram.haptic('error');
            telegram.alert((error as any).response?.data?.detail || 'Группа не найдена');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 " style={{ marginTop: '0' }}>
            <Card variant="modal" className="w-full max-w-md p-6">
                <h2 className="text-lg font-semibold mb-4">Вступить в группу</h2>
                <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value.toUpperCase())}
                    placeholder="Код приглашения"
                    className="w-full px-3 py-2 border rounded-lg bg-lecto-bg-secondary focus:ring-lecto-accent-primary focus:ring-2 focus:outline-none transition-all text-center font-mono text-lg"
                    autoFocus
                />
                <div className="flex gap-2 mt-6">
                    <Button variant="primary" onClick={onClose} className="flex-1" disabled={isLoading}>
                        Отмена
                    </Button>
                    <Button onClick={handleJoin} disabled={isLoading || !code.trim()} className="flex-1">
                        {isLoading ? <Spinner size="sm" /> : 'Вступить'}
                    </Button>
                </div>
            </Card>
        </div>
    );
}