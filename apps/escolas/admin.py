from django.contrib import admin

from .models import Escola, Vinculo


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'ativa', 'criado_em']
    list_filter = ['ativa']
    search_fields = ['nome', 'cnpj']


@admin.register(Vinculo)
class VinculoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'escola', 'tipo', 'ativo']
    list_filter = ['escola', 'tipo', 'ativo']
    search_fields = ['usuario__email', 'escola__nome']
