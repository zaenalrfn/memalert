<template>
  <div class="min-h-screen bg-[#060608] text-zinc-100 font-sans relative overflow-x-hidden">
    <!-- Cryptographic Background Effect -->
    <div class="fixed inset-0 pointer-events-none opacity-[0.03] z-0 overflow-hidden select-none" aria-hidden="true">
      <div class="absolute inset-0 font-mono text-[10px] leading-none break-all whitespace-pre-wrap">
        {{ cryptoBgText }}
      </div>
      <div class="absolute inset-0 bg-gradient-to-b from-transparent via-[#060608]/50 to-[#060608]"></div>
    </div>

    <div class="max-w-5xl mx-auto space-y-6 p-4 md:p-6 relative z-10">
      <!-- Header -->
      <header class="flex items-center justify-between py-4 border-b border-zinc-800/50">
        <div>
          <h1 class="text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-500">
            Moon Spotter
          </h1>
          <p class="text-xs font-mono text-zinc-500 uppercase tracking-widest">Solana Network Intelligence</p>
        </div>
        <div class="flex items-center gap-3">
          <button @click="testAlert" class="bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-bold uppercase tracking-tighter px-4 py-2 rounded-md transition-all active:scale-95">
            Test Ping
          </button>
          <div class="flex items-center gap-2 bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 px-3 py-1.5 rounded-full shadow-inner">
            <div :class="botStatus.is_muted ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]' : 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]'" class="w-1.5 h-1.5 rounded-full animate-pulse"></div>
            <span class="text-[10px] font-bold uppercase tracking-tighter">{{ botStatus.is_muted ? 'Muted' : 'Live' }}</span>
          </div>
        </div>
      </header>

      <!-- Main Grid -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <!-- Sidebar -->
        <div class="md:col-span-1 space-y-4">
          <div class="bg-zinc-900/40 backdrop-blur-md p-5 rounded-xl border border-zinc-800/50 shadow-2xl">
            <h2 class="text-[10px] font-black mb-4 text-zinc-500 uppercase tracking-widest">Engine Config</h2>
            <div class="space-y-4">
              <div>
                <label class="text-[9px] uppercase text-zinc-400 font-bold tracking-tighter">Min Liquidity (USD)</label>
                <div class="relative mt-1">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600 text-xs">$</span>
                  <input v-model.number="config.min_liquidity_usd" type="number" class="w-full bg-black/40 border border-zinc-800 rounded-lg pl-6 pr-3 py-2 text-xs focus:border-zinc-400 outline-none transition-colors font-mono">
                </div>
              </div>
              <div>
                <label class="text-[9px] uppercase text-zinc-400 font-bold tracking-tighter">Min Vol 5m (USD)</label>
                <div class="relative mt-1">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600 text-xs">$</span>
                  <input v-model.number="config.min_volume_5m_usd" type="number" class="w-full bg-black/40 border border-zinc-800 rounded-lg pl-6 pr-3 py-2 text-xs focus:border-zinc-400 outline-none transition-colors font-mono">
                </div>
              </div>
              <div>
                <label class="text-[9px] uppercase text-zinc-400 font-bold tracking-tighter">Max Pool Age (Min)</label>
                <div class="relative mt-1">
                  <input v-model.number="config.max_age_minutes" type="number" class="w-full bg-black/40 border border-zinc-800 rounded-lg px-3 py-2 text-xs focus:border-zinc-400 outline-none transition-colors font-mono">
                </div>
              </div>
              <div>
                <label class="text-[9px] uppercase text-zinc-400 font-bold tracking-tighter">Min Buy/Sell Ratio</label>
                <div class="relative mt-1">
                  <input v-model.number="config.min_buy_sell_ratio" type="number" step="0.1" class="w-full bg-black/40 border border-zinc-800 rounded-lg px-3 py-2 text-xs focus:border-zinc-400 outline-none transition-colors font-mono">
                </div>
              </div>
              <div>
                <label class="text-[9px] uppercase text-zinc-400 font-bold tracking-tighter">Poll Interval (Sec)</label>
                <div class="relative mt-1">
                  <input v-model.number="config.polling_interval_seconds" type="number" class="w-full bg-black/40 border border-zinc-800 rounded-lg px-3 py-2 text-xs focus:border-zinc-400 outline-none transition-colors font-mono">
                </div>
              </div>
              <button @click="saveConfig" class="w-full bg-zinc-100 text-black text-[10px] font-black uppercase tracking-widest py-2.5 rounded-lg hover:bg-white transition-all active:scale-95 shadow-lg shadow-white/5">
                Apply Core
              </button>
            </div>
          </div>

          <div class="bg-zinc-900/40 backdrop-blur-md p-5 rounded-xl border border-zinc-800/50 shadow-2xl">
            <h2 class="text-[10px] font-black mb-4 text-zinc-500 uppercase tracking-widest">Bot Status</h2>
            <div class="space-y-2">
              <button v-if="!botStatus.is_muted" @click="muteBot(30)" class="w-full bg-zinc-900 hover:bg-zinc-800 text-[10px] font-bold uppercase py-2 rounded-lg border border-zinc-800 transition-all">
                Mute 30m
              </button>
              <button v-else @click="unmuteBot" class="w-full bg-red-500/10 text-red-500 text-[10px] font-bold uppercase py-2 rounded-lg border border-red-500/20 transition-all">
                Unmute Signal
              </button>
            </div>
          </div>
        </div>

        <!-- Feed Container -->
        <div class="md:col-span-3 space-y-4">
          <!-- Filter Tabs -->
          <div class="flex items-center gap-1 p-1 bg-zinc-900/40 backdrop-blur-md border border-zinc-800/50 rounded-xl overflow-x-auto scrollbar-hide">
            <button v-for="tab in ['all', 'alerted', 'alerted_muted', 'rejected']" 
                    :key="tab"
                    @click="currentTab = tab"
                    :class="currentTab === tab ? 'bg-zinc-100 text-black shadow-lg' : 'text-zinc-500 hover:text-zinc-300'"
                    class="px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all whitespace-nowrap">
              {{ tab.replace('_', ' ') }}
            </button>
          </div>

          <!-- Market Table -->
          <div class="bg-zinc-900/20 backdrop-blur-md rounded-xl border border-zinc-800/50 shadow-2xl overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-left">
                <thead>
                  <tr class="border-b border-zinc-800/50 text-zinc-500 text-[9px] uppercase font-black tracking-[0.2em]">
                    <th class="p-4">Asset Matrix</th>
                    <th class="p-4 text-right">Liquidity</th>
                    <th class="p-4 text-right">Mkt Cap</th>
                    <th class="p-4 text-right">Vol (5m)</th>
                    <th class="p-4 text-center">Protocol</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-zinc-800/30">
                  <tr v-for="token in filteredTokens" :key="token.token_address" class="hover:bg-zinc-100/[0.02] transition-colors group">
                    <td class="p-4">
                      <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-md bg-zinc-800 flex items-center justify-center font-mono text-[10px] font-bold border border-zinc-700/50 group-hover:border-zinc-400 transition-colors">
                          {{ token.symbol[0] }}
                        </div>
                        <div>
                          <div class="text-xs font-black tracking-tight">${{ token.symbol }}</div>
                          <div class="text-[9px] font-mono text-zinc-600 group-hover:text-zinc-400 transition-colors truncate max-w-[80px]">{{ token.token_address }}</div>
                        </div>
                      </div>
                    </td>
                    <td class="p-4 text-right font-mono text-xs text-zinc-400">${{ (token.liquidity_usd/1000).toFixed(1) }}k</td>
                    <td class="p-4 text-right font-mono text-xs text-zinc-400">
                      {{ token.market_cap_usd ? '$' + (token.market_cap_usd/1000).toFixed(1) + 'k' : '--' }}
                    </td>
                    <td class="p-4 text-right font-mono text-xs text-zinc-200">${{ (token.volume_5m_usd/1000).toFixed(1) }}k</td>
                    <td class="p-4 text-center">
                      <div :class="{
                        'bg-green-500/10 text-green-500 border-green-500/20': token.status === 'alerted',
                        'bg-zinc-100/10 text-zinc-100 border-zinc-100/20': token.status === 'alerted_muted',
                        'bg-red-500/10 text-red-500 border-red-500/20': token.status === 'rejected'
                      }" class="inline-block px-2 py-0.5 rounded text-[8px] font-black uppercase border tracking-tighter">
                        {{ token.status === 'alerted' ? 'Passed' : (token.status === 'alerted_muted' ? 'Muted' : 'Reject') }}
                      </div>
                    </td>
                  </tr>
                  <tr v-if="filteredTokens.length === 0">
                    <td colspan="5" class="p-20 text-center text-zinc-600 font-mono text-[10px] uppercase tracking-[0.3em] animate-pulse">
                      No Data Signal Found
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, onBeforeUnmount, computed } from 'vue';
import api from './services/api';

const tokens = ref([]);
const currentTab = ref('all');
const botStatus = ref({ is_muted: false });
const config = ref({ 
  min_liquidity_usd: 0, 
  min_volume_5m_usd: 0, 
  max_age_minutes: 0,
  min_buy_sell_ratio: 0,
  polling_interval_seconds: 0
});
const cryptoBgText = ref('');
let refreshInterval = null;

// Generate cryptographic background text
function generateCryptoText() {
  const chars = '01ABCDEFHIJKLMNOPQRSTUVWXYZ$#@&*';
  let text = '';
  for(let i=0; i<2000; i++) {
    text += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  cryptoBgText.value = text;
}

const filteredTokens = computed(() => {
  if (currentTab.value === 'all') return tokens.value;
  return tokens.value.filter(t => t.status === currentTab.value);
});

async function fetchTokens() { 
  try { 
    const res = await api.get('/tokens', { params: { limit: 100 } }); 
    tokens.value = res.data.items; 
  } catch (e) {} 
}

async function fetchStatus() { try { const res = await api.get('/bot/status'); botStatus.value = res.data; } catch (e) {} }
async function fetchConfig() { try { const res = await api.get('/config'); config.value = res.data; } catch (e) {} }
async function saveConfig() { await api.put('/config', config.value); fetchConfig(); }
async function muteBot(mins) { await api.post('/bot/mute', { duration_minutes: mins }); fetchStatus(); }
async function unmuteBot() { await api.post('/bot/unmute'); fetchStatus(); }
async function testAlert() { await api.post('/bot/test-alert'); }

onMounted(() => {
  generateCryptoText();
  fetchTokens(); fetchStatus(); fetchConfig();
  refreshInterval = setInterval(() => { 
    fetchTokens(); 
    fetchStatus(); 
    generateCryptoText(); // refresh matrix text
  }, 5000);
});

onBeforeUnmount(() => clearInterval(refreshInterval));
</script>

<style>
@tailwind base;
@tailwind components;
@tailwind utilities;

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

body {
  background-color: #060608;
}

@keyframes pulse-subtle {
  0%, 100% { opacity: 0.03; }
  50% { opacity: 0.05; }
}

input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>
