// frontend/src/components/UploadModal.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { useState, useRef } from 'react';
import { X, Upload, FileText, Type, Camera } from 'lucide-react';
import { Button, Input, Textarea, Card } from './ui';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';

interface UploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    folderId?: string;
}

type UploadMode = 'file' | 'text' | 'scan';

export function UploadModal({ isOpen, onClose, folderId }: UploadModalProps) {
    const [mode, setMode] = useState<UploadMode>('file');
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const imageInputRef = useRef<HTMLInputElement>(null);

    const { addMaterial, setLimits } = useStore();

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

    const handleSubmit = async () => {
        try {
            setIsLoading(true);
            telegram.haptic('medium');

            let material;

            if (mode === 'file' && file) {
                material = await api.uploadFile(file, title || file.name, folderId);
            } else if (mode === 'scan' && file) {
                material = await api.scanImage(file, title || 'Скан', folderId);
            } else if (mode === 'text' && content.trim()) {
                material = await api.createTextMaterial(
                    title || 'Без названия',
                    content,
                    folderId
                );
            } else {
                telegram.alert('Добавьте файл или текст');
                return;
            }

            addMaterial(material);

            const limits = await api.getMyLimits();
            setLimits(limits);

            telegram.haptic('success');
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
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-end justify-center">
            <div className="bg-tg-bg w-full max-w-lg rounded-t-3xl p-6 max-h-[90vh] overflow-y-auto animate-slide-up">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold">Новый материал</h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-tg-secondary rounded-full transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Mode Selector - 3 кнопки */}
                <div className="flex gap-2 mb-6">
                    <Button
                        variant={mode === 'file' ? 'primary' : 'secondary'}
                        className="flex-1"
                        onClick={() => setMode('file')}
                    >
                        <Upload className="w-4 h-4 mr-1" />
                        Файл
                    </Button>
                    <Button
                        variant={mode === 'scan' ? 'primary' : 'secondary'}
                        className="flex-1"
                        onClick={() => setMode('scan')}
                    >
                        <Camera className="w-4 h-4 mr-1" />
                        Скан
                    </Button>
                    <Button
                        variant={mode === 'text' ? 'primary' : 'secondary'}
                        className="flex-1"
                        onClick={() => setMode('text')}
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

                {/* Scan (Image) */}
                {mode === 'scan' && (
                    <div className="space-y-4">
                        <input
                            ref={imageInputRef}
                            type="file"
                            accept="image/jpeg,image/jpg,image/png,image/webp"
                            capture="environment"
                            onChange={handleImageSelect}
                            className="hidden"
                        />

                        <Card
                            variant="outlined"
                            className="border-dashed cursor-pointer hover:border-tg-button transition-colors"
                            onClick={() => imageInputRef.current?.click()}
                        >
                            <div className="py-8 text-center">
                                {file ? (
                                    <>
                                        <img
                                            src={URL.createObjectURL(file)}
                                            alt="Preview"
                                            className="w-32 h-32 object-cover mx-auto mb-2 rounded-lg"
                                        />
                                        <p className="font-medium">Фото выбрано</p>
                                        <p className="text-sm text-tg-hint">
                                            {(file.size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                    </>
                                ) : (
                                    <>
                                        <Camera className="w-12 h-12 text-tg-hint mx-auto mb-2" />
                                        <p className="text-tg-hint">Сфотографируйте доску</p>
                                        <p className="text-xs text-tg-hint mt-1">
                                            или выберите фото из галереи
                                        </p>
                                    </>
                                )}
                            </div>
                        </Card>

                        <Input
                            label="Название (опционально)"
                            placeholder="Тема лекции..."
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />

                        <p className="text-xs text-tg-hint">
                            💡 AI распознает текст с фото и создаст конспект
                        </p>
                    </div>
                )}

                {/* Text Input */}
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

                {/* Submit Button */}
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
                    {mode === 'scan' ? '📷 Сканировать' : '📤 Загрузить'}
                </Button>
            </div>
        </div>
    );
}