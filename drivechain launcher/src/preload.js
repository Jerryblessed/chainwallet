const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    onDownloadsInProgress: (callback) => ipcRenderer.on('downloads-in-progress', (_, data) => callback(data)),
    getMasterWallet: () => ipcRenderer.invoke('get-master-wallet'),
    notifyReady: () => ipcRenderer.send('notify-ready'),
    forceQuitWithDownloads: () => ipcRenderer.send('force-quit-downloads'),
});
