document.getElementById('btn-start').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: "start_tracking" });
    document.getElementById('status').innerText = "Iniciando a câmera...";
});

document.getElementById('btn-stop').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: "stop_tracking" });
    document.getElementById('status').innerText = "Parando...";
});

// Ouve as respostas que vêm do Python
chrome.runtime.onMessage.addListener((msg) => {
    document.getElementById('status').innerText = msg.message;
});