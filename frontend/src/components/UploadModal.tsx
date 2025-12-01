import { useState, useRef } from 'react';
import { X, Upload, FileText, Type } from 'lucide-react';
import { Button, Input, Textarea, Card } from './ui';
import { api } from '../lib/api';
import { useStore } from '../store/useStore';
import { telegram } from '../lib/telegram';

interface UploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    folderId?: string;
}

type UploadMode = 'file' | 'text';

export function UploadModal({ isOpen, onClose, folderId }: UploadModalProps) {
    const [mode, setMode] = useState<UploadMode>('file');
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

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

    const handleSubmit = async () => {
        try {
            setIsLoading(true);
            telegram.haptic('medium');

            let material;

            if (mode === 'file' && file) {
                material = await api.uploadFile(file, title || file.name, folderId);
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

            // Обновляем лимиты
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

                {/* Mode Selector */}
                <div className="flex gap-2 mb-6">
                    <Button
                        variant={mode === 'file' ? 'primary' : 'secondary'}
                        className="flex-1"
                        onClick={() => setMode('file')}
                    >
                        <Upload className="w-4 h-4 mr-2" />
                        Файл
                    </Button>
                    <Button
                        variant={mode === 'text' ? 'primary' : 'secondary'}
                        className="flex-1"
                        onClick={() => setMode('text')}
                    >
                        <Type className="w-4 h-4 mr-2" />
                        Текст
                    </Button>
                </div>

                {/* File Upload */}
                {mode === 'file' && (
                    <div className="space-y-4">
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg"
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
                                        <p className="text-tg-hint">
                                            Нажмите для выбора файла
                                        </p>
                                        <p className="text-xs text-tg-hint mt-1">
                                            PDF, DOCX, TXT, PNG, JPG (до 20 MB)
                                        </p>
                                    </>
                                )}
                            </div>
                        </Card>

                        <Input
                            label="Название (опционально)"
                            placeholder="Введите название материала"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
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
                    disabled={mode === 'file' ? !file : !content.trim()}
                >
                    Загрузить и обработать
                </Button>
            </div>
        </div>
    );
}