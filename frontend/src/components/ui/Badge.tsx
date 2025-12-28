import { forwardRef, type HTMLAttributes } from 'react';
import { clsx } from 'clsx';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
    variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'gold';
    size?: 'sm' | 'md';
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
    ({ className, variant = 'default', size = 'sm', children, ...props }, ref) => {
        return (
            <span
                ref={ref}
                className={clsx(
                    'inline-flex items-center font-medium rounded-full',
                    {
                        // Sizes
                        'px-2 py-0.5 text-xs': size === 'sm',
                        'px-3 py-1 text-sm': size === 'md',
                        // Variants
                        'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300': variant === 'default',
                        'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400': variant === 'success',
                        'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400': variant === 'warning',
                        'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400': variant === 'danger',
                        'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400': variant === 'info',
                        'bg-gradient-to-r from-yellow-400 to-orange-400 text-black': variant === 'gold',
                    },
                    className
                )}
                {...props}
            >
                {children}
            </span>
        );
    }
);

Badge.displayName = 'Badge';