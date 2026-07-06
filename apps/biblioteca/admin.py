from django.contrib import admin

from .models import (
    AuditLog,
    Autor,
    Configuracao,
    Emprestimo,
    EmprestimoTurma,
    Exemplar,
    Genero,
    ItemEmprestimoTurma,
    Livro,
    Renovacao,
    Turma,
)


class ExemplarInline(admin.TabularInline):
    model = Exemplar
    extra = 0


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'escola', 'isbn', 'exemplares_disponiveis', 'total_exemplares', 'ativo']
    search_fields = ['titulo', 'isbn']
    list_filter = ['escola', 'ativo', 'generos']
    inlines = [ExemplarInline]


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'escola', 'livro', 'data_prevista_devolucao', 'status']
    list_filter = ['escola', 'status']
    search_fields = ['usuario__email', 'livro__titulo']


admin.site.register(Turma)
admin.site.register(Autor)
admin.site.register(Genero)
admin.site.register(Exemplar)
admin.site.register(Renovacao)
admin.site.register(EmprestimoTurma)
admin.site.register(ItemEmprestimoTurma)
admin.site.register(Configuracao)
admin.site.register(AuditLog)
