from django import forms
from .models import Phone


class PhoneCompareForm(forms.Form):
    phone_one = forms.ModelChoiceField(
        queryset=Phone.objects.all(),
        widget=forms.Select(attrs={'onchange': 'form.submit();'}),
        empty_label='Выберите телефон',
        label='Первый телефон',
        required=False,
    ) 
    phone_two = forms.ModelChoiceField(
        queryset=Phone.objects.all(),
        widget=forms.Select(attrs={'onchange': 'form.submit();'}),
        empty_label='Выберите телефон',
        label='Второй телефон',
        required=False,
    )


class PhoneForm(forms.ModelForm):
    class Meta:
        model = Phone
        exclude = ['image', 'is_favorite']
