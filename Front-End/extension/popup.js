document.addEventListener('DOMContentLoaded', function() {
    const btnTestCamera = document.getElementById('btn-test-camera');
    const btnSettings = document.getElementById('btn-settings');
    const extensionStatus = document.getElementById('extension-status');

    // Verificar se a extensão está funcionando
    extensionStatus.textContent = '✓ Extensão Ativa';
    extensionStatus.className = 'status active';

    // Botão de testar câmera
    btnTestCamera.addEventListener('click', async function() {
        try {
            // Abrir uma nova aba com a página de teste
            const tab = await chrome.tabs.create({
                url: chrome.runtime.getURL('../Interface/arquiteto.html')
            });

            // Fechar o popup
            window.close();
        } catch (error) {
            console.error('Erro ao abrir página de teste:', error);
            alert('Erro ao abrir página de teste. Verifique as permissões da extensão.');
        }
    });

    // Botão de configurações
    btnSettings.addEventListener('click', function() {
        // Abrir página de configurações (se existir)
        alert('Configurações ainda não implementadas. Em breve!');
    });

    // Verificar permissões da câmera
    navigator.permissions.query({ name: 'camera' }).then(function(result) {
        if (result.state === 'denied') {
            extensionStatus.textContent = '⚠ Permissões necessárias';
            extensionStatus.className = 'status inactive';
        }
    }).catch(function(error) {
        console.log('Erro ao verificar permissões:', error);
    });
});