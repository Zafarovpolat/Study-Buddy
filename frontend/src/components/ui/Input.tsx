// frontend/src/components/ui/Input.tsx
import type { InputHTMLAttributes } from 'react';
import { forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ className, label, error, ...props }, ref) => {
        const classes = [
            'w-full px-4 py-3 rounded-xl',
            'bg-lecto-bg-secondary text-[#9452ea] hover:bg-[#E9D5FF]',
            'placeholder:text-tg-hint',
            'focus:outline-none focus:ring-2 focus:ring-lecto-accent-primary',
            'transition-all',
            error && 'ring-2 ring-red-500',
            className,
        ].filter(Boolean).join(' ');

        return (
            <div className="w-full">
                {label && (
                    <label className="block text-sm font-medium text-lecto-text-secondary mb-1">
                        {label}
                    </label>
                )}
                <input
                    ref={ref}
                    className={classes}
                    {...props}
                />
                {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
            </div>
        );
    }
);

Input.displayName = 'Input';
