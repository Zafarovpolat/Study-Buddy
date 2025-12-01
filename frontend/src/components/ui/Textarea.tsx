// frontend/src/components/ui/Textarea.tsx
import type { TextareaHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { clsx } from 'clsx';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
    label?: string;
    error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className, label, error, ...props }, ref) => {
        return (
            <div className="w-full">
                {label && (
                    <label className="block text-sm font-medium text-tg-text mb-1">
                        {label}
                    </label>
                )}
                <textarea
                    ref={ref}
                    className={clsx(
                        'w-full px-4 py-3 rounded-xl resize-none',
                        'bg-tg-secondary text-tg-text',
                        'placeholder:text-tg-hint',
                        'focus:outline-none focus:ring-2 focus:ring-tg-button',
                        'transition-all',
                        error && 'ring-2 ring-red-500',
                        className
                    )}
                    {...props}
                />
                {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
            </div>
        );
    }
);

Textarea.displayName = 'Textarea';