import { defineStore } from 'pinia';
import api from '../services/api';

export const useConfigStore = defineStore('config', {
  state: () => ({
    config: {
      min_liquidity_usd: 5000.0,
      min_volume_5m_usd: 1000.0,
      max_age_minutes: 60,
      min_buy_sell_ratio: 1.2,
      require_lp_locked: true,
      require_mint_renounced: true,
      blacklist_keywords: 'test,scam,airdrop,pump',
      polling_interval_seconds: 20
    },
    loading: false
  }),
  actions: {
    async fetchConfig() {
      try {
        const response = await api.get('/config');
        this.config = response.data;
      } catch (error) {
        console.error('Error fetching config:', error);
      }
    },
    async updateConfig(newConfig) {
      this.loading = true;
      try {
        const response = await api.put('/config', newConfig);
        this.config = response.data;
        return true;
      } catch (error) {
        console.error('Error updating config:', error);
        return false;
      } finally {
        this.loading = false;
      }
    }
  }
});
