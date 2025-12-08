// frontend/src/components/UploadModal.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { useState, useRef, useEffect } from 'react';
import { X, Upload, FileText, Type, Camera, Image, ChevronDown, Users, User } from 'lucide-react';
import { Button, Input, Textarea, Card } from './ui';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';

interface UploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    folderId?: string;
    groupId?: string;  // Предустановленная группа (если открыли из группы)
}

type UploadMode = 'file' | 'text' | 'scan';
type UploadTarget = { type: 'personal'; id?: string } | { type: 'group'; id: string; name: string };

export function UploadModal({ isOpen, onClose, folderId, groupId: initialGroupId }: UploadModalProps) {
    const [mode, setMode] = useState<UploadMode>('file');
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [showTargetDropdown, setShowTargetDropdown] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);
    const cameraInputRef = useRef<HTMLInputElement>(null);
    const galleryInputRef = useRef<HTMLInputElement>(null);

    const { groups, addMaterial, setLimits } = useStore();

    // Определяем начальную цель загрузки
    const getInitialTarget = (): UploadTarget => {
        if (initialGroupId) {
            const group = groups.find(g => g.id === initialGroupId);
            if (group) {
                return { type: 'group', id: group.id, name: group.name };
            }
        }
        return { type: 'personal' };
    };

    const [uploadTarget, setUploadTarget] = useState<UploadTarget>(getInitialTarget);

    // Обновляем target при изменении initialGroupId
    useEffect(() => {
        setUploadTarget(getInitialTarget());
    }, [initialGroupId, groups]);

    if (!isOpen) return null;

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
            if (!title) {
                setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
            }
        }
    };

    const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
            if (!title) {
                setTitle('Скан: ' + new Date().toLocaleDateString('ru-RU'));
            }
        }
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

            const targetGroupId = uploadTarget.type === 'group' ? uploadTarget.id : undefined;
            let material;

            if (mode === 'file' && file) {
                material = await api.uploadFile(file, title || file.name, folderId, targetGroupId);
            } else if (mode === 'scan' && file) {
                material = await api.scanImage(file, title || 'Скан', folderId, targetGroupId);
            } else if (mode === 'text' && content.trim()) {
                material = await api.createTextMaterial(
                    title || 'Без названия',
                    content,
                    folderId,
                    targetGroupId
                );
            } else {
                telegram.alert('Добавьте файл или текст');
                return;
            }

            addMaterial(material);

            const limits = await api.getMyLimits();
            setLimits(limits);

            telegram.haptic('success');

            // Показываем уведомление об успехе
            const targetName = uploadTarget.type === 'group'
                ? `группу "${uploadTarget.name}"`
                : 'личную библиотеку';
            telegram.showPopup({
                title: '✅ Готово!',
                message: `Материал загружен в ${targetName}`,
                buttons: [{ type: 'ok' }]
            });

            onClose();
            resetForm();
        } catch (error: any) {
            telegram.haptic('error');
            telegram.alert(error.response?.data?.detail || 'Ошибка загрузки');
        } finally {
            setIsLoading(false);
        }
    };

    const resetForm = () => {
        setTitle('');
        setContent('');
        setFile(null);
        setMode('file');
        setUploadTarget(getInitialTarget());
        setShowTargetDropdown(false);
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-end justify-center">
            <div className="bg-tg-bg w-full max-w-lg rounded-t-3xl p-6 max-h-[90vh] overflow-y-auto animate-slide-up">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold">Новый материал</h2>
                    <button
                        onClick={() => { resetForm(); onClose(); }}
                        className="p-2 hover:bg-tg-secondary rounded-full transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* ===== DROPDOWN ВЫБОРА МЕСТА ЗАГРУЗКИ ===== */}
                <div className="mb-4 relative">
                    <label className="block text-sm font-medium text-tg-hint mb-2">
                        Загрузить в:
                    </label>
                    <button
                        type="button"
                        onClick={() => setShowTargetDropdown(!showTargetDropdown)}
                        className="w-full flex items-center justify-between p-3 bg-tg-secondary rounded-xl border border-transparent hover:border-tg-button transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            {uploadTarget.type === 'personal' ? (
                                <>
                                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                                        <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                                    </div>
                                    <span className="font-medium">Личная библиотека</span>
                                </>
                            ) : (
                                <>
                                    <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
                                        <Users className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                                    </div>
                                    <span className="font-medium">{uploadTarget.name}</span>
                                </>
                            )}
                        </div>
                        <ChevronDown className={`w-5 h-5 text-tg-hint transition-transform ${showTargetDropdown ? 'rotate-180' : ''}`} />
                    </button>

                    {/* Dropdown Menu */}
                    {showTargetDropdown && (
                        <div className="absolute top-full left-0 right-0 mt-2 bg-tg-bg border border-tg-secondary rounded-xl shadow-lg z-10 overflow-hidden">
                            {/* Личная библиотека */}
                            <button
                                type="button"
                                onClick={() => handleSelectTarget({ type: 'personal' })}
                                className={`w-full flex items-center gap-3 p-3 hover:bg-tg-secondary transition-colors ${uploadTarget.type === 'personal' ? 'bg-tg-secondary' : ''
                                    }`}
                            >
                                <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                                    <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                                </div>
                                <span className="font-medium">Личная библиотека</span>
                                {uploadTarget.type === 'personal' && (
                                    <span className="ml-auto text-tg-button">✓</span>
                                )}
                            </button>

                            {/* Разделитель если есть группы */}
                            {groups.length > 0 && (
                                <div className="border-t border-tg-secondary">
                                    <div className="px-3 py-2 text-xs text-tg-hint uppercase tracking-wider">
                                        Группы
                                    </div>
                                </div>
                            )}

                            {/* Список групп */}
                            {groups.map((group) => (
                                <button
                                    key={group.id}
                                    type="button"
                                    onClick={() => handleSelectTarget({ type: 'group', id: group.id, name: group.name })}
                                    className={`w-full flex items-center gap-3 p-3 hover:bg-tg-secondary transition-colors ${uploadTarget.type === 'group' && uploadTarget.id === group.id ? 'bg-tg-secondary' : ''
                                        }`}
                                >
                                    <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
                                        <Users className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                                    </div>
                                    <div className="flex-1 text-left">
                                        <span className="font-medium">{group.name}</span>
                                        <span className="text-xs text-tg-hint ml-2">
                                            {group.member_count} чел.
                                        </span>
                                    </div>
                                    {uploadTarget.type === 'group' && uploadTarget.id === group.id && (
                                        <span className="text-tg-button">✓</span>
                                    )}
                                </button>
                            ))}

                            {/* Если нет групп */}
                            {groups.length === 0 && (
                                <div className="p-3 text-center text-tg-hint text-sm">
                                    У вас пока нет групп
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Mode Selector */}
                <div className="flex gap-2 mb-6">
                    <Button
                        variant={mode === 'file' ? 'primary' : 'secondary'}
                        className="flex-1"
                        onClick={() => { setMode('file'); setFile(null); }}
                    >
                        <Upload className="w-4 h-4 mr-1" />
                        Файл
                    </Button>
                    <Button
                        variant={mode === 'scan' ? 'primary' : 'secondary'}
                        className="flex-1"
                        onClick={() => { setMode('scan'); setFile(null); }}
                    >
                        <Camera className="w-4 h-4 mr-1" />
                        Скан
                    </Button>
                    <Button
                        variant={mode === 'text' ? 'primary' : 'secondary'}
                        className="flex-1"
                        onClick={() => { setMode('text'); setFile(null); }}
                    >
                        <Type className="w-4 h-4 mr-1" />
                        Текст
                    </Button>
                </div>

                {/* File Upload */}
                {mode === 'file' && (
                    <div className="space-y-4">
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".pdf,.docx,.doc,.txt"
                            onChange={handleFileSelect}
                            className="hidden"
                        />

                        <Card
                            variant="outlined"
                            className="border-dashed cursor-pointer hover:border-tg-button transition-colors"
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <div className="py-8 text-center">
                                {file ? (
                                    <>
                                        <FileText className="w-12 h-12 text-tg-button mx-auto mb-2" />
                                        <p className="font-medium">{file.name}</p>
                                        <p className="text-sm text-tg-hint">
                                            {(file.size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                    </>
                                ) : (
                                    <>
                                        <Upload className="w-12 h-12 text-tg-hint mx-auto mb-2" />
                                        <p className="text-tg-hint">Нажмите для выбора</p>
                                        <p className="text-xs text-tg-hint mt-1">
                                            PDF, DOCX, TXT (до 20 MB)
                                        </p>
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

                {/* Scan */}
                {mode === 'scan' && (
                    <div className="space-y-4">
                        <input
                            ref={cameraInputRef}
                            type="file"
                            accept="image/*"
                            capture="environment"
                            onChange={handleImageSelect}
                            className="hidden"
                        />
                        <input
                            ref={galleryInputRef}
                            type="file"
                            accept="image/jpeg,image/jpg,image/png,image/webp"
                            onChange={handleImageSelect}
                            className="hidden"
                        />

                        {file ? (
                            <Card variant="outlined" className="overflow-hidden">
                                <img
                                    src={URL.createObjectURL(file)}
                                    alt="Preview"
                                    className="w-full h-48 object-cover"
                                />
                                <div className="p-3 text-center">
                                    <p className="font-medium">Фото выбрано</p>
                                    <p className="text-sm text-tg-hint">
                                        {(file.size / 1024 / 1024).toFixed(2)} MB
                                    </p>
                                    <button
                                        onClick={() => setFile(null)}
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
                                    className="border-dashed cursor-pointer hover:border-tg-button transition-colors"
                                    onClick={() => cameraInputRef.current?.click()}
                                >
                                    <div className="py-6 text-center">
                                        <Camera className="w-10 h-10 text-tg-button mx-auto mb-2" />
                                        <p className="font-medium text-sm">Камера</p>
                                    </div>
                                </Card>

                                <Card
                                    variant="outlined"
                                    className="border-dashed cursor-pointer hover:border-tg-button transition-colors"
                                    onClick={() => galleryInputRef.current?.click()}
                                >
                                    <div className="py-6 text-center">
                                        <Image className="w-10 h-10 text-tg-button mx-auto mb-2" />
                                        <p className="font-medium text-sm">Галерея</p>
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
                            💡 AI распознает текст с фото
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

                {/* Submit */}
                <Button
                    className="w-full mt-6"
                    size="lg"
                    onClick={handleSubmit}
                    isLoading={isLoading}
                    disabled={
                        mode === 'file' ? !file :
                            mode === 'scan' ? !file :
                                !content.trim()
                    }
                >
                    {uploadTarget.type === 'group'
                        ? `👥 Загрузить в "${uploadTarget.name}"`
                        : mode === 'scan'
                            ? '📷 Сканировать'
                            : '📤 Загрузить'
                    }
                </Button>
            </div>
        </div>
    );
}