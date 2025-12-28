import { useState, useRef, useEffect } from 'react';
import { clsx } from 'clsx';

interface Tab {
    id: string;
    label: string;
    icon?: React.ReactNode;
}

interface SliderTabsProps {
    tabs: Tab[];
    activeTab: string;
    onChange: (tabId: string) => void;
    className?: string;
}

export function SliderTabs({ tabs, activeTab, onChange, className }: SliderTabsProps) {
    const [sliderStyle, setSliderStyle] = useState({ left: 0, width: 0 });
    const tabsRef = useRef<(HTMLButtonElement | null)[]>([]);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const activeIndex = tabs.findIndex(t => t.id === activeTab);
        const activeTabEl = tabsRef.current[activeIndex];

        if (activeTabEl && containerRef.current) {
            const containerRect = containerRef.current.getBoundingClientRect();
            const tabRect = activeTabEl.getBoundingClientRect();

            setSliderStyle({
                left: tabRect.left - containerRect.left,
                width: tabRect.width,
            });
        }
    }, [activeTab, tabs]);

    return (
        <div
            ref={containerRef}
            className={clsx(
                'relative flex bg-lecto-bg-secondary rounded-xl p-1',
                className
            )}
        >
            {/* Slider indicator */}
            <div
                className="absolute top-1 bottom-1 bg-lecto-bg-tertiary rounded-lg transition-all duration-300 ease-out"
                style={{ left: sliderStyle.left, width: sliderStyle.width }}
            />

            {/* Tabs */}
            {tabs.map((tab, index) => (
                <button
                    key={tab.id}
                    ref={(el) => { tabsRef.current[index] = el; }}
                    onClick={() => onChange(tab.id)}
                    className={clsx(
                        'relative z-10 flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg transition-colors',
                        activeTab === tab.id
                            ? 'text-lecto-text-primary'
                            : 'text-lecto-text-secondary hover:text-lecto-text-primary'
                    )}
                >
                    {tab.icon}
                    <span className="text-sm font-medium">{tab.label}</span>
                </button>
            ))}
        </div>
    );
}