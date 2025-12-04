// frontend/src/lib/api.ts - ЗАМЕНИ ПОЛНОСТЬЮ
import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import { telegram } from './telegram';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: API_URL,
            timeout: 60000, // 60 секунд для AI обработки
        });

        // Добавляем заголовки авторизации
        this.client.interceptors.request.use((config) => {
            if (telegram.isAvailable && telegram.initData) {
                config.headers['X-Telegram-Init-Data'] = telegram.initData;
            } else {
                // Dev режим
                config.headers['X-User-ID'] = import.meta.env.VITE_DEV_USER_ID || '123456789';
            }
            return config;
        });

        // Обработка ошибок
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

    // Users
    async getMe() {
        const { data } = await this.client.get('/users/me');
        return data;
    }

    async getMyLimits() {
        const { data } = await this.client.get('/users/me/limits');
        return data;
    }

    // Folders
    async getFolders(parentId?: string) {
        const params = parentId ? { parent_id: parentId } : {};
        const { data } = await this.client.get('/folders/', { params });
        return data;
    }

    async createFolder(name: string, parentId?: string) {
        const { data } = await this.client.post('/folders/', {
            name,
            parent_id: parentId,
        });
        return data;
    }

    async deleteFolder(folderId: string) {
        const { data } = await this.client.delete(`/folders/${folderId}`);
        return data;
    }

    // Materials
    async getMaterials(folderId?: string) {
        const params = folderId ? { folder_id: folderId } : {};
        const { data } = await this.client.get('/materials/', { params });
        return data;
    }

    async getMaterial(materialId: string) {
        const { data } = await this.client.get(`/materials/${materialId}`);
        return data;
    }

    async uploadFile(file: File, title?: string, folderId?: string) {
        const formData = new FormData();
        formData.append('file', file);
        if (title) formData.append('title', title);
        if (folderId) formData.append('folder_id', folderId);
        formData.append('auto_process', 'true');

        const { data } = await this.client.post('/materials/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return data;
    }

    async createTextMaterial(title: string, content: string, folderId?: string) {
        const formData = new FormData();
        formData.append('title', title);
        formData.append('content', content);
        if (folderId) formData.append('folder_id', folderId);

        const { data } = await this.client.post('/materials/text', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return data;
    }

    async deleteMaterial(materialId: string) {
        const { data } = await this.client.delete(`/materials/${materialId}`);
        return data;
    }

    // Processing
    async processMaterial(materialId: string) {
        const { data } = await this.client.post(`/processing/material/${materialId}`);
        return data;
    }

    async getProcessingStatus(materialId: string) {
        const { data } = await this.client.get(`/processing/material/${materialId}/status`);
        return data;
    }

    async regenerateOutput(materialId: string, format: string) {
        const { data } = await this.client.post(
            `/processing/material/${materialId}/regenerate/${format}`
        );
        return data;
    }

    // Outputs
    async getMaterialOutputs(materialId: string, format?: string) {
        const params = format ? { format } : {};
        const { data } = await this.client.get(`/outputs/material/${materialId}`, { params });
        return data;
    }

    async getOutput(outputId: string) {
        const { data } = await this.client.get(`/outputs/${outputId}`);
        return data;
    }

    async scanImage(file: File, title?: string, folderId?: string) {
        const formData = new FormData();
        formData.append('file', file);
        if (title) formData.append('title', title);
        if (folderId) formData.append('folder_id', folderId);

        const { data } = await this.client.post('/materials/scan', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return data;
    }

    async getMyStreak() {
        const { data } = await this.client.get('/users/me/streak');
        return data;
    }
}

// Создаём и экспортируем синглтон
export const api = new ApiClient();