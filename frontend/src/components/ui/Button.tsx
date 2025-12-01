// frontend/src/components/ui/Button.tsx
import type { ButtonHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { clsx } from 'clsx';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
        return (
            <button
                ref={ref}
                disabled={disabled || isLoading}
                className={clsx(
                    'inline-flex items-center justify-center rounded-xl font-medium transition-all',
                    'disabled:opacity-50 disabled:cursor-not-allowed',
                    'active:scale-[0.98]',
                    {
                        'bg-tg-button text-tg-button-text hover:opacity-90': variant === 'primary',
                        'bg-tg-secondary text-tg-text hover:opacity-80': variant === 'secondary',
                        'bg-transparent text-tg-link hover:bg-tg-secondary': variant === 'ghost',
                        'bg-red-500 text-white hover:bg-red-600': variant === 'danger',
                    },
                    {
                        'px-3 py-1.5 text-sm': size === 'sm',
                        'px-4 py-2 text-base': size === 'md',
                        'px-6 py-3 text-lg': size === 'lg',
                    },
                    className
                )}
                {...props}
            >
                {isLoading ? (
                    <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                        <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                        />
                        <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                    </svg>
                ) : null}
                {children}
            </button>
        );
    }
);

Button.displayName = 'Button';