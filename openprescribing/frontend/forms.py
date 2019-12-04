import urllib.parse
from django import forms
from django.utils.safestring import mark_safe


def _name_with_url(bookmark):
    html = '<a href="%s">%s</a>' % (bookmark.dashboard_url(), bookmark.name)
    return mark_safe(html)


class BookmarkListForm(forms.Form):
    org_bookmarks = forms.MultipleChoiceField(
        label="Alerts about organisations", widget=forms.CheckboxSelectMultiple()
    )
    search_bookmarks = forms.MultipleChoiceField(
        label="Alerts about searches", widget=forms.CheckboxSelectMultiple()
    )
    ncso_concessions_bookmarks = forms.MultipleChoiceField(
        label="Alerts about NCSO price concessions",
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, *args, **kwargs):
        """Populate choices with those passed in, and remove fields with no
        choices.

        """
        org_bookmarks = kwargs.pop("org_bookmarks", [])
        search_bookmarks = kwargs.pop("search_bookmarks", [])
        ncso_concessions_bookmarks = kwargs.pop("ncso_concessions_bookmarks", [])
        super(BookmarkListForm, self).__init__(*args, **kwargs)
        if org_bookmarks:
            self.fields["org_bookmarks"].choices = [
                (x.id, _name_with_url(x)) for x in org_bookmarks
            ]
        else:
            del self.fields["org_bookmarks"]
        if search_bookmarks:
            self.fields["search_bookmarks"].choices = [
                (x.id, _name_with_url(x)) for x in search_bookmarks
            ]
        else:
            del self.fields["search_bookmarks"]
        if ncso_concessions_bookmarks:
            self.fields["ncso_concessions_bookmarks"].choices = [
                (x.id, _name_with_url(x)) for x in ncso_concessions_bookmarks
            ]
        else:
            del self.fields["ncso_concessions_bookmarks"]


class SearchBookmarkForm(forms.Form):
    email = forms.EmailField(
        label="",
        error_messages={
            "required": "This can't be blank!",
            "invalid": "Please enter a valid email address",
        },
        widget=forms.TextInput(attrs={"placeholder": "Email address", "size": "35"}),
    )
    url = forms.CharField(widget=forms.HiddenInput(), required=True)
    name = forms.CharField(widget=forms.HiddenInput(), required=True)

    def clean_name(self):
        name = self.cleaned_data["name"]
        return urllib.parse.unquote(name)

    def clean_url(self):
        url = self.cleaned_data["url"]
        return urllib.parse.unquote(url)


class OrgBookmarkForm(forms.Form):
    email = forms.EmailField(
        label="",
        error_messages={
            "required": "This can't be blank!",
            "invalid": "Please enter a valid email address",
        },
        widget=forms.TextInput(attrs={"placeholder": "Email address", "size": "35"}),
    )
    pct_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    practice_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    pcn_id = forms.CharField(widget=forms.HiddenInput(), required=False)


class FeedbackForm(forms.Form):

    # This incredibly crude captcha technique has proved enough in the past to
    # deter spam bots which blindly fill out any contact form they can find
    HUMAN_TEST_ANSWER = "health"

    email = forms.EmailField()
    name = forms.CharField()
    subject = forms.CharField()
    human_test = forms.CharField(
        label='Please type the word "{}" to show you\'re not a robot'.format(
            HUMAN_TEST_ANSWER
        )
    )
    message = forms.CharField(widget=forms.Textarea)

    def clean_human_test(self):
        data = self.cleaned_data["human_test"]
        if data.strip().lower() != self.HUMAN_TEST_ANSWER:
            raise forms.ValidationError(
                'Sorry, you need to put the word "{}" here'.format(
                    self.HUMAN_TEST_ANSWER
                )
            )
