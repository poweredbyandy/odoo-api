(function () {
    const TOKEN_KEY = "oauth_provider_embed_token";
    const DB_KEY = "oauth_provider_embed_db";
    const TOKEN_HEADER = "X-OAuth-Embed-Token";
    const DB_HEADER = "X-OAuth-Embed-Db";

    function captureEmbedParamsFromUrl() {
        const params = new URLSearchParams(window.location.search);
        const token = params.get("oauth_embed_token");
        const db = params.get("db");
        if (token) {
            sessionStorage.setItem(TOKEN_KEY, token);
        }
        if (db) {
            sessionStorage.setItem(DB_KEY, db);
        }
    }

    function getToken() {
        return sessionStorage.getItem(TOKEN_KEY) || "";
    }

    function getDb() {
        return sessionStorage.getItem(DB_KEY) || "";
    }

    function decorateUrl(url) {
        const token = getToken();
        const db = getDb();
        if (!token || typeof url !== "string") {
            return url;
        }
        try {
            const parsed = new URL(url, window.location.origin);
            if (parsed.origin !== window.location.origin) {
                return url;
            }
            if (!parsed.searchParams.has("oauth_embed_token")) {
                parsed.searchParams.set("oauth_embed_token", token);
            }
            if (db && !parsed.searchParams.has("db")) {
                parsed.searchParams.set("db", db);
            }
            return parsed.pathname + parsed.search + parsed.hash;
        } catch {
            return url;
        }
    }

    function patchXHR() {
        const origOpen = XMLHttpRequest.prototype.open;
        const origSetHeader = XMLHttpRequest.prototype.setRequestHeader;
        const origSend = XMLHttpRequest.prototype.send;

        XMLHttpRequest.prototype.open = function (method, url, ...rest) {
            this._oauthEmbedDecoratedUrl =
                typeof url === "string" ? decorateUrl(url) : url;
            return origOpen.call(this, method, this._oauthEmbedDecoratedUrl, ...rest);
        };

        XMLHttpRequest.prototype.send = function (body) {
            const token = getToken();
            const db = getDb();
            if (token && this._oauthEmbedDecoratedUrl) {
                try {
                    const parsed = new URL(
                        this._oauthEmbedDecoratedUrl,
                        window.location.origin
                    );
                    if (parsed.origin === window.location.origin) {
                        origSetHeader.call(this, TOKEN_HEADER, token);
                        if (db) {
                            origSetHeader.call(this, DB_HEADER, db);
                        }
                    }
                } catch {
                    /* noop */
                }
            }
            return origSend.call(this, body);
        };
    }

    function patchFetch() {
        const origFetch = window.fetch.bind(window);
        window.fetch = function (input, init) {
            const token = getToken();
            const db = getDb();
            if (!token) {
                return origFetch(input, init);
            }
            let url = typeof input === "string" ? input : input?.url;
            if (!url) {
                return origFetch(input, init);
            }
            try {
                const parsed = new URL(url, window.location.origin);
                if (parsed.origin !== window.location.origin) {
                    return origFetch(input, init);
                }
                const nextInit = Object.assign({}, init);
                const headers = new Headers(
                    nextInit.headers ||
                        (input instanceof Request ? input.headers : undefined)
                );
                if (!headers.has(TOKEN_HEADER)) {
                    headers.set(TOKEN_HEADER, token);
                }
                if (db && !headers.has(DB_HEADER)) {
                    headers.set(DB_HEADER, db);
                }
                nextInit.headers = headers;
                if (typeof input === "string") {
                    return origFetch(decorateUrl(input), nextInit);
                }
                return origFetch(input, nextInit);
            } catch {
                return origFetch(input, init);
            }
        };
    }

    captureEmbedParamsFromUrl();
    patchXHR();
    patchFetch();
})();
