from django import forms
from django.contrib.auth.password_validation import validate_password

from apps.biblioteca.models import Configuracao, Turma
from apps.escolas.models import Vinculo

from .models import PerfilAdminBiblioteca, PerfilAluno, PerfilProfessor, Usuario
from .validators import validar_cpf


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

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        validar_cpf(cpf)
        return cpf

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
    matricula = forms.CharField(max_length=20, required=False)
    turma = forms.ModelChoiceField(queryset=Turma.objects.none(), required=False)
    data_nascimento = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    responsavel_nome = forms.CharField(max_length=200, required=False)
    responsavel_contato = forms.CharField(max_length=20, required=False)
    telefone = forms.CharField(max_length=20, required=False, label='Telefone')
    cpf = forms.CharField(max_length=14, required=False, label='CPF')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['turma'].queryset = Turma.objects.filter(escola=self.escola, ativa=True)

        config = Configuracao.get_solo(self.escola)
        self.fields['matricula'].required = config.exigir_matricula_aluno
        self.fields['cpf'].required = config.exigir_cpf_aluno
        self.fields['telefone'].required = config.exigir_telefone_aluno
        self.fields['data_nascimento'].required = config.exigir_data_nascimento_aluno
        self.fields['responsavel_nome'].required = config.exigir_responsavel_aluno
        self.fields['responsavel_contato'].required = config.exigir_responsavel_aluno

        if self.instance.pk:
            vinculo = self.instance.vinculos.filter(escola=self.escola).first()
            perfil = getattr(vinculo, 'perfil_aluno', None) if vinculo else None
            if perfil:
                self.fields['matricula'].initial = perfil.matricula
                self.fields['turma'].initial = perfil.turma
                self.fields['data_nascimento'].initial = perfil.data_nascimento
                self.fields['responsavel_nome'].initial = perfil.responsavel_nome
                self.fields['responsavel_contato'].initial = perfil.responsavel_contato
                self.fields['telefone'].initial = perfil.telefone
                self.fields['cpf'].initial = perfil.cpf

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        vinculo, _ = Vinculo.objects.get_or_create(
            usuario=usuario, escola=self.escola, defaults={'tipo': Vinculo.TIPO_ALUNO, 'ativo': True}
        )
        perfil, _ = PerfilAluno.objects.get_or_create(vinculo=vinculo)
        perfil.matricula = self.cleaned_data.get('matricula', '')
        perfil.turma = self.cleaned_data.get('turma')
        perfil.data_nascimento = self.cleaned_data.get('data_nascimento')
        perfil.responsavel_nome = self.cleaned_data.get('responsavel_nome', '')
        perfil.responsavel_contato = self.cleaned_data.get('responsavel_contato', '')
        perfil.telefone = self.cleaned_data.get('telefone', '')
        perfil.cpf = self.cleaned_data.get('cpf', '')
        perfil.save()
        vinculo.save()
        self.instance = usuario
        return usuario


class ProfessorForm(BaseUsuarioForm):
    matricula_funcional = forms.CharField(max_length=20, required=False)
    disciplinas = forms.CharField(max_length=500, required=False)
    turmas = forms.ModelMultipleChoiceField(queryset=Turma.objects.none(), required=False)
    telefone = forms.CharField(max_length=20, required=False, label='Telefone')
    cpf = forms.CharField(max_length=14, required=False, label='CPF')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['turmas'].queryset = Turma.objects.filter(escola=self.escola, ativa=True)

        config = Configuracao.get_solo(self.escola)
        self.fields['matricula_funcional'].required = config.exigir_matricula_professor
        self.fields['cpf'].required = config.exigir_cpf_professor
        self.fields['telefone'].required = config.exigir_telefone_professor

        if self.instance.pk:
            vinculo = self.instance.vinculos.filter(escola=self.escola).first()
            perfil = getattr(vinculo, 'perfil_professor', None) if vinculo else None
            if perfil:
                self.fields['matricula_funcional'].initial = perfil.matricula_funcional
                self.fields['disciplinas'].initial = perfil.disciplinas
                self.fields['turmas'].initial = perfil.turmas.all()
                self.fields['telefone'].initial = perfil.telefone
                self.fields['cpf'].initial = perfil.cpf

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        vinculo, _ = Vinculo.objects.get_or_create(
            usuario=usuario, escola=self.escola, defaults={'tipo': Vinculo.TIPO_PROFESSOR, 'ativo': True}
        )
        perfil, _ = PerfilProfessor.objects.get_or_create(vinculo=vinculo)
        perfil.matricula_funcional = self.cleaned_data.get('matricula_funcional', '')
        perfil.disciplinas = self.cleaned_data.get('disciplinas', '')
        perfil.telefone = self.cleaned_data.get('telefone', '')
        perfil.cpf = self.cleaned_data.get('cpf', '')
        perfil.save()
        perfil.turmas.set(self.cleaned_data.get('turmas') or [])
        vinculo.save()
        self.instance = usuario
        return usuario


class AdminBibliotecaForm(BaseUsuarioForm):
    registro_funcional = forms.CharField(max_length=20, required=False)
    telefone = forms.CharField(max_length=20, required=False, label='Telefone')
    cpf = forms.CharField(max_length=14, required=False, label='CPF')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        config = Configuracao.get_solo(self.escola)
        self.fields['registro_funcional'].required = config.exigir_registro_funcional_admin_biblioteca
        self.fields['cpf'].required = config.exigir_cpf_admin_biblioteca
        self.fields['telefone'].required = config.exigir_telefone_admin_biblioteca

        if self.instance.pk:
            vinculo = self.instance.vinculos.filter(escola=self.escola).first()
            perfil = getattr(vinculo, 'perfil_biblioteca', None) if vinculo else None
            if perfil:
                self.fields['registro_funcional'].initial = perfil.registro_funcional
                self.fields['telefone'].initial = perfil.telefone
                self.fields['cpf'].initial = perfil.cpf

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        vinculo, _ = Vinculo.objects.get_or_create(
            usuario=usuario, escola=self.escola, defaults={'tipo': Vinculo.TIPO_ADMIN_BIBLIOTECA, 'ativo': True}
        )
        perfil, _ = PerfilAdminBiblioteca.objects.get_or_create(vinculo=vinculo)
        perfil.registro_funcional = self.cleaned_data.get('registro_funcional', '')
        perfil.telefone = self.cleaned_data.get('telefone', '')
        perfil.cpf = self.cleaned_data.get('cpf', '')
        perfil.save()
        vinculo.save()
        self.instance = usuario
        return usuario
