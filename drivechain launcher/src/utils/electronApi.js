function getElectronAPI() {
    return window?.electronAPI;
}

export function getMasterWallet() {
    return getElectronAPI()?.getMasterWallet?.() ?? Promise.resolve(null);
}

export function notifyReady() {
    getElectronAPI()?.notifyReady?.();
}

export function onDownloadsInProgress(callback) {
    return getElectronAPI()?.onDownloadsInProgress?.(callback) ?? (() => { });
}

export function forceQuitWithDownloads() {
    getElectronAPI()?.forceQuitWithDownloads?.();
}

export function isRunningInElectron() {
    return !!getElectronAPI();
}
  