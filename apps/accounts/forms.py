from django import forms
from django.contrib.auth.password_validation import validate_password

from apps.biblioteca.models import Turma
from apps.escolas.models import Vinculo

from .models import PerfilAdminBiblioteca, PerfilAluno, PerfilProfessor, Usuario


class BaseUsuarioForm(forms.ModelForm):
    senha = forms.CharField(
        label='Senha', widget=forms.PasswordInput, required=False,
        help_text='Deixe em branco para manter a senha atual (edição) ou se a pessoa já tiver conta em outra escola.',
    )

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'username']
        labels = {'first_name': 'Nome', 'last_name': 'Sobrenome', 'username': 'Usuário (login alternativo)'}

    def __init__(self, *args, escola=None, **kwargs):
        self.escola = escola
        self._usuario_existente = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        email = cleaned_data.get('email')

        if not self.instance.pk and email:
            existente = Usuario.objects.filter(email__iexact=email).first()
            if existente:
                if existente.vinculos.filter(escola=self.escola).exists():
                    raise forms.ValidationError('Esta pessoa já possui vínculo com esta escola.')
                self._usuario_existente = existente

        if not self.instance.pk and not senha and not self._usuario_existente:
            self.add_error('senha', 'A senha é obrigatória para novos usuários.')
        if senha:
            validate_password(senha)
        return cleaned_data

    def _post_clean(self):
        if self._usuario_existente:
            return
        super()._post_clean()

    def save(self, commit=True):
        usuario = self._usuario_existente or super().save(commit=False)
        senha = self.cleaned_data.get('senha')
        if senha:
            usuario.set_password(senha)
        if commit:
            usuario.save()
        return usuario


class AlunoForm(BaseUsuarioForm):
    matricula = forms.CharField(max_length=20)
    turma = forms.ModelChoiceField(queryset=Turma.objects.none(), required=False)
    data_nascimento = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    responsavel_nome = forms.CharField(max_length=200, required=False)
    responsavel_contato = forms.CharField(max_length=20, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['turma'].queryset = Turma.objects.filter(escola=self.escola, ativa=True)
        if self.instance.pk:
            vinculo = self.instance.vinculos.filter(escola=self.escola).first()
            perfil = getattr(vinculo, 'perfil_aluno', None) if vinculo else None
            if perfil:
                self.fields['matricula'].initial = perfil.matricula
                self.fields['turma'].initial = perfil.turma
                self.fields['data_nascimento'].initial = perfil.data_nascimento
                self.fields['responsavel_nome'].initial = perfil.responsavel_nome
                self.fields['responsavel_contato'].initial = perfil.responsavel_contato

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        vinculo, _ = Vinculo.objects.get_or_create(
            usuario=usuario, escola=self.escola, defaults={'tipo': Vinculo.TIPO_ALUNO, 'ativo': True}
        )
        perfil, _ = PerfilAluno.objects.get_or_create(vinculo=vinculo)
        perfil.matricula = self.cleaned_data['matricula']
        perfil.turma = self.cleaned_data.get('turma')
        perfil.data_nascimento = self.cleaned_data.get('data_nascimento')
        perfil.responsavel_nome = self.cleaned_data.get('responsavel_nome', '')
        perfil.responsavel_contato = self.cleaned_data.get('responsavel_contato', '')
        perfil.save()
        self.instance = usuario
        return usuario


class ProfessorForm(BaseUsuarioForm):
    matricula_funcional = forms.CharField(max_length=20)
    disciplinas = forms.CharField(max_length=500, required=False)
    turmas = forms.ModelMultipleChoiceField(queryset=Turma.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['turmas'].queryset = Turma.objects.filter(escola=self.escola, ativa=True)
        if self.instance.pk:
            vinculo = self.instance.vinculos.filter(escola=self.escola).first()
            perfil = getattr(vinculo, 'perfil_professor', None) if vinculo else None
            if perfil:
                self.fields['matricula_funcional'].initial = perfil.matricula_funcional
                self.fields['disciplinas'].initial = perfil.disciplinas
                self.fields['turmas'].initial = perfil.turmas.all()

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        vinculo, _ = Vinculo.objects.get_or_create(
            usuario=usuario, escola=self.escola, defaults={'tipo': Vinculo.TIPO_PROFESSOR, 'ativo': True}
        )
        perfil, _ = PerfilProfessor.objects.get_or_create(vinculo=vinculo)
        perfil.matricula_funcional = self.cleaned_data['matricula_funcional']
        perfil.disciplinas = self.cleaned_data.get('disciplinas', '')
        perfil.save()
        perfil.turmas.set(self.cleaned_data.get('turmas') or [])
        self.instance = usuario
        return usuario


class AdminBibliotecaForm(BaseUsuarioForm):
    registro_funcional = forms.CharField(max_length=20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            vinculo = self.instance.vinculos.filter(escola=self.escola).first()
            perfil = getattr(vinculo, 'perfil_biblioteca', None) if vinculo else None
            if perfil:
                self.fields['registro_funcional'].initial = perfil.registro_funcional

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        vinculo, _ = Vinculo.objects.get_or_create(
            usuario=usuario, escola=self.escola, defaults={'tipo': Vinculo.TIPO_ADMIN_BIBLIOTECA, 'ativo': True}
        )
        perfil, _ = PerfilAdminBiblioteca.objects.get_or_create(vinculo=vinculo)
        perfil.registro_funcional = self.cleaned_data['registro_funcional']
        perfil.save()
        self.instance = usuario
        return usuario
