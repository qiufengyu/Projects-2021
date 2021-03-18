from django import forms


class TopNForm(forms.Form):
    your_name = forms.IntegerField(label='', min_value=1)