/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

const LOG = "[oauth_provider.embed.debug]";

function embedContext() {
    try {
        if (sessionStorage.getItem("oauth_provider_embed_token")) {
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

function trace(event, detail = {}) {
    const logFn = window.__oauthEmbedDebugLog || console.warn.bind(console, LOG);
    logFn(event, detail);
}

if (embedContext()) {
    trace("module-init");

    try {
        const origRpc = rpc._rpc;
        rpc._rpc = function (url, params, settings) {
            return origRpc.call(this, url, params, settings).catch((error) => {
                if (
                    error?.exceptionName === "odoo.http.SessionExpiredException" ||
                    error?.data?.name === "odoo.http.SessionExpiredException"
                ) {
                    trace("rpc SessionExpiredException", { url });
                }
                throw error;
            });
        };
    } catch (err) {
        trace("rpc-patch-skipped", { reason: String(err) });
    }

    const watchMenus = () => {
        const promise = window.odoo?.loadMenusPromise;
        if (!promise || typeof promise.then !== "function") {
            window.setTimeout(watchMenus, 30);
            return;
        }
        promise.then(
            (menus) => {
                trace("loadMenusPromise resolved", {
                    menuCount: menus ? Object.keys(menus).length : 0,
                });
            },
            (error) => {
                trace("loadMenusPromise rejected", { error: String(error) });
            }
        );
    };
    watchMenus();
}
