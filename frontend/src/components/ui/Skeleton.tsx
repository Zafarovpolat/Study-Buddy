import { clsx } from 'clsx';

interface SkeletonProps {
    className?: string;
    variant?: 'text' | 'circular' | 'rectangular';
    width?: string | number;
    height?: string | number;
}

export function Skeleton({
    className,
    variant = 'rectangular',
    width,
    height
}: SkeletonProps) {
    return (
        <div
            className={clsx(
                'animate-shimmer',
                {
                    'rounded': variant === 'text',
                    'rounded-full': variant === 'circular',
                    'rounded-xl': variant === 'rectangular',
                },
                className
            )}
            style={{
                width: width,
                height: height || (variant === 'text' ? '1em' : undefined)
            }}
        />
    );
}

// Предустановленные скелетоны
export function SkeletonCard() {
    return (
        <div className="bg-lecto-bg-secondary rounded-2xl p-4 space-y-3">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
        </div>
    );
}

export function SkeletonMaterialCard() {
    return (
        <div className="bg-lecto-bg-secondary rounded-2xl p-4 flex gap-3">
            <Skeleton variant="rectangular" className="w-12 h-12 flex-shrink-0" />
            <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-3 w-1/4" />
            </div>
        </div>
    );
}