from datetime import date

from django import forms

from apps.escolas.models import Vinculo

from .models import Autor, Avaliacao, Configuracao, Emprestimo, Exemplar, Genero, Livro, Turma

NUM_LINHAS_EMPRESTIMO_TURMA = 6


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
    usuario_busca = forms.CharField(label='Matrícula ou e-mail do usuário')
    livro = forms.ModelChoiceField(queryset=Livro.objects.none())

    def __init__(self, *args, escola=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['livro'].queryset = Livro.objects.filter(escola=escola, ativo=True)


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
        livros_qs = Livro.objects.filter(escola=escola, ativo=True)
        for i in range(1, NUM_LINHAS_EMPRESTIMO_TURMA + 1):
            self.fields[f'livro_{i}'] = forms.ModelChoiceField(queryset=livros_qs, required=False, label=f'Livro {i}')
            self.fields[f'quantidade_{i}'] = forms.IntegerField(
                required=False, min_value=1, initial=1, label='Quantidade'
            )

    def itens_selecionados(self):
        itens = []
        for i in range(1, NUM_LINHAS_EMPRESTIMO_TURMA + 1):
            livro = self.cleaned_data.get(f'livro_{i}')
            quantidade = self.cleaned_data.get(f'quantidade_{i}')
            if livro and quantidade:
                itens.append((livro, quantidade))
        return itens


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
