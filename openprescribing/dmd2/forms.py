from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder, Submit
from crispy_forms.bootstrap import InlineCheckboxes


obj_types_choices = [
    ('vtm', 'VTMs'),
    ('vmp', 'VMPs'),
    ('amp', 'AMPs'),
    ('vmpp', 'VMPPs'),
    ('ampp', 'AMPPs'),
]

include_choices = [
    ('unavailable', 'Unavailable items'),
    ('invalid', 'Invalid items'),
    ('no_bnf_code', 'Items with no BNF code'),
]

class SearchForm(forms.Form):
    q = forms.CharField(
        label='Query or SNOMED code',
        min_length=3,
    )
    obj_types = forms.MultipleChoiceField(
        label='Search...',
        choices=obj_types_choices,
        required=False,
        initial=[tpl[0] for tpl in obj_types_choices],
    )
    include = forms.MultipleChoiceField(
        label='Include...',
        choices=include_choices,
        required=False,
        help_text='Unavailable items are not available to be prescribed and/or have been discontinued.',
    )

    # This is only used in tests
    max_results_per_obj_type = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Field('q'),
            InlineCheckboxes('obj_types'),
            InlineCheckboxes('include'),
            ButtonHolder(
                Submit('submit', 'Search'),
            )
        )
