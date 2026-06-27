(function () {
    const LOG = "[oauth_provider.embed.debug]";
    const TOKEN_KEY = "oauth_provider_embed_token";

    function embedContext() {
        try {
            if (sessionStorage.getItem(TOKEN_KEY)) {
                return true;
            }
            if (new URLSearchParams(window.location.search).has("oauth_embed_token")) {
                return true;
            }
            return window.self !== window.top;
        } catch {
            return true;
        }
    }

    if (!embedContext()) {
        return;
    }

    let seq = 0;
    function log(event, detail) {
        seq += 1;
        let inIframe = false;
        try {
            inIframe = window.self !== window.top;
        } catch {
            inIframe = true;
        }
        console.warn(LOG, "#" + seq, event, Object.assign({ href: location.href, inIframe }, detail || {}));
    }

    log("boot");

    window.addEventListener("beforeunload", function () {
        log("beforeunload");
    });
    window.addEventListener("pagehide", function (ev) {
        log("pagehide", { persisted: ev.persisted });
    });
    window.addEventListener("pageshow", function (ev) {
        log("pageshow", { persisted: ev.persisted });
    });
    window.addEventListener("error", function (ev) {
        log("window.error", { message: ev.message, filename: ev.filename, lineno: ev.lineno });
    });
    window.addEventListener("unhandledrejection", function (ev) {
        log("unhandledrejection", { reason: String(ev.reason) });
    });

    const pushState = history.pushState.bind(history);
    history.pushState = function (state, title, url) {
        log("history.pushState", { url: url || "", title: title || "" });
        console.trace(LOG, "pushState stack");
        return pushState(state, title, url);
    };
    const replaceState = history.replaceState.bind(history);
    history.replaceState = function (state, title, url) {
        log("history.replaceState", { url: url || "", title: title || "" });
        console.trace(LOG, "replaceState stack");
        return replaceState(state, title, url);
    };

    try {
        const proto = window.Location.prototype;
        const desc = Object.getOwnPropertyDescriptor(proto, "reload");
        if (desc && desc.configurable) {
            const nativeReload = desc.value;
            Object.defineProperty(proto, "reload", {
                configurable: true,
                writable: true,
                value: function () {
                    log("Location.prototype.reload");
                    console.trace(LOG, "reload stack");
                    return nativeReload.apply(this, arguments);
                },
            });
        } else {
            log("reload-patch-skipped", { reason: "reload not configurable on Location.prototype" });
        }
    } catch (err) {
        log("reload-patch-skipped", { reason: String(err) });
    }

    window.__oauthEmbedDebugLog = log;
})();
