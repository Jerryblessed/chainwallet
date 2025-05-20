import getPort from "get-port";
import { exec } from "child_process";
import { platform } from "os";

const DEFAULT_PORT = 3000;

(async () => {
    try {
        const port = await getPort({ port: DEFAULT_PORT });
        console.log(`✅ Starting app on available port ${port}`);

        const command = platform() === "win32"
            ? `set PORT=${port} && npm run react-start`
            : `PORT=${port} npm run react-start`;

        const child = exec(command, { stdio: "inherit", shell: true });

        if (child.stdout) child.stdout.pipe(process.stdout);
        if (child.stderr) child.stderr.pipe(process.stderr);
    } catch (err) {
        console.error("❌ Failed to find an available port:", err);
        process.exit(1);
    }
})();
