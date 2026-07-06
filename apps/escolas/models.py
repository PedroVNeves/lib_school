from django.conf import settings
from django.db import models


class Escola(models.Model):
    nome = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=20, unique=True, null=True, blank=True)
    endereco = models.CharField(max_length=500, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email_contato = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='escolas/', null=True, blank=True)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Vinculo(models.Model):
    TIPO_ADMIN_GERAL = 'admin_geral'
    TIPO_ADMIN_BIBLIOTECA = 'admin_biblioteca'
    TIPO_PROFESSOR = 'professor'
    TIPO_ALUNO = 'aluno'

    TIPO_CHOICES = [
        (TIPO_ADMIN_GERAL, 'Admin Geral'),
        (TIPO_ADMIN_BIBLIOTECA, 'Admin Biblioteca'),
        (TIPO_PROFESSOR, 'Professor'),
        (TIPO_ALUNO, 'Aluno'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vinculos')
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='vinculos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['usuario', 'escola']
        ordering = ['escola__nome']

    def __str__(self):
        return f'{self.usuario} @ {self.escola} ({self.get_tipo_display()})'
