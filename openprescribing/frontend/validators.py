from django.core.validators import RegexValidator
'''
This regex assumes that you have a clean string,
you should clean the string for spaces and other characters
'''
isAlphaNumeric = RegexValidator(
    r'^[\w]*$', message='name must be alphanumeric', code='Invalid name')
