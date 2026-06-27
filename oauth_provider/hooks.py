def post_init_hook(env):
    if "auth.oauth.provider" not in env.registry.models:
        return
    provider = env.ref("auth_oauth.provider_openerp", raise_if_not_found=False)
    if provider:
        provider.sudo().write({"enabled": False})
