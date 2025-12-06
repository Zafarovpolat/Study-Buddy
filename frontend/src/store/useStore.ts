// frontend/src/store/useStore.ts - ЗАМЕНИ ПОЛНОСТЬЮ
import { create } from 'zustand';

interface User {
    id: string;
    telegram_id: number;
    telegram_username?: string;
    first_name?: string;
    subscription_tier: 'free' | 'pro' | 'group';
    daily_requests_count: number;
    referral_code?: string;
    referral_count?: number;
    created_at: string;
}

interface Folder {
    id: string;
    name: string;
    parent_id?: string;
    is_group?: boolean;
    created_at: string;
}

interface Group {
    id: string;
    name: string;
    description?: string;
    invite_code: string;
    role: 'owner' | 'admin' | 'member';
    member_count: number;
    max_members: number;
    joined_at: string;
    is_owner: boolean;
}

interface Material {
    id: string;
    title: string;
    material_type: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    created_at: string;
    outputs?: AIOutput[];
}

interface AIOutput {
    id: string;
    format: string;
    content: string;
    created_at: string;
}

interface Limits {
    subscription_tier: string;
    can_make_request: boolean;
    remaining_today: number | string;
    daily_limit: number | string;
}

interface ReferralStats {
    referral_code: string;
    referral_link: string;
    referral_count: number;
    referrals_needed: number;
    pro_granted: boolean;
    threshold: number;
}

interface AppState {
    // User
    user: User | null;
    limits: Limits | null;
    setUser: (user: User | null) => void;
    setLimits: (limits: Limits | null) => void;

    // Navigation
    currentFolderId: string | null;
    setCurrentFolderId: (id: string | null) => void;

    // Active Tab
    activeTab: 'personal' | 'groups';
    setActiveTab: (tab: 'personal' | 'groups') => void;

    // Folders
    folders: Folder[];
    setFolders: (folders: Folder[]) => void;
    addFolder: (folder: Folder) => void;

    // Groups
    groups: Group[];
    setGroups: (groups: Group[]) => void;
    addGroup: (group: Group) => void;
    removeGroup: (id: string) => void;

    // Materials
    materials: Material[];
    setMaterials: (materials: Material[]) => void;
    addMaterial: (material: Material) => void;
    updateMaterial: (id: string, updates: Partial<Material>) => void;
    removeMaterial: (id: string) => void;

    // Referrals
    referralStats: ReferralStats | null;
    setReferralStats: (stats: ReferralStats | null) => void;

    // UI State
    isLoading: boolean;
    setIsLoading: (loading: boolean) => void;

    // Selected material for viewing
    selectedMaterial: Material | null;
    setSelectedMaterial: (material: Material | null) => void;
}

export const useStore = create<AppState>((set) => ({
    // User
    user: null,
    limits: null,
    setUser: (user) => set({ user }),
    setLimits: (limits) => set({ limits }),

    // Navigation
    currentFolderId: null,
    setCurrentFolderId: (id) => set({ currentFolderId: id }),

    // Active Tab
    activeTab: 'personal',
    setActiveTab: (tab) => set({ activeTab: tab }),

    // Folders
    folders: [],
    setFolders: (folders) => set({ folders }),
    addFolder: (folder) => set((state) => ({ folders: [...state.folders, folder] })),

    // Groups
    groups: [],
    setGroups: (groups) => set({ groups }),
    addGroup: (group) => set((state) => ({ groups: [...state.groups, group] })),
    removeGroup: (id) => set((state) => ({
        groups: state.groups.filter((g) => g.id !== id)
    })),

    // Materials
    materials: [],
    setMaterials: (materials) => set({ materials }),
    addMaterial: (material) => set((state) => ({
        materials: [material, ...state.materials]
    })),
    updateMaterial: (id, updates) => set((state) => ({
        materials: state.materials.map((m) =>
            m.id === id ? { ...m, ...updates } : m
        ),
    })),
    removeMaterial: (id) => set((state) => ({
        materials: state.materials.filter((m) => m.id !== id),
    })),

    // Referrals
    referralStats: null,
    setReferralStats: (stats) => set({ referralStats: stats }),

    // UI
    isLoading: false,
    setIsLoading: (isLoading) => set({ isLoading }),

    // Selected
    selectedMaterial: null,
    setSelectedMaterial: (material) => set({ selectedMaterial: material }),
}));