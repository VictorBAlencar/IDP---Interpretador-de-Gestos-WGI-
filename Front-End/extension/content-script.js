window.IGW_EXTENSION_INSTALLED = true;
document.documentElement.dataset.igwExtensionInstalled = 'true';
window.dispatchEvent(new CustomEvent('igwExtensionInstalled'));
