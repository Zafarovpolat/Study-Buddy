// frontend/src/components/GroupsTab.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { useState } from 'react';
import { Users, Plus, Link, Copy, Check, LogOut, Trash2, Crown, ChevronRight, ArrowLeft } from 'lucide-react';
import { Card, Button, Spinner } from './ui';
import { api } from '../lib/api';
import { telegram } from '../lib/telegram';
import { MaterialCard } from './MaterialCard';

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

export function GroupsTab({ groups, onRefresh, onUploadToGroup }: GroupsTabProps) {
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [isJoinOpen, setIsJoinOpen] = useState(false);
    const [copiedId, setCopiedId] = useState<string | null>(null);

    const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
    const [groupMaterials, setGroupMaterials] = useState<Material[]>([]);
    const [isLoadingMaterials, setIsLoadingMaterials] = useState(false);

    const handleCopyInvite = async (e: React.MouseEvent, group: Group) => {
        e.stopPropagation();
        const inviteText = `📚 Присоединяйся к группе "${group.name}"!\n\n🔑 Код: ${group.invite_code}`;
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
        } catch (error: any) {
            telegram.alert(error.response?.data?.detail || 'Ошибка');
        }
    };

    const handleDeleteGroup = async (e: React.MouseEvent, group: Group) => {
        e.stopPropagation();
        if (!confirm(`Удалить группу "${group.name}"?`)) return;

        try {
            await api.deleteGroup(group.id);
            telegram.haptic('success');
            onRefresh();
        } catch (error: any) {
            telegram.alert(error.response?.data?.detail || 'Ошибка');
        }
    };

    const openGroup = async (group: Group) => {
        setSelectedGroup(group);
        setIsLoadingMaterials(true);
        telegram.haptic('selection');

        try {
            const materials = await api.getGroupMaterials(group.id);
            setGroupMaterials(materials);
        } catch (error) {
            console.error('Failed to load group materials:', error);
            setGroupMaterials([]);
        } finally {
            setIsLoadingMaterials(false);
        }
    };

    const closeGroup = () => {
        setSelectedGroup(null);
        setGroupMaterials([]);
    };

    // Если открыта группа
    if (selectedGroup) {
        return (
            <section className="space-y-4">
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

                    {onUploadToGroup && (
                        <button
                            onClick={() => {
                                telegram.haptic('medium');
                                onUploadToGroup(selectedGroup.id);
                            }}
                            className="p-2 bg-tg-button text-tg-button-text rounded-lg"
                        >
                            <Plus className="w-5 h-5" />
                        </button>
                    )}
                </div>

                {isLoadingMaterials ? (
                    <div className="flex justify-center py-8">
                        <Spinner size="lg" />
                    </div>
                ) : groupMaterials.length > 0 ? (
                    <div className="space-y-2">
                        {groupMaterials.map((material) => (
                            <MaterialCard
                                key={material.id}
                                material={material}
                                onClick={() => {
                                    window.location.hash = `#/material/${material.id}`;
                                }}
                            />
                        ))}
                    </div>
                ) : (
                    <Card className="text-center py-8">
                        <Users className="w-12 h-12 text-tg-hint mx-auto mb-2" />
                        <p className="text-tg-hint mb-2">В группе пока нет материалов</p>
                        {onUploadToGroup && (
                            <Button
                                onClick={() => onUploadToGroup(selectedGroup.id)}
                                className="mt-2"
                            >
                                <Plus className="w-4 h-4 mr-2" />
                                Добавить материал
                            </Button>
                        )}
                    </Card>
                )}
            </section>
        );
    }

    // Список групп
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
                    variant="secondary"
                    onClick={() => setIsJoinOpen(true)}
                    className="flex items-center justify-center gap-2"
                >
                    <Link className="w-4 h-4" />
                    Вступить
                </Button>
            </div>

            {groups.length > 0 ? (
                <div className="space-y-2">
                    {groups.map((group) => (
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
            onCreated();
            onClose();
            setName('');
            setDescription('');
        } catch (error: any) {
            telegram.alert(error.response?.data?.detail || 'Ошибка');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md p-6">
                <h2 className="text-lg font-semibold mb-4">Создать группу</h2>
                <div className="space-y-4">
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Название группы"
                        className="w-full px-3 py-2 border rounded-lg bg-tg-secondary"
                    />
                    <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Описание (опционально)"
                        className="w-full px-3 py-2 border rounded-lg bg-tg-secondary resize-none"
                        rows={3}
                    />
                </div>
                <div className="flex gap-2 mt-6">
                    <Button variant="secondary" onClick={onClose} className="flex-1">Отмена</Button>
                    <Button onClick={handleCreate} disabled={isLoading} className="flex-1">
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
            telegram.alert(`Вы вступили в "${result.group.name}"!`);
            onJoined();
            onClose();
            setCode('');
        } catch (error: any) {
            telegram.alert(error.response?.data?.detail || 'Группа не найдена');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md p-6">
                <h2 className="text-lg font-semibold mb-4">Вступить в группу</h2>
                <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value.toUpperCase())}
                    placeholder="Код приглашения"
                    className="w-full px-3 py-2 border rounded-lg bg-tg-secondary text-center font-mono text-lg"
                />
                <div className="flex gap-2 mt-6">
                    <Button variant="secondary" onClick={onClose} className="flex-1">Отмена</Button>
                    <Button onClick={handleJoin} disabled={isLoading} className="flex-1">
                        {isLoading ? <Spinner size="sm" /> : 'Вступить'}
                    </Button>
                </div>
            </Card>
        </div>
    );
}