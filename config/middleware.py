from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.middleware.csrf import CsrfViewMiddleware


class LocalPreviewCsrfViewMiddleware(CsrfViewMiddleware):
    """Allow opaque origins only for local DEBUG previews; token checks remain on."""

    def _origin_verified(self, request):
        if (
            settings.ALLOW_NULL_ORIGIN_FOR_LOCAL_DEBUG
            and request.META.get('HTTP_ORIGIN') == 'null'
        ):
            try:
                host = request.get_host()
            except DisallowedHost:
                return False
            hostname = urlsplit(f'//{host}').hostname
            if hostname in {'localhost', '127.0.0.1', '::1'}:
                return True
        return super()._origin_verified(request)
