/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { standardErrorDialogProps } from "@web/core/errors/error_dialogs";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

function isEmbeddedIframe() {
    try {
        return window.self !== window.top;
    } catch {
        return true;
    }
}

class OAuthEmbedSessionExpiredDialog extends Component {
    static template = "web.SessionExpiredDialog";
    static components = { Dialog };
    static props = { ...standardErrorDialogProps };

    onClick() {
        if (isEmbeddedIframe()) {
            console.warn(
                "[oauth_provider.embed.debug]",
                "SessionExpired dialog cerrado en iframe (sin reload)"
            );
            this.props.close();
            return;
        }
        console.warn("[oauth_provider.embed.debug]", "SessionExpired dialog → reload");
        browser.location.reload();
    }
}

registry
    .category("error_dialogs")
    .add("odoo.http.SessionExpiredException", OAuthEmbedSessionExpiredDialog, {
        force: true,
    });
