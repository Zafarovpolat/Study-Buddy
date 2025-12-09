// frontend/src/components/MaterialCard.tsx - ЗАМЕНИ ПОЛНОСТЬЮ
import { FileText, Image, File, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Card } from './ui';
import { MaterialActions } from './MaterialActions';

interface Material {
    id: string;
    title: string;
    material_type: string;
    status: string;
    created_at: string;
    folder_id?: string;
}

interface MaterialCardProps {
    material: Material;
    onClick: () => void;
    onUpdate?: () => void;
    onDelete?: () => void;
    showActions?: boolean;
}

const typeIcons: Record<string, React.ReactNode> = {
    pdf: <FileText className="w-5 h-5 text-red-500" />,
    docx: <FileText className="w-5 h-5 text-blue-500" />,
    txt: <FileText className="w-5 h-5 text-gray-500" />,
    image: <Image className="w-5 h-5 text-green-500" />,
    default: <File className="w-5 h-5 text-tg-hint" />,
};

const statusConfig: Record<string, { icon: React.ReactNode; text: string; className: string }> = {
    pending: {
        icon: <Clock className="w-4 h-4" />,
        text: 'Ожидает',
        className: 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/30',
    },
    processing: {
        icon: <Loader2 className="w-4 h-4 animate-spin" />,
        text: 'Обработка',
        className: 'text-blue-500 bg-blue-100 dark:bg-blue-900/30',
    },
    completed: {
        icon: <CheckCircle className="w-4 h-4" />,
        text: 'Готово',
        className: 'text-green-500 bg-green-100 dark:bg-green-900/30',
    },
    failed: {
        icon: <XCircle className="w-4 h-4" />,
        text: 'Ошибка',
        className: 'text-red-500 bg-red-100 dark:bg-red-900/30',
    },
};

export function MaterialCard({
    material,
    onClick,
    onUpdate,
    onDelete,
    showActions = true
}: MaterialCardProps) {
    const icon = typeIcons[material.material_type] || typeIcons.default;
    const status = statusConfig[material.status] || statusConfig.pending;

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'только что';
        if (diffMins < 60) return `${diffMins} мин назад`;
        if (diffHours < 24) return `${diffHours} ч назад`;
        if (diffDays < 7) return `${diffDays} дн назад`;
        return date.toLocaleDateString('ru-RU');
    };

    return (
        <Card
            className="flex items-center gap-3 p-4 cursor-pointer hover:bg-tg-secondary/50 active:scale-[0.99] transition-all"
            onClick={onClick}
        >
            {/* Icon */}
            <div className="flex-shrink-0 w-10 h-10 bg-tg-secondary rounded-lg flex items-center justify-center">
                {icon}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
                <h3 className="font-medium truncate">{material.title}</h3>
                <div className="flex items-center gap-2 mt-1">
                    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${status.className}`}>
                        {status.icon}
                        {status.text}
                    </span>
                    <span className="text-xs text-tg-hint">
                        {formatDate(material.created_at)}
                    </span>
                </div>
            </div>

            {/* Actions */}
            {showActions && onUpdate && onDelete && (
                <MaterialActions
                    material={material}
                    onUpdate={onUpdate}
                    onDelete={onDelete}
                />
            )}
        </Card>
    );
}