// frontend/src/components/MaterialActions.tsx
import { useState } from 'react';
import { MoreVertical, Edit2, Trash2, X, Check } from 'lucide-react';
import { api } from '../lib/api';
import { telegram } from '../lib/telegram';

interface Material {
    id: string;
    title: string;
    folder_id?: string;
}

interface MaterialActionsProps {
    material: Material;
    onUpdate: () => void;
    onDelete: () => void;
    children?: React.ReactNode;
}

export function MaterialActions({ material, onUpdate, onDelete, children }: MaterialActionsProps) {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isRenaming, setIsRenaming] = useState(false);
    const [newTitle, setNewTitle] = useState(material.title);
    const [isLoading, setIsLoading] = useState(false);

    const handleRename = async () => {
        if (!newTitle.trim() || newTitle === material.title) {
            setIsRenaming(false);
            return;
        }

        setIsLoading(true);
        try {
            await api.updateMaterial(material.id, { title: newTitle.trim() });
            telegram.haptic('success');
            onUpdate();
            setIsRenaming(false);
        } catch (error: any) {
            telegram.alert(error.response?.data?.detail || 'Ошибка переименования');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async () => {
        setIsMenuOpen(false);

        const confirmed = confirm(`Удалить "${material.title}"?`);
        if (!confirmed) return;

        setIsLoading(true);
        try {
            await api.deleteMaterial(material.id);
            telegram.haptic('success');
            onDelete();
        } catch (error: any) {
            telegram.alert(error.response?.data?.detail || 'Ошибка удаления');
        } finally {
            setIsLoading(false);
        }
    };

    if (isRenaming) {
        return (
            <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    className="flex-1 px-2 py-1 text-sm border rounded bg-tg-secondary"
                    autoFocus
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRename();
                        if (e.key === 'Escape') setIsRenaming(false);
                    }}
                />
                <button
                    onClick={handleRename}
                    disabled={isLoading}
                    className="p-1 text-green-500 hover:bg-green-100 rounded"
                >
                    <Check className="w-4 h-4" />
                </button>
                <button
                    onClick={() => setIsRenaming(false)}
                    className="p-1 text-red-500 hover:bg-red-100 rounded"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>
        );
    }

    return (
        <div className="relative" onClick={(e) => e.stopPropagation()}>
            {children ? (
                <div onClick={() => setIsMenuOpen(!isMenuOpen)}>
                    {children}
                </div>
            ) : (
                <button
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    className="p-2 hover:bg-tg-secondary rounded-lg transition-colors"
                >
                    <MoreVertical className="w-4 h-4 text-tg-hint" />
                </button>
            )}

            {isMenuOpen && (
                <>
                    <div
                        className="fixed inset-0 z-40"
                        onClick={() => setIsMenuOpen(false)}
                    />

                    <div className="absolute right-0 top-full mt-1 bg-tg-bg border border-tg-secondary rounded-xl shadow-lg z-50 py-1 min-w-[150px]">
                        <button
                            onClick={() => {
                                setIsMenuOpen(false);
                                setIsRenaming(true);
                                telegram.haptic('light');
                            }}
                            className="w-full flex items-center gap-3 px-4 py-2 hover:bg-tg-secondary transition-colors"
                        >
                            <Edit2 className="w-4 h-4 text-tg-hint" />
                            <span>Переименовать</span>
                        </button>

                        <button
                            onClick={handleDelete}
                            className="w-full flex items-center gap-3 px-4 py-2 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-red-500"
                        >
                            <Trash2 className="w-4 h-4" />
                            <span>Удалить</span>
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}