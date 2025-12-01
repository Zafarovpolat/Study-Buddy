import { FileText, Image, Music, File, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Card } from './ui';
import { telegram } from '../lib/telegram';

interface Material {
    id: string;
    title: string;
    material_type: string;
    status: string;
    created_at: string;
}

interface MaterialCardProps {
    material: Material;
    onClick: () => void;
}

const typeIcons: Record<string, typeof FileText> = {
    pdf: FileText,
    docx: FileText,
    txt: FileText,
    image: Image,
    audio: Music,
};

const statusConfig: Record<string, { icon: typeof Clock; color: string; text: string }> = {
    pending: { icon: Clock, color: 'text-yellow-500', text: 'Ожидает' },
    processing: { icon: Loader2, color: 'text-blue-500', text: 'Обработка...' },
    completed: { icon: CheckCircle, color: 'text-green-500', text: 'Готово' },
    failed: { icon: XCircle, color: 'text-red-500', text: 'Ошибка' },
};

export function MaterialCard({ material, onClick }: MaterialCardProps) {
    const TypeIcon = typeIcons[material.material_type] || File;
    const status = statusConfig[material.status] || statusConfig.pending;
    const StatusIcon = status.icon;

    const handleClick = () => {
        telegram.haptic('light');
        onClick();
    };

    return (
        <Card
            className="cursor-pointer active:scale-[0.98] transition-transform"
            onClick={handleClick}
        >
            <div className="flex items-start gap-3">
                <div className="p-2 bg-tg-button/10 rounded-xl">
                    <TypeIcon className="w-6 h-6 text-tg-button" />
                </div>

                <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-tg-text truncate">{material.title}</h3>

                    <div className="flex items-center gap-2 mt-1">
                        <StatusIcon
                            className={`w-4 h-4 ${status.color} ${material.status === 'processing' ? 'animate-spin' : ''
                                }`}
                        />
                        <span className={`text-xs ${status.color}`}>{status.text}</span>
                    </div>
                </div>

                <span className="text-xs text-tg-hint">
                    {new Date(material.created_at).toLocaleDateString('ru-RU', {
                        day: 'numeric',
                        month: 'short',
                    })}
                </span>
            </div>
        </Card>
    );
}