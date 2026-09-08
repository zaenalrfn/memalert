import { defineStore } from 'pinia';
import api from '../services/api';

export const useTokenStore = defineStore('tokens', {
  state: () => ({
    tokens: [],
    total: 0,
    loading: false,
    status: 'all'
  }),
  actions: {
    async fetchTokens(status = 'all', limit = 50, offset = 0) {
      this.loading = true;
      try {
        const response = await api.get('/tokens', { params: { status, limit, offset } });
        this.tokens = response.data.items;
        this.total = response.data.total;
        this.status = status;
      } catch (error) {
        console.error('Error fetching tokens:', error);
      } finally {
        this.loading = false;
      }
    }
  }
});
