<script setup>
import { computed, onMounted, ref } from 'vue';
const dashboard = ref({}); const incidents = ref([]); const diagnosis = ref(null); const selectedId = ref(null); const loading = ref(false);
const selected = computed(() => incidents.value.find(item => item.id === selectedId.value));
async function load() { const [d, i] = await Promise.all([fetch('/api/v1/dashboard').then(r => r.json()), fetch('/api/v1/incidents').then(r => r.json())]); dashboard.value = d; incidents.value = i; selectedId.value ??= i[0]?.id; }
async function diagnose() { if (!selectedId.value) return; loading.value = true; diagnosis.value = await fetch(`/api/v1/incidents/${selectedId.value}/diagnose`, { method: 'POST' }).then(r => r.json()); loading.value = false; await load(); }
onMounted(load);
</script>
<template><main><aside><strong>云网智维 AI</strong><span>Vue 3 控制台</span></aside><section><header><p>AI OPS WORKBENCH</p><h1>云网智能故障处置助手</h1></header><div class="metrics"><article><small>演示 API 可用率</small><b>{{ dashboard.api_availability }}%</b></article><article><small>活跃告警</small><b>{{ dashboard.active_incidents }}</b></article><article><small>高风险告警</small><b class="danger">{{ dashboard.high_risk_incidents }}</b></article></div><div class="grid"><article><h2>告警列表</h2><button v-for="item in incidents" :key="item.id" :class="{ active: item.id === selectedId }" @click="selectedId = item.id"><small>{{ item.category }} · {{ item.severity }}风险</small><b>{{ item.title }}</b><span>{{ item.detail }}</span></button></article><article class="diagnosis"><h2>AI 诊断</h2><p v-if="selected">{{ selected.title }}</p><button @click="diagnose">{{ loading ? '诊断中…' : '开始诊断' }}</button><pre v-if="diagnosis">{{ diagnosis.diagnosis }}</pre></article></div></section></main></template>
