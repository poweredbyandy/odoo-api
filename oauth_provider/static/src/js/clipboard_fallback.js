/** @odoo-module **/

async function writeTextFallback(text) {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    if (!ok) {
        throw new Error("clipboard copy failed");
    }
}

function ensureNavigatorClipboard() {
    const nav = window.navigator;
    if (!nav || nav.clipboard?.writeText) {
        return;
    }
    const clipboard = {
        writeText(text) {
            return writeTextFallback(String(text));
        },
        write(data) {
            if (typeof data === "string") {
                return writeTextFallback(data);
            }
            return Promise.reject(new Error("clipboard.write unavailable"));
        },
        readText() {
            return Promise.reject(new Error("clipboard.readText unavailable"));
        },
    };
    try {
        Object.defineProperty(nav, "clipboard", {
            value: clipboard,
            configurable: true,
        });
    } catch {
        try {
            nav.clipboard = clipboard;
        } catch {
        }
    }
}

ensureNavigatorClipboard();
