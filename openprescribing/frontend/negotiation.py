from rest_framework.negotiation import DefaultContentNegotiation


class IgnoreAcceptsContentNegotiation(DefaultContentNegotiation):
    def select_parser(self, request, parsers):
        """
        Select the first parser in the `.parser_classes` list.
        """
        return parsers[0]

    def select_renderer(self, request, renderers, format_suffix=None):
        """
        Given a request and a list of renderers, return a two-tuple of:
        (renderer, media type).
        """
        # Allow URL style format override.  eg. "?format=json
        requested_format = format_suffix or request.query_params.get('format')
        found_html = False
        if requested_format:
            renderers = self.filter_renderers(renderers, requested_format)
        else:
            for renderer in renderers:
                if 'html' in renderer.media_type.lower():
                    found_html = True
                    break
        if not found_html:
            renderer = renderers[0]
        return renderer, renderer.media_type
