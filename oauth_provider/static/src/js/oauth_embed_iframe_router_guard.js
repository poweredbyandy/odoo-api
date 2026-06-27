/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { cookie } from "@web/core/browser/cookie";
import { router } from "@web/core/browser/router";
import { WebClient } from "@web/webclient/webclient";

const LOG = "[oauth_provider.embed.guard]";
const TOKEN_KEY = "oauth_provider_embed_token";
const DB_KEY = "oauth_provider_embed_db";
const COLOR_SCHEME_KEY = "oauth_provider_color_scheme";
const EMBED_LOCATION_MSG = "oauth_provider_embed_location";

function embedLocationPath() {
    try {
        const parsed = new URL(window.location.href);
        parsed.searchParams.delete("oauth_embed_token");
        return parsed.pathname + parsed.search + parsed.hash;
    } catch {
        return window.location.pathname + window.location.search + window.location.hash;
    }
}

function isPersistableEmbedPath(path) {
    if (!path) {
        return false;
    }
    try {
        const parsed = new URL(path, window.location.origin);
        const pathname = parsed.pathname || "";
        if (
            pathname.startsWith("/oauth_provider/") ||
            pathname === "/web/login" ||
            pathname === "/web/database/selector"
        ) {
            return false;
        }
        if (pathname === "/web") {
            return false;
        }
        if (pathname === "/odoo" || pathname === "/odoo/") {
            return false;
        }
        return pathname.startsWith("/odoo/") && pathname.length > "/odoo/".length;
    } catch {
        return false;
    }
}

function notifyParentEmbedLocation() {
    try {
        if (window.self === window.top) {
            return;
        }
        const path = embedLocationPath();
        if (!isPersistableEmbedPath(path)) {
            return;
        }
        window.parent.postMessage(
            {
                type: EMBED_LOCATION_MSG,
                path,
            },
            "*"
        );
    } catch {
        /* noop */
    }
}

let _notifyParentTimer = null;
function scheduleNotifyParentEmbedLocation() {
    browser.clearTimeout(_notifyParentTimer);
    _notifyParentTimer = browser.setTimeout(notifyParentEmbedLocation, 300);
}

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

function appendEmbedQueryToPath(path) {
    const token = sessionStorage.getItem(TOKEN_KEY);
    const db = sessionStorage.getItem(DB_KEY);
    if (!token || !path) {
        return path;
    }
    try {
        const parsed = new URL(path, window.location.origin);
        if (!parsed.searchParams.has("oauth_embed_token")) {
            parsed.searchParams.set("oauth_embed_token", token);
        }
        if (db && !parsed.searchParams.has("db")) {
            parsed.searchParams.set("db", db);
        }
        return parsed.pathname + parsed.search + parsed.hash;
    } catch {
        return path;
    }
}

function isOAuthProviderShellPath() {
    return (window.location.pathname || "").startsWith("/oauth_provider/");
}

function stripReloadOption(options) {
    if (!options?.reload) {
        return options;
    }
    console.warn(LOG, "router reload suprimido");
    return { ...options, reload: false };
}

function resolvedColorScheme() {
    const stored = browser.sessionStorage.getItem(COLOR_SCHEME_KEY);
    if (stored) {
        return stored;
    }
    const scheme = browser.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    browser.sessionStorage.setItem(COLOR_SCHEME_KEY, scheme);
    return scheme;
}

if (embedContext()) {
    patch(cookie, {
        get(key) {
            const value = super.get(...arguments);
            if (key === "color_scheme" && !value) {
                return resolvedColorScheme();
            }
            return value;
        },
        set(key, value) {
            if (key === "color_scheme") {
                browser.sessionStorage.setItem(COLOR_SCHEME_KEY, value);
            }
            return super.set(...arguments);
        },
    });

    const nativeLocation = window.location;
    Object.defineProperty(browser, "location", {
        configurable: true,
        get() {
            return new Proxy(nativeLocation, {
                get(target, prop) {
                    if (prop === "reload") {
                        return function () {
                            console.warn(LOG, "location.reload suprimido en embed");
                            console.trace(LOG);
                        };
                    }
                    const value = target[prop];
                    if (typeof value === "function") {
                        return value.bind(target);
                    }
                    return value;
                },
                set(target, prop, value) {
                    target[prop] = value;
                    return true;
                },
            });
        },
        set(val) {
            window.location = val;
        },
    });

    const baseStateToUrl = router.stateToUrl.bind(router);
    const basePushState = router.pushState.bind(router);
    const baseReplaceState = router.replaceState.bind(router);

    patch(router, {
        stateToUrl(state) {
            return appendEmbedQueryToPath(baseStateToUrl(state));
        },
        pushState(state, options) {
            const ret = basePushState(state, stripReloadOption(options));
            scheduleNotifyParentEmbedLocation();
            return ret;
        },
        replaceState(state, options) {
            const ret = baseReplaceState(state, stripReloadOption(options));
            scheduleNotifyParentEmbedLocation();
            return ret;
        },
    });

    browser.addEventListener("popstate", scheduleNotifyParentEmbedLocation);

    patch(WebClient.prototype, {
        registerServiceWorker() {},
        async _loadDefaultApp() {
            if (embedContext() && isOAuthProviderShellPath()) {
                return;
            }
            return super._loadDefaultApp(...arguments);
        },
    });
}
