// frontend/src/components/ui/Card.tsx
import type { HTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { clsx } from 'clsx';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'outlined';
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
    ({ className, variant = 'default', children, ...props }, ref) => {
        return (
            <div
                ref={ref}
                className={clsx(
                    'rounded-2xl p-4',
                    {
                        'bg-tg-secondary': variant === 'default',
                        'border border-tg-hint/20 bg-transparent': variant === 'outlined',
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