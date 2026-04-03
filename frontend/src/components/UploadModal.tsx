// frontend/src/components/UploadModal.tsx
import { useState, useEffect } from 'react';
import { X, Upload, FileText, Type, Camera, Image, ChevronDown, Users, User, Folder, Sparkles, Lightbulb } from 'lucide-react';
import { Button, Input, Textarea, Card } from './ui';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';

interface UploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    folderId?: string;
    groupId?: string;
    initialMode?: 'file' | 'scan' | 'text' | 'topic';
}

type UploadMode = 'file' | 'text' | 'scan' | 'topic';
type UploadTarget =
    | { type: 'personal'; id?: undefined }
    | { type: 'folder'; id: string; name: string }
    | { type: 'group'; id: string; name: string };

export function UploadModal({ isOpen, onClose, folderId, groupId, initialMode = 'file' }: UploadModalProps) {
    const [mode, setMode] = useState<UploadMode>(initialMode);
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [topicName, setTopicName] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [filePreview, setFilePreview] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [showTargetDropdown, setShowTargetDropdown] = useState(false);

    const { groups, folders } = useStore();

    const getInitialTarget = (): UploadTarget => {
        if (groupId) {
            const group = groups.find(g => g.id === groupId);
            if (group) {
                return { type: 'group', id: group.id, name: group.name };
            }
        }
        if (folderId) {
            const folder = folders.find(f => f.id === folderId);
            if (folder) {
                return { type: 'folder', id: folder.id, name: folder.name };
            }
        }
        return { type: 'personal' };
    };

    const [uploadTarget, setUploadTarget] = useState<UploadTarget>(getInitialTarget);

    useEffect(() => {
        if (isOpen) {
            setMode(initialMode);
            setUploadTarget(getInitialTarget());
        }
    }, [isOpen, initialMode, folderId, groupId, groups, folders]);

    // Escape key для закрытия
    useEffect(() => {
        if (!isOpen) return;
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                resetForm();
                onClose();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose]);

    // Очистка превью при размонтировании
    useEffect(() => {
        return () => {
            if (filePreview) {
                URL.revokeObjectURL(filePreview);
            }
        };
    }, [filePreview]);

    if (!isOpen) return null;

    // ===== ОТКРЫТИЕ КАМЕРЫ (динамический input) =====
    const openCamera = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.capture = 'environment'; // Задняя камера

        input.onchange = (e) => {
            const target = e.target as HTMLInputElement;
            const selectedFile = target.files?.[0];
            if (selectedFile) {
                handleImageSelected(selectedFile);
            }
        };

        input.click();
    };

    // ===== ОТКРЫТИЕ ГАЛЕРЕИ (динамический input) =====
    const openGallery = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/jpeg,image/png,image/webp,image/jpg';
        // БЕЗ capture - открывает галерею

        input.onchange = (e) => {
            const target = e.target as HTMLInputElement;
            const selectedFile = target.files?.[0];
            if (selectedFile) {
                handleImageSelected(selectedFile);
            }
        };

        input.click();
    };

    // ===== ОТКРЫТИЕ ВЫБОРА ФАЙЛА =====
    const openFileSelector = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.pdf,.docx,.doc,.txt';

        input.onchange = (e) => {
            const target = e.target as HTMLInputElement;
            const selectedFile = target.files?.[0];
            if (selectedFile) {
                setFile(selectedFile);
                if (!title) {
                    setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
                }
            }
        };

        input.click();
    };

    // ===== ОБРАБОТКА ВЫБРАННОГО ИЗОБРАЖЕНИЯ =====
    const handleImageSelected = (selectedFile: File) => {
        setFile(selectedFile);

        // Создаём превью
        const url = URL.createObjectURL(selectedFile);
        setFilePreview(url);

        if (!title) {
            setTitle('Скан: ' + new Date().toLocaleDateString('ru-RU'));
        }

        telegram.haptic('light');
    };

    const clearFile = () => {
        if (filePreview) {
            URL.revokeObjectURL(filePreview);
        }
        setFile(null);
        setFilePreview(null);
    };

    const handleSelectTarget = (target: UploadTarget) => {
        setUploadTarget(target);
        setShowTargetDropdown(false);
        telegram.haptic('light');
    };

    const handleSubmit = async () => {
        try {
            setIsLoading(true);
            telegram.haptic('medium');

            let targetFolderId: string | undefined;
            let targetGroupId: string | undefined;

            if (uploadTarget.type === 'folder') {
                targetFolderId = uploadTarget.id;
            } else if (uploadTarget.type === 'group') {
                targetGroupId = uploadTarget.id;
            }

            if (mode === 'file' && file) {
                await api.uploadFile(file, title || file.name, targetFolderId, targetGroupId);
            } else if (mode === 'scan' && file) {
                await api.scanImage(file, title || 'Скан', targetFolderId, targetGroupId);
            } else if (mode === 'text' && content.trim()) {
                await api.createTextMaterial(
                    title || 'Без названия',
                    content,
                    targetFolderId,
                    targetGroupId
                );
            } else if (mode === 'topic' && topicName.trim()) {
                await api.generateFromTopic(
                    topicName.trim(),
                    targetFolderId,
                    targetGroupId
                );
            } else {
                telegram.alert('Заполните необходимые поля');
                setIsLoading(false);
                return;
            }

            // Успех! Закрываем сразу, не ждём обработки
            telegram.haptic('success');
            onClose();
            setTimeout(() => {
                resetForm();
            }, 300);

        } catch (error: unknown) {
            console.error('Upload error:', error);
            telegram.haptic('error');

            // Проверяем тип ошибки
            if ((error as any).code === 'ECONNABORTED' || (error as Error).message?.includes('timeout')) {
                // Timeout — но материал скорее всего создан
                telegram.alert('Материал загружен, обработка идёт в фоне. Обновите страницу.');
                resetForm();
                onClose();
            } else {
                const errorMessage = (error as any).response?.data?.detail || (error as Error).message || 'Ошибка загрузки';
                telegram.alert(errorMessage);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const resetForm = () => {
        setTitle('');
        setContent('');
        setTopicName('');
        clearFile();
        setMode('file');
        setShowTargetDropdown(false);
    };

    const getTargetIcon = () => {
        switch (uploadTarget.type) {
            case 'group':
                return <Users className="w-4 h-4 text-lecto-accent-primary" />;
            case 'folder':
                return <Folder className="w-4 h-4 text-lecto-accent-primary" />;
            default:
                return <User className="w-4 h-4 text-lecto-accent-primary" />;
        }
    };

    const getTargetBgClass = () => {
        switch (uploadTarget.type) {
            case 'group':
                return 'bg-lecto-accent-primary/10';
            default:
                return 'bg-lecto-accent-primary/10';
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-end justify-center">
            <div className="bg-white w-full max-w-lg rounded-t-3xl p-6 max-h-[90vh] overflow-y-auto animate-slide-up">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-lecto-text-primary">Новый материал</h2>
                    <button
                        onClick={() => { resetForm(); onClose(); }}
                        className="p-2 hover:bg-lecto-bg-secondary rounded-full transition-colors"
                    >
                        <X className="w-5 h-5 text-lecto-text-secondary" />
                    </button>
                </div>

                {/* Dropdown выбора места загрузки */}
                <div className="mb-4 relative">
                    <label className="block text-sm font-medium text-lecto-text-secondary mb-2">
                        Загрузить в:
                    </label>
                    <button
                        type="button"
                        onClick={() => setShowTargetDropdown(!showTargetDropdown)}
                        className="w-full flex items-center justify-between p-3 bg-lecto-bg-secondary rounded-xl border border-transparent hover:border-lecto-accent-primary transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 ${getTargetBgClass()} rounded-full flex items-center justify-center`}>
                                {getTargetIcon()}
                            </div>
                            <span className="font-medium">
                                {uploadTarget.type === 'personal'
                                    ? 'Личная библиотека'
                                    : uploadTarget.name}
                            </span>
                        </div>
                        <ChevronDown className={`w-5 h-5 text-lecto-text-secondary transition-transform ${showTargetDropdown ? 'rotate-180' : ''}`} />
                    </button>

                    {showTargetDropdown && (
                        <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-lecto-border rounded-xl shadow-lg z-10 overflow-hidden max-h-64 overflow-y-auto">
                            <button
                                type="button"
                                onClick={() => handleSelectTarget({ type: 'personal' })}
                                className={`w-full flex items-center gap-3 p-3 hover:bg-lecto-bg-secondary transition-colors ${uploadTarget.type === 'personal' ? 'bg-lecto-bg-secondary' : ''}`}
                            >
                                <div className="w-8 h-8 bg-lecto-accent-primary/10 rounded-full flex items-center justify-center">
                                    <User className="w-4 h-4 text-lecto-accent-primary" />
                                </div>
                                <span className="font-medium text-lecto-text-primary">Личная библиотека</span>
                                {uploadTarget.type === 'personal' && <span className="ml-auto text-lecto-accent-primary">✓</span>}
                            </button>

                            {Array.isArray(folders) && folders.length > 0 && (
                                <>
                                    <div className="border-t border-lecto-border">
                                        <div className="px-3 py-2 text-xs text-lecto-text-secondary uppercase tracking-wider">Папки</div>
                                    </div>
                                    {folders.map((folder) => (
                                        <button
                                            key={folder.id}
                                            type="button"
                                            onClick={() => handleSelectTarget({ type: 'folder', id: folder.id, name: folder.name })}
                                            className={`w-full flex items-center gap-3 p-3 hover:bg-lecto-bg-secondary transition-colors ${uploadTarget.type === 'folder' && uploadTarget.id === folder.id ? 'bg-lecto-bg-secondary' : ''}`}
                                        >
                                            <div className="w-8 h-8 bg-lecto-accent-primary/10 rounded-full flex items-center justify-center">
                                                <Folder className="w-4 h-4 text-lecto-accent-primary" />
                                            </div>
                                            <span className="font-medium text-lecto-text-primary">{folder.name}</span>
                                            {uploadTarget.type === 'folder' && uploadTarget.id === folder.id && <span className="ml-auto text-lecto-accent-primary">✓</span>}
                                        </button>
                                    ))}
                                </>
                            )}

                            {Array.isArray(groups) && groups.length > 0 && (
                                <>
                                    <div className="border-t border-lecto-border">
                                        <div className="px-3 py-2 text-xs text-lecto-text-secondary uppercase tracking-wider">Группы</div>
                                    </div>
                                    {groups.map((group) => (
                                        <button
                                            key={group.id}
                                            type="button"
                                            onClick={() => handleSelectTarget({ type: 'group', id: group.id, name: group.name })}
                                            className={`w-full flex items-center gap-3 p-3 hover:bg-lecto-bg-secondary transition-colors ${uploadTarget.type === 'group' && uploadTarget.id === group.id ? 'bg-lecto-bg-secondary' : ''}`}
                                        >
                                            <div className="w-8 h-8 bg-lecto-accent-primary/10 rounded-full flex items-center justify-center">
                                                <Users className="w-4 h-4 text-lecto-accent-primary" />
                                            </div>
                                            <div className="flex-1 text-left">
                                                <span className="font-medium text-lecto-text-primary">{group.name}</span>
                                                <span className="text-xs text-lecto-text-secondary ml-2">{group.member_count} чел.</span>
                                            </div>
                                            {uploadTarget.type === 'group' && uploadTarget.id === group.id && <span className="text-lecto-accent-primary">✓</span>}
                                        </button>
                                    ))}
                                </>
                            )}
                        </div>
                    )}
                </div>

                {/* Mode Selector */}
                <div className="grid grid-cols-4 gap-2 mb-6">
                    <Button
                        variant={mode === 'file' ? 'primary' : 'primary'}
                        className="flex-1 px-2"
                        onClick={() => { setMode('file'); clearFile(); }}
                    >
                        <Upload className="w-4 h-4" />
                        <span className="hidden sm:inline ml-1">Файл</span>
                    </Button>
                    <Button
                        variant={mode === 'scan' ? 'primary' : 'primary'}
                        className="flex-1 px-2"
                        onClick={() => { setMode('scan'); clearFile(); }}
                    >
                        <Camera className="w-4 h-4" />
                        <span className="hidden sm:inline ml-1">Скан</span>
                    </Button>
                    <Button
                        variant={mode === 'text' ? 'primary' : 'primary'}
                        className="flex-1 px-2"
                        onClick={() => { setMode('text'); clearFile(); }}
                    >
                        <Type className="w-4 h-4" />
                        <span className="hidden sm:inline ml-1">Текст</span>
                    </Button>
                    <Button
                        variant={mode === 'topic' ? 'primary' : 'primary'}
                        className="flex-1 px-2"
                        onClick={() => { setMode('topic'); clearFile(); }}
                    >
                        <Sparkles className="w-4 h-4" />
                        <span className="hidden sm:inline ml-1">Тема</span>
                    </Button>
                </div>

                {/* File Upload */}
                {mode === 'file' && (
                    <div className="space-y-4">
                        <Card
                            variant="outlined"
                            className="border-dashed cursor-pointer hover:border-lecto-accent-primary transition-colors"
                            onClick={openFileSelector}
                        >
                            <div className="py-8 text-center">
                                {file ? (
                                    <>
                                        <FileText className="w-12 h-12 text-lecto-accent-primary mx-auto mb-2" />
                                        <p className="font-medium overflow-hidden text-ellipsis">{file.name}</p>
                                        <p className="text-sm text-lecto-text-secondary">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                    </>
                                ) : (
                                    <>
                                        <Upload className="w-12 h-12 text-lecto-accent-primary mx-auto mb-2" />
                                        <p className="text-lecto-text-secondary">Нажмите для выбора</p>
                                        <p className="text-xs text-le mt-1">PDF, DOCX, TXT (до 20 MB)</p>
                                    </>
                                )}
                            </div>
                        </Card>
                        <Input
                            label="Название (опционально)"
                            placeholder="Введите название"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                    </div>
                )}

                {/* Scan - НОВАЯ РЕАЛИЗАЦИЯ */}
                {mode === 'scan' && (
                    <div className="space-y-4">
                        {file && filePreview ? (
                            <Card variant="outlined" className="overflow-hidden">
                                <img
                                    src={filePreview}
                                    alt="Preview"
                                    className="w-full h-48 object-cover"
                                />
                                <div className="p-3 text-center">
                                    <p className="font-medium">Фото выбрано</p>
                                    <p className="text-sm text-tg-hint">
                                        {(file.size / 1024 / 1024).toFixed(2)} MB
                                    </p>
                                    <button
                                        onClick={clearFile}
                                        className="text-sm text-red-500 mt-2"
                                    >
                                        Удалить
                                    </button>
                                </div>
                            </Card>
                        ) : (
                            <div className="grid grid-cols-2 gap-3">
                                <Card
                                    variant="outlined"
                                    className="border-dashed cursor-pointer hover:border-lecto-accent-primary transition-colors active:scale-95"
                                    onClick={openCamera}
                                >
                                    <div className="py-6 text-center">
                                        <Camera className="w-10 h-10 text-lecto-accent-primary mx-auto mb-2" />
                                        <p className="font-medium text-sm">Камера</p>
                                        <p className="text-xs text-tg-hint mt-1">Сделать фото</p>
                                    </div>
                                </Card>

                                <Card
                                    variant="outlined"
                                    className="border-dashed cursor-pointer hover:border-lecto-accent-primary transition-colors active:scale-95"
                                    onClick={openGallery}
                                >
                                    <div className="py-6 text-center">
                                        <Image className="w-10 h-10 text-lecto-accent-primary mx-auto mb-2" />
                                        <p className="font-medium text-sm">Галерея</p>
                                        <p className="text-xs text-tg-hint mt-1">Выбрать фото</p>
                                    </div>
                                </Card>
                            </div>
                        )}

                        <Input
                            label="Название (опционально)"
                            placeholder="Тема лекции..."
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />

                        <p className="text-xs text-tg-hint">
                            <Lightbulb className="w-4 h-4 mr-2" /> AI распознает текст с фото
                        </p>
                    </div>
                )}

                {/* Text */}
                {mode === 'text' && (
                    <div className="space-y-4">
                        <Input
                            label="Название"
                            placeholder="Введите название"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                        <Textarea
                            label="Текст материала"
                            placeholder="Вставьте или введите текст..."
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            rows={8}
                        />
                    </div>
                )}

                {/* Topic */}
                {mode === 'topic' && (
                    <div className="space-y-4">
                        <div className="p-4 bg-gradient-to-r from-[#F3E8FF] to-[#E0E7FF] rounded-xl">
                            <div className="flex items-center gap-2 mb-2">
                                <Sparkles className="w-5 h-5 text-lecto-accent-primary" />
                                <span className="font-medium">AI Генерация</span>
                            </div>
                            <p className="text-sm text-tg-hint">
                                Введите название темы, и AI сгенерирует полный учебный материал
                            </p>
                        </div>
                        <Input
                            label="Название темы"
                            placeholder="Например: Квантовая физика..."
                            value={topicName}
                            onChange={(e) => setTopicName(e.target.value)}
                        />
                        <p className="text-xs text-tg-hint">
                            <Sparkles className="w-4 h-4 mr-2" /> AI создаст: конспект, тест (15-20 вопросов), глоссарий и карточки
                        </p>
                    </div>
                )}

                {/* Submit */}
                <Button
                    className="w-full mt-6"
                    size="lg"
                    onClick={handleSubmit}
                    isLoading={isLoading}
                    disabled={
                        mode === 'file' ? !file :
                            mode === 'scan' ? !file :
                                mode === 'text' ? !content.trim() :
                                    mode === 'topic' ? !topicName.trim() :
                                        true
                    }
                >
                    {mode === 'topic'
                        ? <><Sparkles className="w-4 h-4 mr-2" /> Сгенерировать</>
                        : uploadTarget.type === 'group'
                            ? <><Users className="w-4 h-4 mr-2" /> Загрузить</>
                            : mode === 'scan'
                                ? <><Camera className="w-4 h-4 mr-2" /> Сканировать</>
                                : '📤 Загрузить'
                    }
                </Button>
            </div>
        </div>
    );
}