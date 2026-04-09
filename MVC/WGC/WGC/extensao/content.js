// Cria um elemento que simula o cursor apenas DENTRO do site!
let virtualCursor = document.createElement("div");
virtualCursor.id = "wgc-virtual-cursor";
virtualCursor.style.position = "fixed";
virtualCursor.style.width = "20px";
virtualCursor.style.height = "20px";
virtualCursor.style.backgroundColor = "rgba(0, 150, 255, 0.7)";
virtualCursor.style.border = "2px solid white";
virtualCursor.style.borderRadius = "50%";
virtualCursor.style.pointerEvents = "none"; // IMPORTANTE: não bloqueia os seus cliques
virtualCursor.style.zIndex = "2147483647"; // Fica acima de tudo
virtualCursor.style.transition = "background-color 0.1s, transform 0.05s linear";
virtualCursor.style.display = "none";
document.body.appendChild(virtualCursor);

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "WGC_STOP") {
        virtualCursor.style.display = "none";
        return;
    }
    
    if (msg.type === "WGC_STATE") {
        let state = msg.data;
        virtualCursor.style.display = "block";
        
        // Converte valores (0.0 até 1.0) nas dimensões reais da tela da guia do site
        let x = state.x * window.innerWidth;
        let y = state.y * window.innerHeight;
        
        virtualCursor.style.left = `${x}px`;
        virtualCursor.style.top = `${y}px`;
        virtualCursor.style.transform = "translate(-50%, -50%)"; // Centraliza a bolinha
        
        if (state.action === "left_click" || state.action === "double_click") {
            virtualCursor.style.backgroundColor = "rgba(0, 255, 0, 0.9)"; // Pisca verde
            simulateClick(x, y);
            setTimeout(() => virtualCursor.style.backgroundColor = "rgba(0, 150, 255, 0.7)", 150);
        }
    }
});

// Lógica do clique DOM real independente do Windows OS
function simulateClick(x, y) {
    let el = document.elementFromPoint(x, y);
    if (el) {
        let clickEvent = new MouseEvent('click', {
            view: window, bubbles: true, cancelable: true, clientX: x, clientY: y
        });
        el.dispatchEvent(clickEvent);
    }
}