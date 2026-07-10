from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    foto = models.ImageField(upload_to='usuarios/', null=True, blank=True)
    is_super_admin = models.BooleanField(
        default=False, help_text='Administrador do produto: cadastra e gerencia escolas, não pertence a nenhuma.'
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.get_full_name() or self.username


class PerfilAluno(models.Model):
    vinculo = models.OneToOneField('escolas.Vinculo', on_delete=models.CASCADE, related_name='perfil_aluno')
    matricula = models.CharField(max_length=20)
    turma = models.ForeignKey('biblioteca.Turma', on_delete=models.SET_NULL, null=True, blank=True, related_name='alunos')
    data_nascimento = models.DateField(null=True, blank=True)
    responsavel_nome = models.CharField(max_length=200, blank=True)
    responsavel_contato = models.CharField(max_length=20, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    cpf = models.CharField(max_length=14, blank=True)

    class Meta:
        unique_together = ['vinculo', 'matricula']

    def __str__(self):
        return f'{self.vinculo.usuario.get_full_name()} - {self.matricula}'


class PerfilProfessor(models.Model):
    vinculo = models.OneToOneField('escolas.Vinculo', on_delete=models.CASCADE, related_name='perfil_professor')
    matricula_funcional = models.CharField(max_length=20)
    disciplinas = models.CharField(max_length=500, blank=True)
    turmas = models.ManyToManyField('biblioteca.Turma', related_name='professores', blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    cpf = models.CharField(max_length=14, blank=True)

    class Meta:
        unique_together = ['vinculo', 'matricula_funcional']

    def __str__(self):
        return f'{self.vinculo.usuario.get_full_name()} - {self.matricula_funcional}'


class PerfilAdminBiblioteca(models.Model):
    vinculo = models.OneToOneField('escolas.Vinculo', on_delete=models.CASCADE, related_name='perfil_biblioteca')
    registro_funcional = models.CharField(max_length=20)
    telefone = models.CharField(max_length=20, blank=True)
    cpf = models.CharField(max_length=14, blank=True)

    class Meta:
        unique_together = ['vinculo', 'registro_funcional']

    def __str__(self):
        return f'{self.vinculo.usuario.get_full_name()} - {self.registro_funcional}'
