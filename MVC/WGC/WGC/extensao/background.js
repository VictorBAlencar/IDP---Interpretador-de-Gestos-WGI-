let pollingInterval = null;

function pollState() {
    fetch("http://127.0.0.1:5000/state")
        .then(res => res.json())
        .then(data => {
            // Passa os dados de estado para injetar o mouse web
            chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
                if(tabs[0]) {
                    chrome.tabs.sendMessage(tabs[0].id, { type: "WGC_STATE", data: data }).catch(() => {});
                }
            });
        })
        .catch(err => {}); // Erros silenciosos caso não conecte
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "start_tracking") {
        fetch("http://127.0.0.1:5000/" + request.action, { method: "POST" })
            .then(response => response.json())
            .then(data => {
                chrome.runtime.sendMessage({ message: data.message }).catch(() => {});
                if (!pollingInterval) {
                    pollingInterval = setInterval(pollState, 33); // ~30 fps
                }
            })
            .catch(error => {
                chrome.runtime.sendMessage({ message: "Erro: O servidor Python não está rodando." }).catch(() => {});
            });
    } else if (request.action === "stop_tracking") {
        fetch("http://127.0.0.1:5000/" + request.action, { method: "POST" })
            .then(response => response.json())
            .then(data => {
                chrome.runtime.sendMessage({ message: data.message }).catch(() => {});
                if (pollingInterval) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                }
                chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
                    if(tabs[0]) {
                        chrome.tabs.sendMessage(tabs[0].id, { type: "WGC_STOP" }).catch(() => {});
                    }
                });
            })
            .catch(error => {});
    }
});
