// frontend/src/components/GroupsTab.tsx - СОЗДАЙ НОВЫЙ ФАЙЛ
import { useState } from 'react';
import { Users, Plus, Link, Copy, Check, LogOut, Trash2, Crown } from 'lucide-react';
import { Card, Button, Spinner } from './ui';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';

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

interface GroupsTabProps {
    groups: Group[];
    onRefresh: () => void;
}

export function GroupsTab({ groups, onRefresh }: GroupsTabProps) {
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [isJoinOpen, setIsJoinOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [copiedId, setCopiedId] = useState<string | null>(null);

    const handleCopyInvite = async (group: Group) => {
        const inviteLink = `https://t.me/your_bot?start=group_${group.invite_code}`;
        await navigator.clipboard.writeText(inviteLink);
        setCopiedId(group.id);
        telegram.haptic('success');
        setTimeout(() => setCopiedId(null), 2000);
    };

    const handleLeaveGroup = async (group: Group) => {
        if (!confirm(`Покинуть группу "${group.name}"?`)) return;

        try {
            await api.leaveGroup(group.id);
            telegram.haptic('success');
            onRefresh();
        } catch (error) {
            telegram.alert('Ошибка при выходе из группы');
        }
    };

    const handleDeleteGroup = async (group: Group) => {
        if (!confirm(`Удалить группу "${group.name}"? Это действие нельзя отменить.`)) return;

        try {
            await api.deleteGroup(group.id);
            telegram.haptic('success');
            onRefresh();
        } catch (error) {
            telegram.alert('Ошибка при удалении группы');
        }
    };

    return (
        <section className="space-y-4">
            {/* Кнопки действий */}
            <div className="grid grid-cols-2 gap-2">
                <Button
                    onClick={() => setIsCreateOpen(true)}
                    className="flex items-center justify-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Создать группу
                </Button>
                <Button
                    variant="secondary"
                    onClick={() => setIsJoinOpen(true)}
                    className="flex items-center justify-center gap-2"
                >
                    <Link className="w-4 h-4" />
                    Присоединиться
                </Button>
            </div>

            {/* Список групп */}
            {groups.length > 0 ? (
                <div className="space-y-2">
                    {groups.map((group) => (
                        <Card key={group.id} className="p-4">
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-medium">{group.name}</h3>
                                        {group.is_owner && (
                                            <Crown className="w-4 h-4 text-yellow-500" />
                                        )}
                                    </div>
                                    {group.description && (
                                        <p className="text-sm text-tg-hint mt-1">{group.description}</p>
                                    )}
                                    <div className="flex items-center gap-4 mt-2 text-sm text-tg-hint">
                                        <span className="flex items-center gap-1">
                                            <Users className="w-4 h-4" />
                                            {group.member_count}/{group.max_members}
                                        </span>
                                        <span className="capitalize">{group.role}</span>
                                    </div>
                                </div>

                                <div className="flex items-center gap-1">
                                    <button
                                        onClick={() => handleCopyInvite(group)}
                                        className="p-2 hover:bg-tg-secondary rounded-lg transition-colors"
                                    >
                                        {copiedId === group.id ? (
                                            <Check className="w-5 h-5 text-green-500" />
                                        ) : (
                                            <Copy className="w-5 h-5 text-tg-hint" />
                                        )}
                                    </button>

                                    {group.is_owner ? (
                                        <button
                                            onClick={() => handleDeleteGroup(group)}
                                            className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                                        >
                                            <Trash2 className="w-5 h-5 text-red-500" />
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => handleLeaveGroup(group)}
                                            className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                                        >
                                            <LogOut className="w-5 h-5 text-red-500" />
                                        </button>
                                    )}
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            ) : (
                <Card className="text-center py-8">
                    <Users className="w-12 h-12 text-tg-hint mx-auto mb-2" />
                    <p className="text-tg-hint mb-4">
                        У вас пока нет групп
                    </p>
                    <p className="text-sm text-tg-hint">
                        Создайте группу для совместного обучения или присоединитесь по ссылке
                    </p>
                </Card>
            )}

            {/* Модальные окна */}
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

// Модал создания группы
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
            telegram.alert('Введите название группы');
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
        } catch (error) {
            telegram.alert('Ошибка при создании группы');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md p-6">
                <h2 className="text-lg font-semibold mb-4">Создать группу</h2>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Название</label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Моя учебная группа"
                            className="w-full px-3 py-2 border rounded-lg bg-tg-secondary"
                            maxLength={100}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">Описание (опционально)</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Описание группы..."
                            className="w-full px-3 py-2 border rounded-lg bg-tg-secondary resize-none"
                            rows={3}
                            maxLength={500}
                        />
                    </div>
                </div>

                <div className="flex gap-2 mt-6">
                    <Button variant="secondary" onClick={onClose} className="flex-1">
                        Отмена
                    </Button>
                    <Button onClick={handleCreate} disabled={isLoading} className="flex-1">
                        {isLoading ? <Spinner size="sm" /> : 'Создать'}
                    </Button>
                </div>
            </Card>
        </div>
    );
}

// Модал присоединения к группе
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
            telegram.alert('Введите код приглашения');
            return;
        }

        setIsLoading(true);
        try {
            const result = await api.joinGroup(code.trim());
            telegram.haptic('success');
            telegram.alert(`Вы присоединились к группе "${result.group.name}"!`);
            onJoined();
            onClose();
            setCode('');
        } catch (error: any) {
            telegram.alert(error.response?.data?.detail || 'Ошибка при присоединении');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md p-6">
                <h2 className="text-lg font-semibold mb-4">Присоединиться к группе</h2>

                <div>
                    <label className="block text-sm font-medium mb-1">Код приглашения</label>
                    <input
                        type="text"
                        value={code}
                        onChange={(e) => setCode(e.target.value.toUpperCase())}
                        placeholder="XXXXXXXX"
                        className="w-full px-3 py-2 border rounded-lg bg-tg-secondary text-center font-mono text-lg tracking-wider"
                        maxLength={20}
                    />
                </div>

                <div className="flex gap-2 mt-6">
                    <Button variant="secondary" onClick={onClose} className="flex-1">
                        Отмена
                    </Button>
                    <Button onClick={handleJoin} disabled={isLoading} className="flex-1">
                        {isLoading ? <Spinner size="sm" /> : 'Присоединиться'}
                    </Button>
                </div>
            </Card>
        </div>
    );
}