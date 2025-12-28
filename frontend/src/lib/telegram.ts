// frontend/src/lib/telegram.ts
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

// 🎨 LECTO 2.0 ФИКСИРОВАННАЯ ТЁМНАЯ ТЕМА
const LECTO_THEME = {
    bg_color: '#0D1117',
    secondary_bg_color: '#161B22',
    text_color: '#F0F6FC',
    hint_color: '#8B949E',
    link_color: '#58A6FF',
    button_color: '#238636',
    button_text_color: '#FFFFFF',
};

class TelegramService {
    private webApp: TelegramWebApp | null = null;
    private isRealTelegram: boolean = false;

    constructor() {
        if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
            this.webApp = window.Telegram.WebApp;
            this.isRealTelegram = !!(this.webApp.initData && this.webApp.initData.length > 0);
        }

        // Сразу применяем нашу тему при создании сервиса
        this.applyLectoTheme();
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
        // Всегда тёмный режим
        return true;
    }

    init() {
        if (this.webApp && this.isRealTelegram) {
            try {
                this.webApp.ready();
                this.webApp.expand();

                // Устанавливаем цвета в Telegram
                this.webApp.setHeaderColor(LECTO_THEME.bg_color);
                this.webApp.setBackgroundColor(LECTO_THEME.bg_color);
            } catch (e) {
                console.log('Telegram init error:', e);
            }
        }

        // Всегда применяем нашу тему
        this.applyLectoTheme();
    }

    // 🎨 Применяем НАШУ тему, игнорируя Telegram
    private applyLectoTheme() {
        if (typeof document === 'undefined') return;

        const root = document.documentElement;

        // Принудительно устанавливаем наши цвета
        root.style.setProperty('--tg-theme-bg-color', LECTO_THEME.bg_color);
        root.style.setProperty('--tg-theme-text-color', LECTO_THEME.text_color);
        root.style.setProperty('--tg-theme-hint-color', LECTO_THEME.hint_color);
        root.style.setProperty('--tg-theme-link-color', LECTO_THEME.link_color);
        root.style.setProperty('--tg-theme-button-color', LECTO_THEME.button_color);
        root.style.setProperty('--tg-theme-button-text-color', LECTO_THEME.button_text_color);
        root.style.setProperty('--tg-theme-secondary-bg-color', LECTO_THEME.secondary_bg_color);

        // Также устанавливаем на body для надёжности
        document.body.style.backgroundColor = LECTO_THEME.bg_color;
        document.body.style.color = LECTO_THEME.text_color;
    }

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
            // Игнорируем
        }
    }

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

    showPopup(params: {
        title?: string;
        message: string;
        buttons?: Array<{ type: 'ok' | 'close' | 'cancel'; text?: string }>;
    }): void {
        if (this.webApp?.showPopup) {
            this.webApp.showPopup(params);
        } else {
            alert(params.title ? `${params.title}\n\n${params.message}` : params.message);
        }
    }

    hideMainButton() {
        if (!this.isRealTelegram) return;
        try {
            this.webApp?.MainButton?.hide();
        } catch (e) { }
    }

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
        } catch (e) { }
    }

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