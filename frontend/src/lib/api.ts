// frontend/src/lib/api.ts
import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import { telegram } from './telegram';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiClient {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: API_URL,
            timeout: 30000,
        });

        this.client.interceptors.request.use((config) => {
            if (telegram.isAvailable && telegram.initData) {
                config.headers['X-Telegram-Init-Data'] = telegram.initData;
            } else {
                config.headers['X-User-ID'] = import.meta.env.VITE_DEV_USER_ID || '123456789';
            }
            return config;
        });

        this.client.interceptors.response.use(
            (response) => response,
            (error: AxiosError<{ detail?: string }>) => {
                console.error('API Error:', error.response?.data || error.message);
                if (error.response?.status === 429) {
                    telegram.alert('Достигнут дневной лимит. Оформите Pro подписку для безлимитного доступа.');
                }
                return Promise.reject(error);
            }
        );
    }

    // ==================== Users ====================
    async getMe() {
        const { data } = await this.client.get('/users/me');
        return data;
    }

    async getMyLimits() {
        const { data } = await this.client.get('/users/me/limits');
        return data;
    }

    async getMyStreak() {
        const { data } = await this.client.get('/users/me/streak');
        return data;
    }

    // ==================== Folders ====================
    async getFolders(parentId?: string) {
        const params = parentId ? { parent_id: parentId } : {};
        const { data } = await this.client.get('/folders/', { params });
        return data;
    }

    async createFolder(name: string, parentId?: string) {
        const { data } = await this.client.post('/folders/', { name, parent_id: parentId });
        return data;
    }

    async deleteFolder(folderId: string) {
        const { data } = await this.client.delete(`/folders/${folderId}`);
        return data;
    }

    // ==================== Materials ====================
    async getMaterials(folderId?: string) {
        const params = folderId ? { folder_id: folderId } : {};
        const { data } = await this.client.get('/materials/', { params });
        return data;
    }

    async getMaterial(materialId: string) {
        const { data } = await this.client.get(`/materials/${materialId}`);
        return data;
    }

    async uploadFile(file: File, title?: string, folderId?: string, groupId?: string) {
        const formData = new FormData();
        formData.append('file', file);
        if (title) formData.append('title', title);
        if (folderId) formData.append('folder_id', folderId);
        if (groupId) formData.append('group_id', groupId);
        formData.append('auto_process', 'true');

        const { data } = await this.client.post('/materials/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return data;
    }

    async createTextMaterial(title: string, content: string, folderId?: string, groupId?: string) {
        const formData = new FormData();
        formData.append('title', title);
        formData.append('content', content);
        if (folderId) formData.append('folder_id', folderId);
        if (groupId) formData.append('group_id', groupId);

        const { data } = await this.client.post('/materials/text', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return data;
    }

    async scanImage(file: File, title?: string, folderId?: string, groupId?: string) {
        const formData = new FormData();
        formData.append('file', file);
        if (title) formData.append('title', title);
        if (folderId) formData.append('folder_id', folderId);
        if (groupId) formData.append('group_id', groupId);

        const { data } = await this.client.post('/materials/scan', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return data;
    }

    async generateFromTopic(topic: string, folderId?: string, groupId?: string) {
        const { data } = await this.client.post('/materials/generate-from-topic', {
            topic,
            folder_id: folderId,
            group_id: groupId
        });
        return data;
    }

    async updateMaterial(materialId: string, updateData: { title?: string; folder_id?: string }) {
        const { data } = await this.client.patch(`/materials/${materialId}`, updateData);
        return data;
    }

    async moveMaterialToRoot(materialId: string) {
        const { data } = await this.client.patch(`/materials/${materialId}/move-to-root`);
        return data;
    }

    async deleteMaterial(materialId: string) {
        const { data } = await this.client.delete(`/materials/${materialId}`);
        return data;
    }

    async searchMaterials(query: string) {
        const { data } = await this.client.get('/materials/search/all', { params: { q: query } });
        return data;
    }

    async getGroupMaterials(groupId: string) {
        const { data } = await this.client.get(`/materials/group/${groupId}`);
        return data;
    }

    // ==================== Processing ====================
    async processMaterial(materialId: string) {
        const { data } = await this.client.post(`/processing/material/${materialId}`);
        return data;
    }

    async getProcessingStatus(materialId: string) {
        const { data } = await this.client.get(`/processing/material/${materialId}/status`);
        return data;
    }

    async regenerateOutput(materialId: string, format: string) {
        const { data } = await this.client.post(`/processing/material/${materialId}/regenerate/${format}`);
        return data;
    }

    // ==================== Outputs ====================
    async getMaterialOutputs(materialId: string, format?: string) {
        const params = format ? { format } : {};
        const { data } = await this.client.get(`/outputs/material/${materialId}`, { params });
        return data;
    }

    async getOutput(outputId: string) {
        const { data } = await this.client.get(`/outputs/${outputId}`);
        return data;
    }

    // ==================== Groups ====================
    async getMyGroups() {
        const { data } = await this.client.get('/groups/');
        return data;
    }

    async createGroup(name: string, description?: string) {
        const { data } = await this.client.post('/groups/', { name, description });
        return data;
    }

    async getGroup(groupId: string) {
        const { data } = await this.client.get(`/groups/${groupId}`);
        return data;
    }

    async joinGroup(inviteCode: string) {
        const { data } = await this.client.post('/groups/join', { invite_code: inviteCode });
        return data;
    }

    async leaveGroup(groupId: string) {
        const { data } = await this.client.post(`/groups/${groupId}/leave`);
        return data;
    }

    async deleteGroup(groupId: string) {
        const { data } = await this.client.delete(`/groups/${groupId}`);
        return data;
    }

    async getGroupMembers(groupId: string) {
        const { data } = await this.client.get(`/groups/${groupId}/members`);
        return data;
    }

    // ==================== Quiz Results ====================
    async saveQuizResult(groupId: string, materialId: string, score: number, maxScore: number) {
        const { data } = await this.client.post(`/groups/${groupId}/quiz-result`, null, {
            params: { material_id: materialId, score, max_score: maxScore }
        });
        return data;
    }

    async getGroupQuizResults(groupId: string) {
        const { data } = await this.client.get(`/groups/${groupId}/quiz-results`);
        return data;
    }

    async getGroupLeaderboard(groupId: string) {
        const { data } = await this.client.get(`/groups/${groupId}/leaderboard`);
        return data;
    }

    // ==================== Referrals ====================
    async getReferralStats() {
        const { data } = await this.client.get('/groups/referral/stats');
        return data;
    }

    async generateReferralCode() {
        const { data } = await this.client.post('/groups/referral/generate');
        return data;
    }

    // ==================== Search / RAG ====================
    async askLibrary(question: string, materialId?: string) {
        const { data } = await this.client.post('/search/ask', {
            question,
            material_id: materialId
        });
        return data;
    }

    async semanticSearch(query: string, limit?: number, materialId?: string) {
        const { data } = await this.client.get('/search/semantic', {
            params: { q: query, limit, material_id: materialId }
        });
        return data;
    }

    async indexMaterial(materialId: string) {
        const { data } = await this.client.post(`/search/index/${materialId}`);
        return data;
    }

    // ==================== Presentations ====================
    async generatePresentationPreview(
        topic: string,
        numSlides: number = 10,
        style: 'professional' | 'educational' | 'creative' | 'minimal' = 'professional'
    ) {
        const { data } = await this.client.post('/presentations/generate', {
            topic,
            num_slides: numSlides,
            style
        }, {
            timeout: 60000 // 60 секунд для генерации
        });
        return data;
    }

    async downloadPresentation(
        topic: string,
        numSlides: number = 10,
        style: 'professional' | 'educational' | 'creative' | 'minimal' = 'professional',
        theme: 'blue' | 'green' | 'purple' | 'orange' = 'blue'
    ) {
        const response = await this.client.post('/presentations/download', {
            topic,
            num_slides: numSlides,
            style,
            theme
        }, {
            responseType: 'blob',
            timeout: 90000 // 90 секунд
        });

        // Скачивание файла
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        const filename = `${topic.slice(0, 50).replace(/[^a-zA-Zа-яА-Я0-9]/g, '_')}.pptx`;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    }
}

export const api = new ApiClient();