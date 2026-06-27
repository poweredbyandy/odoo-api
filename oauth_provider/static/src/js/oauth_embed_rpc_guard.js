/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import {
    ConnectionAbortedError,
    rpc,
} from "@web/core/network/rpc";

const ORIG_RPC = rpc._rpc;

function isEmbeddedIframe() {
    try {
        return window.self !== window.top;
    } catch {
        return true;
    }
}

function isSessionExpiredError(error) {
    return (
        error?.exceptionName === "odoo.http.SessionExpiredException" ||
        error?.data?.name === "odoo.http.SessionExpiredException"
    );
}

let sessionExpiredCircuitOpen = false;
const embeddedIframe = isEmbeddedIframe();

rpc._rpc = function patchedEmbedRpc(url, params, settings) {
    if (embeddedIframe && sessionExpiredCircuitOpen) {
        return Promise.reject(
            new ConnectionAbortedError("Sesión embebida expirada.")
        );
    }
    return ORIG_RPC.call(this, url, params, settings).catch((error) => {
        if (embeddedIframe && isSessionExpiredError(error)) {
            sessionExpiredCircuitOpen = true;
            throw error;
        }
        throw error;
    });
};
