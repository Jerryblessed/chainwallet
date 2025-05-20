const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'), // for window.electronAPI
            contextIsolation: true,
            nodeIntegration: false,
        },
    });

    win.loadURL('http://localhost:3001'); // while developing
}

app.whenReady().then(createWindow);
