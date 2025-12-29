// frontend/src/components/ui/Card.tsx
import type { HTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { clsx } from 'clsx';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'outlined' | 'modal';
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
    ({ className, variant = 'default', children, ...props }, ref) => {
        return (
            <div
                ref={ref}
                className={clsx(
                    'rounded-2xl p-4', 'border border-lecto-border',
                    {
                        'bg-lecto-bg-secondary': variant === 'default',
                        'border border-tg-hint/20 bg-transparent': variant === 'outlined',
                        'bg-lecto-bg-primary': variant === 'modal',
                    },
                    className
                )}
                {...props}
            >
                {children}
            </div>
        );
    }
);

Card.displayName = 'Card';