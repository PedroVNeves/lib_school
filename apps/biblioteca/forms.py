from django import forms

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
    usuario_busca = forms.CharField(label='Matrícula ou e-mail do usuário')
    livro = forms.ModelChoiceField(queryset=Livro.objects.none())

    def __init__(self, *args, escola=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['livro'].queryset = Livro.objects.filter(escola=escola, ativo=True)


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
        ]
