from datetime import date

from django import forms

from apps.escolas.models import Vinculo

from .models import Autor, Avaliacao, Configuracao, Emprestimo, Exemplar, Genero, Livro, Turma


class LivroForm(forms.ModelForm):
    class Meta:
        model = Livro
        fields = [
            'titulo', 'autores', 'editora', 'isbn', 'ano_publicacao', 'generos',
            'num_paginas', 'capa', 'sinopse', 'localizacao_prateleira',
        ]
        widgets = {
            'autores': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'generos': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'sinopse': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, escola=None, **kwargs):
        super().__init__(*args, **kwargs)
        escola = escola or getattr(self.instance, 'escola', None)
        self.fields['autores'].queryset = Autor.objects.filter(escola=escola)
        self.fields['generos'].queryset = Genero.objects.filter(escola=escola)


class ExemplarQuantidadeForm(forms.Form):
    quantidade = forms.IntegerField(min_value=1, initial=1, label='Quantidade de exemplares a adicionar')


class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ['codigo', 'ano_letivo', 'nivel', 'turno', 'ativa']


class AutorForm(forms.ModelForm):
    class Meta:
        model = Autor
        fields = ['nome', 'nacionalidade', 'biografia']


class GeneroForm(forms.ModelForm):
    class Meta:
        model = Genero
        fields = ['nome', 'descricao']


class EmprestimoCreateForm(forms.Form):
    vinculo = forms.ModelChoiceField(
        queryset=Vinculo.objects.none(),
        label='Aluno ou professor',
        widget=forms.HiddenInput(attrs={'class': 'usuario-busca-hidden'}),
    )
    livro = forms.ModelChoiceField(
        queryset=Livro.objects.none(), widget=forms.HiddenInput(attrs={'class': 'livro-busca-hidden'})
    )

    def __init__(self, *args, escola=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.escola = escola
        # Aluno/professor e livro são escolhidos via autocomplete (AJAX): os querysets
        # aqui só validam o id enviado — nunca são usados para renderizar opções.
        self.fields['vinculo'].queryset = Vinculo.objects.filter(
            escola=escola, ativo=True, tipo__in=[Vinculo.TIPO_ALUNO, Vinculo.TIPO_PROFESSOR]
        )
        self.fields['livro'].queryset = Livro.objects.filter(escola=escola, ativo=True)

    def vinculo_selecionado(self):
        valor = self['vinculo'].value()
        if not valor:
            return None
        return Vinculo.objects.filter(escola=self.escola, pk=valor).select_related('usuario').first()

    def livro_selecionado(self):
        valor = self['livro'].value()
        if not valor:
            return None
        return Livro.objects.filter(escola=self.escola, pk=valor).first()


class VinculoProfessorChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.email


class EmprestimoTurmaCreateForm(forms.Form):
    turma = forms.ModelChoiceField(queryset=Turma.objects.none(), label='Turma')
    professor_responsavel = VinculoProfessorChoiceField(queryset=Vinculo.objects.none(), label='Professor responsável')
    data_prevista_devolucao = forms.DateField(
        label='Data de devolução', initial=date.today, widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, *args, escola=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['turma'].queryset = Turma.objects.filter(escola=escola, ativa=True)
        self.fields['professor_responsavel'].queryset = (
            Vinculo.objects.filter(escola=escola, tipo=Vinculo.TIPO_PROFESSOR, ativo=True).select_related('usuario')
        )


class ItemEmprestimoTurmaForm(forms.Form):
    """Uma linha (livro + quantidade) do empréstimo de turma.

    O campo `livro` é preenchido via autocomplete (AJAX) no template — o widget
    escondido só carrega o id já escolhido, nunca o catálogo inteiro (ver
    LivroBuscaView), então a lista de livros pode crescer sem limite de linhas.
    """

    livro = forms.ModelChoiceField(
        queryset=Livro.objects.none(),
        required=False,
        widget=forms.HiddenInput(attrs={'class': 'livro-busca-hidden'}),
    )
    quantidade = forms.IntegerField(required=False, min_value=1, initial=1, label='Quantidade')

    def __init__(self, *args, escola=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.escola = escola
        self.fields['livro'].queryset = Livro.objects.filter(escola=escola, ativo=True)

    def livro_selecionado(self):
        valor = self['livro'].value()
        if not valor:
            return None
        return Livro.objects.filter(escola=self.escola, pk=valor).first()

    def clean(self):
        cleaned_data = super().clean()
        livro = cleaned_data.get('livro')
        quantidade = cleaned_data.get('quantidade')
        if livro and not quantidade:
            self.add_error('quantidade', 'Informe a quantidade.')
        return cleaned_data


class BaseItemEmprestimoTurmaFormSet(forms.BaseFormSet):
    def __init__(self, *args, escola=None, **kwargs):
        self.escola = escola
        super().__init__(*args, form_kwargs={'escola': escola}, **kwargs)

    def itens_selecionados(self):
        itens = []
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            livro = form.cleaned_data.get('livro')
            quantidade = form.cleaned_data.get('quantidade')
            if livro and quantidade:
                itens.append((livro, quantidade))
        return itens


ItemEmprestimoTurmaFormSet = forms.formset_factory(
    ItemEmprestimoTurmaForm, formset=BaseItemEmprestimoTurmaFormSet, extra=3, min_num=1, validate_min=True,
)


class RegistroLeituraForm(forms.Form):
    pagina_atual = forms.IntegerField(min_value=1, label='Página atual')


class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['nota', 'comentario']
        widgets = {
            'nota': forms.Select(choices=[(i, f'{i} estrela{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'comentario': forms.Textarea(attrs={'rows': 3, 'placeholder': 'O que você achou do livro?'}),
        }


class ConfiguracaoForm(forms.ModelForm):
    class Meta:
        model = Configuracao
        fields = [
            'prazo_emprestimo_aluno', 'prazo_emprestimo_professor', 'prazo_emprestimo_turma',
            'max_renovacoes', 'max_livros_aluno', 'max_livros_professor',
            'dias_lembrete_vencimento', 'max_dias_notificacao_atraso',
            'metodo_recuperacao_senha',
            'exigir_cpf_aluno', 'exigir_telefone_aluno',
            'exigir_data_nascimento_aluno', 'exigir_responsavel_aluno', 'exigir_matricula_aluno',
            'exigir_cpf_professor', 'exigir_telefone_professor', 'exigir_matricula_professor',
            'exigir_cpf_admin_biblioteca', 'exigir_telefone_admin_biblioteca',
            'exigir_registro_funcional_admin_biblioteca',
        ]
