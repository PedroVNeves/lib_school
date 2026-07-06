from django import forms

from .models import Escola


class EscolaForm(forms.ModelForm):
    class Meta:
        model = Escola
        fields = ['nome', 'cnpj', 'endereco', 'telefone', 'email_contato', 'logo']
