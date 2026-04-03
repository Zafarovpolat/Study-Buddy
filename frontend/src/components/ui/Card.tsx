// frontend/src/components/ui/Card.tsx
import type { HTMLAttributes } from 'react';
import { forwardRef } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'outlined' | 'modal';
}

const variantClasses: Record<string, string> = {
    default: 'bg-lecto-bg-secondary',
    outlined: 'border border-tg-hint/20 bg-transparent',
    modal: 'bg-lecto-bg-primary',
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
    ({ className, variant = 'default', children, ...props }, ref) => {
        const classes = [
            'rounded-2xl p-4',
            'border border-lecto-border',
            variantClasses[variant],
            className,
        ].filter(Boolean).join(' ');

        return (
            <div
                ref={ref}
                className={classes}
                {...props}
            >
                {children}
            </div>
        );
    }
);

Card.displayName = 'Card';
