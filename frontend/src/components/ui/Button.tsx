// frontend/src/components/ui/Button.tsx
import type { ButtonHTMLAttributes } from 'react';
import { forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
}

const variantClasses: Record<string, string> = {
    primary: 'bg-lecto-bg-secondary text-[#9452ea] hover:bg-[#E9D5FF]',
    secondary: 'bg-tg-secondary text-tg-text hover:opacity-80',
    ghost: 'bg-transparent text-tg-link hover:bg-tg-secondary',
    danger: 'bg-red-500 text-white hover:bg-red-600',
};

const sizeClasses: Record<string, string> = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
        const classes = [
            'inline-flex items-center justify-center rounded-xl font-medium transition-all',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'active:scale-[0.98]',
            variantClasses[variant],
            sizeClasses[size],
            className,
        ].filter(Boolean).join(' ');

        return (
            <button
                ref={ref}
                disabled={disabled || isLoading}
                className={classes}
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
