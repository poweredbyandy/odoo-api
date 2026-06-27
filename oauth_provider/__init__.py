from . import controllers
from .hooks import post_init_hook
from . import models
from .http_patch import patch_request_validate_csrf_for_embed

patch_request_validate_csrf_for_embed()
