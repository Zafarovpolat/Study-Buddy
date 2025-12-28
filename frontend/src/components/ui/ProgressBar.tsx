import { clsx } from 'clsx';

interface ProgressBarProps {
    value: number;
    max?: number;
    variant?: 'default' | 'success' | 'gold';
    size?: 'sm' | 'md' | 'lg';
    showLabel?: boolean;
    className?: string;
}

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
        <div className={clsx('w-full', className)}>
            <div
                className={clsx(
                    'w-full bg-lecto-bg-tertiary rounded-full overflow-hidden',
                    {
                        'h-1': size === 'sm',
                        'h-2': size === 'md',
                        'h-3': size === 'lg',
                    }
                )}
            >
                <div
                    className={clsx(
                        'h-full rounded-full transition-all duration-500 ease-out',
                        {
                            'bg-lecto-accent-blue': variant === 'default',
                            'bg-lecto-accent-green': variant === 'success',
                            'bg-gradient-to-r from-yellow-400 to-orange-400': variant === 'gold',
                        }
                    )}
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