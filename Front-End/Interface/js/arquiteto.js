const video = document.getElementById('webcam');
const overlay = document.getElementById('camera-overlay');
const status = document.getElementById('camera-status');
const outputCanvas = document.getElementById('output');
const outputCtx = outputCanvas.getContext('2d');
const pointer = document.getElementById('camera-pointer');
const stopButton = document.getElementById('stop-camera-btn');
let camera = null;
let stream = null;
let handsModel = null;

function updateCameraStatus(message, color = 'text-gray-500') {
    status.textContent = message;
    status.classList.remove('text-gray-500', 'text-red-400', 'text-yellow-300', 'text-green-400');
    status.classList.add(color);
}

function resizeOutputCanvas() {
    if (!video.videoWidth || !video.videoHeight) return;
    outputCanvas.width = video.videoWidth;
    outputCanvas.height = video.videoHeight;
}

function renderHandResults(results) {
    outputCtx.save();
    outputCtx.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
    if (results.image) {
        outputCtx.drawImage(results.image, 0, 0, outputCanvas.width, outputCanvas.height);
    }

    if (results.multiHandLandmarks && results.multiHandLandmarks.length) {
        const landmarks = results.multiHandLandmarks[0];
        for (const landmark of results.multiHandLandmarks) {
            drawConnectors(outputCtx, landmark, HAND_CONNECTIONS, { color: '#00f3ff', lineWidth: 4 });
            drawLandmarks(outputCtx, landmark, { color: '#ffffff', lineWidth: 2, radius: 4 });
        }

        const tip = landmarks[8];
        if (tip) {
            const x = outputCanvas.width * (1 - tip.x);
            const y = outputCanvas.height * tip.y;
            pointer.style.transform = `translate(${x}px, ${y}px)`;
            pointer.classList.remove('hidden');
        }
    } else {
        pointer.classList.add('hidden');
    }

    outputCtx.restore();
}

function renderOverlay() {
    if (stream) {
        overlay.style.display = 'none';
        stopButton.classList.remove('hidden');
        return;
    }

    overlay.style.display = 'flex';
    stopButton.classList.add('hidden');
    overlay.innerHTML = `
        <button onclick="startCamera()" class="px-8 py-3 bg-white text-black font-bold rounded-full hover:bg-gray-200 transition">
            Ativar Câmera de Teste
        </button>
    `;
}

async function initHands() {
    if (handsModel) return;

    handsModel = new Hands({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
    });

    handsModel.setOptions({
        maxNumHands: 1,
        modelComplexity: 1,
        minDetectionConfidence: 0.7,
        minTrackingConfidence: 0.7
    });

    handsModel.onResults((results) => {
        resizeOutputCanvas();
        renderHandResults(results);

        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            updateCameraStatus('Mão detectada. Movimente os dedos para ver os pontos.', 'text-green-400');
        } else {
            updateCameraStatus('Câmera ativa. Posicione a mão no quadro.', 'text-yellow-300');
        }
    });

    camera = new Camera(video, {
        onFrame: async () => {
            await handsModel.send({ image: video });
        },
        width: 1280,
        height: 720
    });
}

async function startCamera() {
    try {
        await initHands();
        await camera.start();
        stream = video.srcObject;
        renderOverlay();
        updateCameraStatus('Câmera ativa. Seu vídeo é processado apenas localmente.', 'text-green-400');
    } catch (error) {
        console.error(error);
        updateCameraStatus('Não foi possível acessar a câmera. Verifique as permissões do navegador.', 'text-red-400');
    }
}

function stopCamera() {
    if (camera) {
        camera.stop();
    }

    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }

    video.srcObject = null;
    outputCtx.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
    renderOverlay();
    updateCameraStatus('Sua câmera está desligada. Ative novamente para testar.', 'text-gray-500');
}

function simulateDownload() {
    window.location.href = '#test';
}

window.addEventListener('DOMContentLoaded', () => {
    renderOverlay();
    updateCameraStatus('Pronto para ativar a câmera. Sem necessidade de extensão.', 'text-green-400');
});
