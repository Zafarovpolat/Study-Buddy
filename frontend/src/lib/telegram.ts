// frontend/src/lib/telegram.ts - ЗАМЕНИ ПОЛНОСТЬЮ
declare global {
    interface Window {
        Telegram?: {
            WebApp: TelegramWebApp;
        };
    }
}

interface TelegramWebApp {
    initData: string;
    initDataUnsafe: {
        user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
            language_code?: string;
        };
        start_param?: string;
    };
    version: string;
    platform: string;
    colorScheme: 'light' | 'dark';
    themeParams: {
        bg_color?: string;
        text_color?: string;
        hint_color?: string;
        link_color?: string;
        button_color?: string;
        button_text_color?: string;
        secondary_bg_color?: string;
    };
    isExpanded: boolean;
    viewportHeight: number;
    viewportStableHeight: number;
    ready: () => void;
    expand: () => void;
    close: () => void;
    MainButton: any;
    BackButton: any;
    HapticFeedback: any;
    showAlert: (message: string, callback?: () => void) => void;
    showConfirm: (message: string, callback?: (confirmed: boolean) => void) => void;
    showPopup: (params: any, callback?: (buttonId: string) => void) => void;
    setHeaderColor: (color: string) => void;
    setBackgroundColor: (color: string) => void;
}

class TelegramService {
    private webApp: TelegramWebApp | null = null;
    private isRealTelegram: boolean = false;

    constructor() {
        if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
            this.webApp = window.Telegram.WebApp;
            // Проверяем что это реальный Telegram, а не просто загруженный скрипт
            this.isRealTelegram = !!(this.webApp.initData && this.webApp.initData.length > 0);
        }
    }

    get isAvailable(): boolean {
        return this.isRealTelegram;
    }

    get app(): TelegramWebApp | null {
        return this.webApp;
    }

    get user() {
        return this.webApp?.initDataUnsafe.user || null;
    }

    get initData(): string {
        return this.webApp?.initData || '';
    }

    get isDarkMode(): boolean {
        if (this.isRealTelegram) {
            return this.webApp?.colorScheme === 'dark';
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    init() {
        if (this.webApp && this.isRealTelegram) {
            try {
                this.webApp.ready();
                this.webApp.expand();
                this.applyTheme();
            } catch (e) {
                console.log('Telegram init error (expected in browser):', e);
            }
        }
    }

    private applyTheme() {
        if (!this.webApp || !this.isRealTelegram) return;

        const theme = this.webApp.themeParams;
        const root = document.documentElement;

        if (theme.bg_color) root.style.setProperty('--tg-theme-bg-color', theme.bg_color);
        if (theme.text_color) root.style.setProperty('--tg-theme-text-color', theme.text_color);
        if (theme.hint_color) root.style.setProperty('--tg-theme-hint-color', theme.hint_color);
        if (theme.link_color) root.style.setProperty('--tg-theme-link-color', theme.link_color);
        if (theme.button_color) root.style.setProperty('--tg-theme-button-color', theme.button_color);
        if (theme.button_text_color) root.style.setProperty('--tg-theme-button-text-color', theme.button_text_color);
        if (theme.secondary_bg_color) root.style.setProperty('--tg-theme-secondary-bg-color', theme.secondary_bg_color);
    }

    // Haptic feedback - безопасный вызов
    haptic(type: 'light' | 'medium' | 'heavy' | 'success' | 'error' | 'warning' | 'selection') {
        if (!this.isRealTelegram || !this.webApp?.HapticFeedback) return;

        try {
            if (type === 'selection') {
                this.webApp.HapticFeedback.selectionChanged();
            } else if (['success', 'error', 'warning'].includes(type)) {
                this.webApp.HapticFeedback.notificationOccurred(type as 'success' | 'error' | 'warning');
            } else {
                this.webApp.HapticFeedback.impactOccurred(type as 'light' | 'medium' | 'heavy');
            }
        } catch (e) {
            // Игнорируем ошибки haptic в браузере
        }
    }

    // Main Button - безопасный вызов
    showMainButton(text: string, onClick: () => void) {
        if (!this.isRealTelegram || !this.webApp?.MainButton) return;

        try {
            this.webApp.MainButton.setText(text);
            this.webApp.MainButton.onClick(onClick);
            this.webApp.MainButton.show();
        } catch (e) {
            console.log('MainButton not supported');
        }
    }

    hideMainButton() {
        if (!this.isRealTelegram) return;
        try {
            this.webApp?.MainButton?.hide();
        } catch (e) {
            // Игнорируем
        }
    }

    // Back Button - безопасный вызов
    showBackButton(onClick: () => void) {
        if (!this.isRealTelegram || !this.webApp?.BackButton) return;

        try {
            this.webApp.BackButton.onClick(onClick);
            this.webApp.BackButton.show();
        } catch (e) {
            console.log('BackButton not supported');
        }
    }

    hideBackButton() {
        if (!this.isRealTelegram) return;
        try {
            this.webApp?.BackButton?.hide();
        } catch (e) {
            // Игнорируем
        }
    }

    // Alerts - с fallback на браузерные
    alert(message: string): Promise<void> {
        return new Promise((resolve) => {
            if (this.isRealTelegram && this.webApp) {
                try {
                    this.webApp.showAlert(message, resolve);
                } catch (e) {
                    window.alert(message);
                    resolve();
                }
            } else {
                window.alert(message);
                resolve();
            }
        });
    }

    confirm(message: string): Promise<boolean> {
        return new Promise((resolve) => {
            if (this.isRealTelegram && this.webApp) {
                try {
                    this.webApp.showConfirm(message, resolve);
                } catch (e) {
                    resolve(window.confirm(message));
                }
            } else {
                resolve(window.confirm(message));
            }
        });
    }
}

export const telegram = new TelegramService();
export type { TelegramWebApp };