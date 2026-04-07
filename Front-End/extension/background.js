// Background script para IGW Extension
// Este script roda em segundo plano e gerencia a comunicação entre content scripts

chrome.runtime.onInstalled.addListener(() => {
  console.log('IGW Extension instalada com sucesso!');
});

// Listener para mensagens dos content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'gestureDetected') {
    // Aqui você pode adicionar lógica para processar gestos detectados
    console.log('Gesto detectado:', request.gesture);
    sendResponse({ success: true });
  }
});

// Manter a extensão ativa
chrome.runtime.onStartup.addListener(() => {
  console.log('IGW Extension iniciada');
});