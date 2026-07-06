from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PerfilAdminBiblioteca, PerfilAluno, PerfilProfessor, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'is_super_admin', 'is_staff']
    list_filter = ['is_super_admin', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Dados do Sistema', {'fields': ('foto', 'is_super_admin')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dados do Sistema', {'fields': ('email',)}),
    )


admin.site.register(PerfilAluno)
admin.site.register(PerfilProfessor)
admin.site.register(PerfilAdminBiblioteca)
