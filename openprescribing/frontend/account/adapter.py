from allauth.account.adapter import DefaultAccountAdapter


class MessageBlockingAdapter(DefaultAccountAdapter):
    def add_message(self, *args, **kw):
        """For now, we don't want messages appearing for the end user unless
        we specify them

        """
        pass
