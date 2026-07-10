from datetime import date

from django.conf import settings
from django.db import models


class Turma(models.Model):
    NIVEL_CHOICES = [
        ('fund1', 'Fundamental I'),
        ('fund2', 'Fundamental II'),
        ('medio', 'Ensino Médio'),
    ]
    TURNO_CHOICES = [
        ('manha', 'Manhã'),
        ('tarde', 'Tarde'),
        ('noite', 'Noite'),
        ('integral', 'Integral'),
    ]
    escola = models.ForeignKey('escolas.Escola', on_delete=models.CASCADE, related_name='turmas')
    codigo = models.CharField(max_length=10)
    ano_letivo = models.IntegerField()
    nivel = models.CharField(max_length=10, choices=NIVEL_CHOICES)
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['escola', 'codigo', 'ano_letivo']
        ordering = ['ano_letivo', 'codigo']

    def __str__(self):
        return f'{self.codigo} ({self.ano_letivo})'


class Autor(models.Model):
    escola = models.ForeignKey('escolas.Escola', on_delete=models.CASCADE, related_name='autores')
    nome = models.CharField(max_length=200)
    nacionalidade = models.CharField(max_length=100, blank=True)
    biografia = models.TextField(blank=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Genero(models.Model):
    escola = models.ForeignKey('escolas.Escola', on_delete=models.CASCADE, related_name='generos')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)

    class Meta:
        unique_together = ['escola', 'nome']
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Livro(models.Model):
    escola = models.ForeignKey('escolas.Escola', on_delete=models.CASCADE, related_name='livros')
    titulo = models.CharField(max_length=500)
    autores = models.ManyToManyField(Autor, related_name='livros', blank=True)
    editora = models.CharField(max_length=200, blank=True)
    isbn = models.CharField(max_length=20, null=True, blank=True)
    ano_publicacao = models.IntegerField(null=True, blank=True)
    generos = models.ManyToManyField(Genero, related_name='livros', blank=True)
    total_exemplares = models.IntegerField(default=1)
    exemplares_disponiveis = models.IntegerField(default=1)
    num_paginas = models.IntegerField(null=True, blank=True)
    capa = models.ImageField(upload_to='capas/', null=True, blank=True)
    sinopse = models.TextField(blank=True)
    localizacao_prateleira = models.CharField(max_length=50, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['escola', 'isbn']
        ordering = ['titulo']

    def __str__(self):
        return self.titulo

    @property
    def disponivel(self):
        return self.exemplares_disponiveis > 0


class Exemplar(models.Model):
    STATUS_CHOICES = [
        ('disponivel', 'Disponível'),
        ('emprestado', 'Emprestado'),
        ('reservado', 'Reservado'),
        ('danificado', 'Danificado'),
        ('perdido', 'Perdido'),
    ]
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='exemplares')
    codigo_tombamento = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disponivel')
    condicao = models.CharField(max_length=100, blank=True)
    adquirido_em = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.livro.titulo} - {self.codigo_tombamento}'


class Configuracao(models.Model):
    METODO_RECUPERACAO_ADMIN = 'admin'
    METODO_RECUPERACAO_EMAIL = 'email'
    METODO_RECUPERACAO_SMS = 'sms'
    METODO_RECUPERACAO_CHOICES = [
        (METODO_RECUPERACAO_ADMIN, 'Reset feito por um administrador'),
        (METODO_RECUPERACAO_EMAIL, 'E-mail (em breve)'),
        (METODO_RECUPERACAO_SMS, 'SMS (em breve)'),
    ]

    escola = models.OneToOneField('escolas.Escola', on_delete=models.CASCADE, related_name='configuracao')
    prazo_emprestimo_aluno = models.IntegerField(default=14)
    prazo_emprestimo_professor = models.IntegerField(default=30)
    prazo_emprestimo_turma = models.IntegerField(default=7)
    max_renovacoes = models.IntegerField(default=2)
    max_livros_aluno = models.IntegerField(default=3)
    max_livros_professor = models.IntegerField(default=10)
    dias_lembrete_vencimento = models.IntegerField(default=3)
    max_dias_notificacao_atraso = models.IntegerField(default=30)

    metodo_recuperacao_senha = models.CharField(
        max_length=10, choices=METODO_RECUPERACAO_CHOICES, default=METODO_RECUPERACAO_ADMIN
    )
    exigir_cpf_aluno = models.BooleanField(default=False)
    exigir_telefone_aluno = models.BooleanField(default=False)
    exigir_data_nascimento_aluno = models.BooleanField(default=False)
    exigir_responsavel_aluno = models.BooleanField(default=False)
    exigir_cpf_professor = models.BooleanField(default=False)
    exigir_telefone_professor = models.BooleanField(default=False)
    exigir_cpf_admin_biblioteca = models.BooleanField(default=False)
    exigir_telefone_admin_biblioteca = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'

    def __str__(self):
        return f'Configurações de {self.escola}'

    @classmethod
    def get_solo(cls, escola):
        obj, _ = cls.objects.get_or_create(escola=escola)
        return obj


class Emprestimo(models.Model):
    STATUS_ATIVO = 'ativo'
    STATUS_ATRASADO = 'atrasado'
    STATUS_DEVOLVIDO = 'devolvido'

    STATUS_CHOICES = [
        (STATUS_ATIVO, 'Ativo'),
        (STATUS_ATRASADO, 'Atrasado'),
        (STATUS_DEVOLVIDO, 'Devolvido'),
    ]
    escola = models.ForeignKey('escolas.Escola', on_delete=models.CASCADE, related_name='emprestimos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='emprestimos')
    livro = models.ForeignKey(Livro, on_delete=models.PROTECT, related_name='emprestimos')
    exemplar = models.ForeignKey(Exemplar, on_delete=models.PROTECT, null=True, related_name='emprestimos')
    data_saida = models.DateTimeField(auto_now_add=True)
    data_prevista_devolucao = models.DateField()
    data_real_devolucao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ATIVO)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='emprestimos_registrados'
    )
    renovacoes_realizadas = models.IntegerField(default=0)
    observacoes = models.TextField(blank=True)
    concluido = models.BooleanField(default=False)
    concluido_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.usuario} - {self.livro} ({self.get_status_display()})'

    @property
    def dias_atraso(self):
        if self.status != self.STATUS_DEVOLVIDO and date.today() > self.data_prevista_devolucao:
            return (date.today() - self.data_prevista_devolucao).days
        return 0

    @property
    def dias_restantes(self):
        if self.status == self.STATUS_DEVOLVIDO:
            return None
        return (self.data_prevista_devolucao - date.today()).days

    def pode_renovar(self):
        config = Configuracao.get_solo(self.escola)
        return (
            self.status != self.STATUS_DEVOLVIDO
            and self.dias_atraso == 0
            and self.renovacoes_realizadas < config.max_renovacoes
        )

    @property
    def severidade(self):
        if self.status == self.STATUS_DEVOLVIDO:
            return 'done'
        if self.dias_atraso > 0:
            return 'critical'
        if self.dias_restantes is not None and self.dias_restantes <= 3:
            return 'warning'
        return 'good'

    @property
    def progresso_pct(self):
        """Percentual decorrido do prazo do empréstimo, para uso em meters visuais."""
        total_dias = (self.data_prevista_devolucao - self.data_saida.date()).days
        if total_dias <= 0:
            return 100
        decorridos = total_dias - (self.dias_restantes or 0)
        return max(0, min(100, round(decorridos / total_dias * 100)))


class Renovacao(models.Model):
    emprestimo = models.ForeignKey(Emprestimo, on_delete=models.CASCADE, related_name='renovacoes')
    data_renovacao = models.DateTimeField(auto_now_add=True)
    nova_data_devolucao = models.DateField()
    renovado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'Renovação de {self.emprestimo} em {self.data_renovacao:%d/%m/%Y}'


class EmprestimoTurma(models.Model):
    escola = models.ForeignKey('escolas.Escola', on_delete=models.CASCADE, related_name='emprestimos_turma')
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, related_name='emprestimos_turma')
    professor_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='emprestimos_turma'
    )
    data_saida = models.DateTimeField(auto_now_add=True)
    data_prevista_devolucao = models.DateField()
    data_real_devolucao = models.DateField(null=True, blank=True)
    devolvido = models.BooleanField(default=False)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='emprestimos_turma_registrados'
    )
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'Empréstimo de turma {self.turma} - {self.data_saida:%d/%m/%Y}'

    @property
    def atrasado(self):
        return not self.devolvido and date.today() > self.data_prevista_devolucao


class ItemEmprestimoTurma(models.Model):
    emprestimo_turma = models.ForeignKey(EmprestimoTurma, on_delete=models.CASCADE, related_name='itens')
    livro = models.ForeignKey(Livro, on_delete=models.PROTECT)
    exemplar = models.ForeignKey(Exemplar, on_delete=models.PROTECT)
    devolvido = models.BooleanField(default=False)
    data_devolucao = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.livro} ({self.emprestimo_turma})'


class RegistroLeitura(models.Model):
    escola = models.ForeignKey('escolas.Escola', on_delete=models.CASCADE, related_name='registros_leitura')
    emprestimo = models.ForeignKey(Emprestimo, on_delete=models.CASCADE, related_name='registros_leitura')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='registros_leitura')
    pagina_atual = models.IntegerField()
    paginas_incrementadas = models.IntegerField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.usuario} - {self.emprestimo.livro} (pág. {self.pagina_atual})'


class Avaliacao(models.Model):
    escola = models.ForeignKey('escolas.Escola', on_delete=models.CASCADE, related_name='avaliacoes')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='avaliacoes')
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='avaliacoes')
    nota = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comentario = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['usuario', 'livro']
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.usuario} avaliou {self.livro} ({self.nota}★)'


class AuditLog(models.Model):
    escola = models.ForeignKey('escolas.Escola', on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    acao = models.CharField(max_length=200)
    modelo = models.CharField(max_length=100)
    objeto_id = models.IntegerField(null=True)
    detalhes = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.criado_em:%d/%m/%Y %H:%M} - {self.acao}'
