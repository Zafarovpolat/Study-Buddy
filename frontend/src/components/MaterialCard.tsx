// frontend/src/components/MaterialCard.tsx
import { FileText, Image, File, Loader2, MoreVertical } from 'lucide-react';
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
    pdf: <FileText className="w-6 h-6 text-red-500" />,
    docx: <FileText className="w-6 h-6 text-blue-500" />,
    txt: <FileText className="w-6 h-6 text-gray-500" />,
    image: <Image className="w-6 h-6 text-green-500" />,
    default: <File className="w-6 h-6 text-tg-hint" />,
};

export function MaterialCard({
    material,
    onClick,
    onUpdate,
    onDelete,
    showActions = true
}: MaterialCardProps) {
    const icon = typeIcons[material.material_type] || typeIcons.default;

    const formatDate = (dateString: string) => {
        const isoString = dateString.endsWith('Z') ? dateString : dateString + 'Z';
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'только что';
        if (diffMins < 60) return `${diffMins} мин`;
        if (diffHours < 24) return `${diffHours} ч`;
        if (diffDays < 7) return `${diffDays} дн`;
        return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
    };

    // Можно кликать даже если processing — откроется страница с прогрессом
    const isClickable = material.status !== 'pending';

    return (
        <Card
            className={`flex items-start gap-4 p-4 transition-all relative ${isClickable
                ? 'cursor-pointer hover:bg-lecto-bg-secondary/80 active:scale-[0.99]'
                : 'opacity-70'
                } ${material.status === 'processing' ? 'animate-pulse' : ''}`}
            onClick={isClickable ? onClick : undefined}
        >
            {/* Icon Container */}
            <div className="relative flex-shrink-0 w-12 h-12 bg-lecto-bg-tertiary rounded-xl flex items-center justify-center">
                {material.status === 'processing' ? (
                    <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                ) : (
                    icon
                )}

                {/* Status Dot (Green for completed) */}
                {material.status === 'completed' && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-lecto-bg-primary opacity-80" />
                )}

                {/* Error Dot */}
                {material.status === 'failed' && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-lecto-bg-primary" />
                )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 flex flex-col justify-between min-h-[3rem]">
                <h3 className="font-medium text-lecto-text-primary leading-tight line-clamp-2 pr-6">
                    {material.title}
                </h3>

                <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-lecto-text-secondary uppercase tracking-wider font-medium opacity-60">
                        {material.material_type}
                    </span>
                    <span className="text-xs text-lecto-text-secondary">
                        {formatDate(material.created_at)}
                    </span>
                </div>
            </div>

            {/* Actions (Absolute positioning or just right aligned) */}
            {showActions && material.status === 'completed' && onUpdate && onDelete && (
                <div className="absolute top-3 right-2" onClick={(e) => e.stopPropagation()}>
                    <MaterialActions
                        material={material}
                        onUpdate={onUpdate}
                        onDelete={onDelete}
                    >
                        <button className="p-1 text-lecto-text-secondary hover:text-lecto-text-primary transition-colors">
                            <MoreVertical className="w-5 h-5" />
                        </button>
                    </MaterialActions>
                </div>
            )}
        </Card>
    );
}