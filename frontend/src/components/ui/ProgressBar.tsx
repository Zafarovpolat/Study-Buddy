interface ProgressBarProps {
    value: number;
    max?: number;
    variant?: 'default' | 'success' | 'gold';
    size?: 'sm' | 'md' | 'lg';
    showLabel?: boolean;
    className?: string;
}

const sizeMap: Record<string, string> = { sm: 'h-1', md: 'h-2', lg: 'h-3' };
const variantMap: Record<string, string> = {
    default: 'bg-lecto-accent-blue',
    success: 'bg-lecto-accent-green',
    gold: 'bg-gradient-to-r from-yellow-400 to-orange-400',
};

export function ProgressBar({
    value,
    max = 100,
    variant = 'default',
    size = 'md',
    showLabel = false,
    className
}: ProgressBarProps) {
    const percentage = Math.min(100, Math.max(0, (value / max) * 100));

    return (
        <div className={`w-full ${className || ''}`}>
            <div className={`w-full bg-lecto-bg-tertiary rounded-full overflow-hidden ${sizeMap[size]}`}>
                <div
                    className={`h-full rounded-full transition-all duration-500 ease-out ${variantMap[variant]}`}
                    style={{ width: `${percentage}%` }}
                />
            </div>
            {showLabel && (
                <div className="flex justify-between mt-1 text-xs text-lecto-text-secondary">
                    <span>{value}</span>
                    <span>{max}</span>
                </div>
            )}
        </div>
    );
}
