import random
import secrets
import string
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import PerfilAdminBiblioteca, PerfilAluno, PerfilProfessor, Usuario
from apps.biblioteca.models import (
    Autor,
    Configuracao,
    Emprestimo,
    Exemplar,
    Genero,
    Livro,
    Turma,
)
from apps.escolas.models import Escola, Vinculo

try:
    from faker import Faker
except ImportError:
    Faker = None


ALFABETO_SEM_AMBIGUOS = (
    string.ascii_letters.replace('l', '').replace('I', '').replace('O', '')
    + string.digits.replace('0', '').replace('1', '')
)


def gerar_senha(tamanho=12):
    """Gera senha aleatória segura (letras, dígitos e símbolo), sem caracteres ambíguos."""
    simbolos = '!@#$%&*'
    base = [secrets.choice(ALFABETO_SEM_AMBIGUOS) for _ in range(tamanho - 1)]
    base.append(secrets.choice(simbolos))
    secrets.SystemRandom().shuffle(base)
    return ''.join(base)


ESCOLAS_SEED = [
    'Escola Municipal Monteiro Lobato',
    'Colégio Everest',
]

GENEROS = ['Ficção Científica', 'Fantasia', 'Romance', 'Aventura', 'Didático', 'Não-Ficção', 'Poesia', 'Terror']

LIVROS_SEED = [
    ('Dom Casmurro', 'Machado de Assis', 'Brasileira', 1899, ['Romance']),
    ('O Cortiço', 'Aluísio Azevedo', 'Brasileira', 1890, ['Não-Ficção', 'Romance']),
    ('Memórias Póstumas de Brás Cubas', 'Machado de Assis', 'Brasileira', 1881, ['Romance']),
    ('Quincas Borba', 'Machado de Assis', 'Brasileira', 1891, ['Romance']),
    ('Capitães da Areia', 'Jorge Amado', 'Brasileira', 1937, ['Aventura']),
    ('Gabriela, Cravo e Canela', 'Jorge Amado', 'Brasileira', 1958, ['Romance']),
    ('Grande Sertão: Veredas', 'Guimarães Rosa', 'Brasileira', 1956, ['Aventura', 'Romance']),
    ('1984', 'George Orwell', 'Britânica', 1949, ['Ficção Científica']),
    ('Admirável Mundo Novo', 'Aldous Huxley', 'Britânica', 1932, ['Ficção Científica']),
    ('O Hobbit', 'J.R.R. Tolkien', 'Britânica', 1937, ['Fantasia', 'Aventura']),
    ('O Senhor dos Anéis: A Sociedade do Anel', 'J.R.R. Tolkien', 'Britânica', 1954, ['Fantasia', 'Aventura']),
    ('Harry Potter e a Pedra Filosofal', 'J.K. Rowling', 'Britânica', 1997, ['Fantasia']),
    ('Harry Potter e a Câmara Secreta', 'J.K. Rowling', 'Britânica', 1998, ['Fantasia']),
    ('Duna', 'Frank Herbert', 'Americana', 1965, ['Ficção Científica']),
    ('O Pequeno Príncipe', 'Antoine de Saint-Exupéry', 'Francesa', 1943, ['Poesia', 'Aventura']),
    ('A Revolução dos Bichos', 'George Orwell', 'Britânica', 1945, ['Não-Ficção']),
    ('O Alquimista', 'Paulo Coelho', 'Brasileira', 1988, ['Aventura']),
    ('Iracema', 'José de Alencar', 'Brasileira', 1865, ['Romance']),
    ('Vidas Secas', 'Graciliano Ramos', 'Brasileira', 1938, ['Não-Ficção']),
    ('It: A Coisa', 'Stephen King', 'Americana', 1986, ['Terror']),
    ('O Iluminado', 'Stephen King', 'Americana', 1977, ['Terror']),
    ('Frankenstein', 'Mary Shelley', 'Britânica', 1818, ['Terror', 'Ficção Científica']),
    ('Drácula', 'Bram Stoker', 'Irlandesa', 1897, ['Terror']),
    ('Fundação', 'Isaac Asimov', 'Americana', 1951, ['Ficção Científica']),
    ('Eu, Robô', 'Isaac Asimov', 'Americana', 1950, ['Ficção Científica']),
    ('As Crônicas de Nárnia: O Leão, a Feiticeira e o Guarda-Roupa', 'C.S. Lewis', 'Britânica', 1950, ['Fantasia']),
    ('Percy Jackson e o Ladrão de Raios', 'Rick Riordan', 'Americana', 2005, ['Fantasia', 'Aventura']),
    ('O Diário de Anne Frank', 'Anne Frank', 'Holandesa', 1947, ['Não-Ficção']),
    ('Sapiens: Uma Breve História da Humanidade', 'Yuval Noah Harari', 'Israelense', 2011, ['Não-Ficção', 'Didático']),
    ('Cosmos', 'Carl Sagan', 'Americana', 1980, ['Didático', 'Não-Ficção']),
    ('A Metamorfose', 'Franz Kafka', 'Tcheca', 1915, ['Não-Ficção']),
    ('Orgulho e Preconceito', 'Jane Austen', 'Britânica', 1813, ['Romance']),
    ('O Morro dos Ventos Uivantes', 'Emily Brontë', 'Britânica', 1847, ['Romance', 'Terror']),
    ('A Culpa é das Estrelas', 'John Green', 'Americana', 2012, ['Romance']),
    ('Jogos Vorazes', 'Suzanne Collins', 'Americana', 2008, ['Aventura', 'Ficção Científica']),
    ('Divergente', 'Veronica Roth', 'Americana', 2011, ['Aventura', 'Ficção Científica']),
]

TURMAS_SEED = [
    ('5A', 'fund1', 'manha'),
    ('6A', 'fund2', 'manha'),
    ('6B', 'fund2', 'tarde'),
    ('7A', 'fund2', 'manha'),
    ('7B', 'fund2', 'tarde'),
    ('8A', 'fund2', 'tarde'),
    ('9A', 'fund2', 'manha'),
    ('9B', 'fund2', 'tarde'),
    ('1M', 'medio', 'manha'),
    ('2M', 'medio', 'noite'),
]

TITULO_SUBSTANTIVOS = [
    'Rio', 'Ilha', 'Floresta', 'Cidade', 'Estrela', 'Jardim', 'Vento', 'Mar', 'Sonho', 'Templo',
    'Reino', 'Deserto', 'Vale', 'Montanha', 'Castelo', 'Segredo', 'Viagem', 'Memória', 'Lua', 'Sombra',
    'Farol', 'Labirinto', 'Horizonte', 'Bosque', 'Travessia', 'Chama', 'Ponte', 'Enigma', 'Caminho', 'Nevoeiro',
]
TITULO_ADJETIVOS = [
    'Perdida', 'Esquecido', 'Silencioso', 'Distante', 'Eterno', 'Secreto', 'Dourado', 'Sombrio',
    'Infinito', 'Encantada', 'Selvagem', 'Oculto', 'Invisível', 'Antigo', 'Derradeiro', 'Inesperado',
]
TITULO_TEMPLATES = [
    '{art1_maiusc} {sub1} {adj1}',
    '{sub1} de {sub2}',
    '{art1_maiusc} {sub1} d{artigo2} {sub2}',
    'O Mistério d{artigo2} {sub2}',
    'Crônicas d{artigo1} {sub1}',
    '{art1_maiusc} {ultimo1} {sub1}',
    '{sub1}: Uma História {adj_fem}',
    'Entre {sub1} e {sub2}',
]

FEMININOS = {'Ilha', 'Floresta', 'Cidade', 'Estrela', 'Viagem', 'Memória', 'Lua', 'Sombra', 'Montanha', 'Travessia', 'Chama', 'Ponte', 'Nevoeiro'}


def _gerar_titulo_aleatorio(rng):
    sub1, sub2 = rng.sample(TITULO_SUBSTANTIVOS, 2)
    adj_base = rng.choice(TITULO_ADJETIVOS)
    fem1 = sub1 in FEMININOS

    def _concordar(adjetivo, feminino):
        if feminino and adjetivo.endswith('o'):
            return adjetivo[:-1] + 'a'
        if not feminino and adjetivo.endswith('a') and adjetivo not in ('Selvagem',):
            return adjetivo[:-1] + 'o'
        return adjetivo

    template = rng.choice(TITULO_TEMPLATES)
    return template.format(
        sub1=sub1,
        sub2=sub2,
        adj1=_concordar(adj_base, fem1),
        adj_fem=_concordar(adj_base, True),
        art1_maiusc='A' if fem1 else 'O',
        ultimo1='Última' if fem1 else 'Último',
        artigo1='a' if fem1 else 'o',
        artigo2='a' if sub2 in FEMININOS else 'o',
    )


PROFESSORES_SEED = [
    ('Carlos', 'Pereira', 'Português, Literatura'),
    ('Fernanda', 'Souza', 'Matemática'),
    ('Ricardo', 'Lima', 'História'),
    ('Juliana', 'Alves', 'Ciências'),
    ('Marcos', 'Ferreira', 'Geografia'),
    ('Patrícia', 'Gomes', 'Inglês'),
    ('André', 'Martins', 'Artes'),
    ('Camila', 'Rocha', 'Educação Física'),
]


class Command(BaseCommand):
    help = 'Popula o banco com dados de teste (escolas, livros, turmas, usuários e empréstimos) e gera credenciais de acesso.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Apaga dados existentes antes de popular.')
        parser.add_argument('--alunos', type=int, default=100, help='Quantidade de alunos a criar POR escola.')

    def handle(self, *args, **options):
        self.fake = Faker('pt_BR') if Faker else None
        rng = random.Random()

        if options['reset']:
            self.stdout.write('Removendo dados existentes...')
            from apps.biblioteca.models import AuditLog
            AuditLog.objects.all().delete()
            Emprestimo.objects.all().delete()
            Exemplar.objects.all().delete()
            Livro.objects.all().delete()
            Autor.objects.all().delete()
            Genero.objects.all().delete()
            Turma.objects.all().delete()
            Usuario.objects.all().delete()
            Escola.objects.all().delete()

        credenciais = []

        with transaction.atomic():
            self._criar_super_admin(credenciais)

            escolas = []
            turmas_por_escola = {}

            for idx, nome_escola in enumerate(ESCOLAS_SEED, start=1):
                escola, _ = Escola.objects.get_or_create(
                    nome=nome_escola, defaults={'email_contato': f'contato{idx}@escola.com.br'}
                )
                config = Configuracao.get_solo(escola)

                generos = {nome: Genero.objects.get_or_create(escola=escola, nome=nome)[0] for nome in GENEROS}
                livros = self._criar_livros(escola, generos, rng)
                self._criar_exemplares(livros, rng)
                turmas = self._criar_turmas(escola)
                turmas_por_escola[escola.id] = turmas

                self._criar_admin_geral(escola, idx, credenciais)
                responsavel = self._criar_admin_biblioteca(escola, idx, credenciais)
                professores = self._criar_professores(escola, idx, turmas, credenciais, rng)
                alunos = self._criar_alunos(escola, idx, turmas, options['alunos'], credenciais, rng)

                self._criar_emprestimos_aleatorios(escola, alunos, professores, livros, responsavel, config, rng)
                escolas.append(escola)

            self._criar_professor_itinerante(escolas, turmas_por_escola, credenciais)

        self.stdout.write(self.style.SUCCESS('\nDados de teste criados com sucesso!\n'))
        for escola in Escola.objects.all():
            self.stdout.write(
                f'{escola.nome}: Livros: {Livro.objects.filter(escola=escola).count()} | '
                f'Turmas: {Turma.objects.filter(escola=escola).count()} | '
                f'Empréstimos: {Emprestimo.objects.filter(escola=escola).count()}'
            )
        self._imprimir_credenciais(credenciais)

    # ------------------------------------------------------------------
    # Acervo
    # ------------------------------------------------------------------

    def _criar_livros(self, escola, generos, rng):
        livros = []
        for titulo, autor_nome, nacionalidade, ano, gens in LIVROS_SEED:
            autor, _ = Autor.objects.get_or_create(
                escola=escola, nome=autor_nome, defaults={'nacionalidade': nacionalidade}
            )
            livro, created = Livro.objects.get_or_create(
                escola=escola,
                titulo=titulo,
                defaults={'editora': 'Editora Nacional', 'ano_publicacao': ano, 'num_paginas': rng.randint(120, 480)},
            )
            if created:
                livro.autores.add(autor)
                livro.generos.add(*[generos[g] for g in gens])
            livros.append(livro)

        # Livros extras gerados aleatoriamente para diversificar o acervo/visualizações.
        if self.fake:
            for _ in range(20):
                titulo = _gerar_titulo_aleatorio(rng)
                if Livro.objects.filter(escola=escola, titulo=titulo).exists():
                    continue
                autor_nome = self.fake.name()
                autor, _ = Autor.objects.get_or_create(escola=escola, nome=autor_nome, defaults={'nacionalidade': 'Brasileira'})
                livro = Livro.objects.create(
                    escola=escola,
                    titulo=titulo,
                    editora=self.fake.company(),
                    ano_publicacao=rng.randint(1960, 2024),
                    num_paginas=rng.randint(80, 520),
                )
                livro.autores.add(autor)
                qtd_generos = rng.randint(1, 2)
                livro.generos.add(*rng.sample(list(generos.values()), qtd_generos))
                livros.append(livro)
        return livros

    def _criar_exemplares(self, livros, rng):
        exemplar_seq = Exemplar.objects.count()
        for livro in livros:
            if livro.exemplares.exists():
                continue
            qtd = rng.choice([2, 3, 3, 4, 5])
            for _ in range(qtd):
                exemplar_seq += 1
                Exemplar.objects.create(livro=livro, codigo_tombamento=f'LIV-{exemplar_seq:05d}')
            livro.total_exemplares = qtd
            livro.exemplares_disponiveis = qtd
            livro.save(update_fields=['total_exemplares', 'exemplares_disponiveis'])

    def _criar_turmas(self, escola):
        turmas = []
        for codigo, nivel, turno in TURMAS_SEED:
            turma, _ = Turma.objects.get_or_create(
                escola=escola, codigo=codigo, ano_letivo=2026, defaults={'nivel': nivel, 'turno': turno}
            )
            turmas.append(turma)
        return turmas

    # ------------------------------------------------------------------
    # Usuários
    # ------------------------------------------------------------------

    def _criar_super_admin(self, credenciais):
        email = 'super@saas.com.br'
        usuario = Usuario.objects.filter(email=email).first()
        if usuario:
            return usuario
        senha = gerar_senha()
        usuario = Usuario.objects.create_superuser(
            username='super.admin', email=email, password=senha, first_name='Super', last_name='Admin',
        )
        usuario.is_super_admin = True
        usuario.save(update_fields=['is_super_admin'])
        credenciais.append(('Super Admin', '(todas as escolas)', usuario.email, senha))
        return usuario

    def _criar_admin_geral(self, escola, idx, credenciais):
        email = f'admin{idx}@escola.com.br'
        usuario = Usuario.objects.filter(email=email).first()
        is_new = usuario is None
        if is_new:
            senha = gerar_senha()
            usuario = Usuario.objects.create_user(
                username=f'admin.geral{idx}', email=email, password=senha,
                first_name='Admin', last_name=f'Geral',
            )
        Vinculo.objects.get_or_create(
            usuario=usuario, escola=escola, defaults={'tipo': Vinculo.TIPO_ADMIN_GERAL, 'ativo': True}
        )
        if is_new:
            credenciais.append(('Admin Geral', escola.nome, usuario.email, senha))
        return usuario

    def _criar_admin_biblioteca(self, escola, idx, credenciais):
        email = f'biblioteca{idx}@escola.com.br'
        usuario = Usuario.objects.filter(email=email).first()
        is_new = usuario is None
        if is_new:
            senha = gerar_senha()
            usuario = Usuario.objects.create_user(
                username=f'ana.biblioteca{idx}', email=email, password=senha,
                first_name='Ana', last_name='Bibliotecária',
            )
        vinculo, _ = Vinculo.objects.get_or_create(
            usuario=usuario, escola=escola, defaults={'tipo': Vinculo.TIPO_ADMIN_BIBLIOTECA, 'ativo': True}
        )
        PerfilAdminBiblioteca.objects.get_or_create(vinculo=vinculo, defaults={'registro_funcional': f'BIB-{idx:03d}'})
        if is_new:
            credenciais.append(('Admin Biblioteca', escola.nome, usuario.email, senha))
        return usuario

    def _criar_professores(self, escola, idx, turmas, credenciais, rng):
        professores = []
        for i, (first, last, disciplinas) in enumerate(PROFESSORES_SEED):
            user = f'{first.lower()}.{last.lower()}{idx}'
            email = f'{user}@escola.com.br'
            usuario = Usuario.objects.filter(email=email).first()
            is_new = usuario is None
            if is_new:
                senha = gerar_senha()
                usuario = Usuario.objects.create_user(
                    username=user, email=email, password=senha, first_name=first, last_name=last,
                )
            vinculo, vinculo_criado = Vinculo.objects.get_or_create(
                usuario=usuario, escola=escola, defaults={'tipo': Vinculo.TIPO_PROFESSOR, 'ativo': True}
            )
            perfil, _ = PerfilProfessor.objects.get_or_create(
                vinculo=vinculo, defaults={'matricula_funcional': f'PROF-{idx}-{i + 1:03d}', 'disciplinas': disciplinas}
            )
            if vinculo_criado:
                qtd_turmas = random.randint(1, 3)
                perfil.turmas.add(*random.sample(turmas, min(qtd_turmas, len(turmas))))
            professores.append(usuario)
            if is_new and i < 3:
                credenciais.append(('Professor', escola.nome, usuario.email, senha))
        return professores

    def _criar_alunos(self, escola, idx, turmas, quantidade, credenciais, rng):
        alunos = []
        usados = set()
        pesos_turma = [rng.randint(6, 16) for _ in turmas]
        i = 0
        while len(alunos) < quantidade:
            i += 1
            first = self.fake.first_name() if self.fake else f'Aluno{i}'
            last = self.fake.last_name() if self.fake else 'Silva'
            base_user = f'{first}.{last}{idx}'.lower().replace(' ', '')
            user = base_user
            suffix = 1
            while user in usados:
                suffix += 1
                user = f'{base_user}{suffix}'
            usados.add(user)
            email = f'{user}@escola.com.br'
            usuario = Usuario.objects.filter(email=email).first()
            is_new = usuario is None
            if is_new:
                senha = gerar_senha()
                usuario = Usuario.objects.create_user(
                    username=user, email=email, password=senha, first_name=first, last_name=last,
                )
            vinculo, vinculo_criado = Vinculo.objects.get_or_create(
                usuario=usuario, escola=escola, defaults={'tipo': Vinculo.TIPO_ALUNO, 'ativo': True}
            )
            if vinculo_criado:
                PerfilAluno.objects.create(
                    vinculo=vinculo,
                    matricula=f'{2026}{idx}{len(alunos) + 1:04d}',
                    turma=rng.choices(turmas, weights=pesos_turma)[0],
                    data_nascimento=date(2011, 1, 1) + timedelta(days=len(alunos) * 25),
                    responsavel_nome=self.fake.name() if self.fake else 'Responsável',
                    responsavel_contato='(11) 90000-0000',
                )
            alunos.append(usuario)
            if is_new and len(alunos) <= 4:
                credenciais.append(('Aluno', escola.nome, usuario.email, senha))
        return alunos

    def _criar_professor_itinerante(self, escolas, turmas_por_escola, credenciais):
        """Professor com vínculo ativo em mais de uma escola, para demonstrar a seleção de escola no login."""
        if len(escolas) < 2:
            return
        email = 'itinerante@escola.com.br'
        usuario = Usuario.objects.filter(email=email).first()
        is_new = usuario is None
        if is_new:
            senha = gerar_senha()
            usuario = Usuario.objects.create_user(
                username='professor.itinerante', email=email, password=senha,
                first_name='Roberto', last_name='Itinerante',
            )
        for idx, escola in enumerate(escolas, start=1):
            vinculo, vinculo_criado = Vinculo.objects.get_or_create(
                usuario=usuario, escola=escola, defaults={'tipo': Vinculo.TIPO_PROFESSOR, 'ativo': True}
            )
            perfil, _ = PerfilProfessor.objects.get_or_create(
                vinculo=vinculo, defaults={'matricula_funcional': f'PROF-ITIN-{idx:03d}', 'disciplinas': 'Educação Física'}
            )
            turmas = turmas_por_escola.get(escola.id) or []
            if vinculo_criado and turmas:
                perfil.turmas.add(*random.sample(turmas, min(2, len(turmas))))
        if is_new:
            credenciais.append(
                ('Professor (múltiplas escolas)', ' + '.join(e.nome for e in escolas), usuario.email, senha)
            )
        return usuario

    # ------------------------------------------------------------------
    # Empréstimos aleatórios e diversificados
    # ------------------------------------------------------------------

    def _criar_emprestimo_historico(self, escola, usuario, livro, exemplar, registrado_por, dias_saida_atras, prazo_dias, cenario, rng):
        data_saida_dt = timezone.now() - timedelta(days=dias_saida_atras)
        data_prevista = data_saida_dt.date() + timedelta(days=prazo_dias)

        status = 'devolvido' if cenario == 'devolvido' else ('atrasado' if cenario == 'atrasado' else 'ativo')
        emprestimo = Emprestimo.objects.create(
            escola=escola, usuario=usuario, livro=livro, exemplar=exemplar,
            data_prevista_devolucao=data_prevista, status=status,
            registrado_por=registrado_por,
        )
        Emprestimo.objects.filter(pk=emprestimo.pk).update(
            data_saida=data_saida_dt, criado_em=data_saida_dt, atualizado_em=data_saida_dt
        )

        if cenario == 'devolvido':
            desvio = rng.randint(-5, 10)
            data_real = min(date.today(), data_prevista + timedelta(days=desvio))
            data_real = max(data_real, data_saida_dt.date())
            Emprestimo.objects.filter(pk=emprestimo.pk).update(data_real_devolucao=data_real)
            exemplar.status = 'disponivel'
        else:
            exemplar.status = 'emprestado'
        exemplar.save(update_fields=['status'])
        return emprestimo

    def _criar_emprestimos_aleatorios(self, escola, alunos, professores, livros, responsavel, config, rng):
        # Controla quantos exemplares de cada livro já estão "emprestados" (ativo/atrasado)
        # simultaneamente, para não estourar a disponibilidade.
        exemplares_por_livro = {l.id: list(l.exemplares.all()) for l in livros}
        emprestados_agora = {l.id: set() for l in livros}

        def escolher_exemplar_livre(livro):
            disponiveis = [
                e for e in exemplares_por_livro[livro.id] if e.id not in emprestados_agora[livro.id]
            ]
            if not disponiveis:
                return None
            return rng.choice(disponiveis)

        def gerar_para_usuario(usuario, eh_professor):
            max_concorrentes = config.max_livros_professor if eh_professor else config.max_livros_aluno
            prazo = config.prazo_emprestimo_professor if eh_professor else config.prazo_emprestimo_aluno
            total_emprestimos = rng.randint(1, min(5, max_concorrentes + 2)) if eh_professor else rng.randint(0, 4)
            if total_emprestimos == 0:
                return
            livros_amostra = rng.sample(livros, min(total_emprestimos, len(livros)))

            concorrentes_criados = 0
            for livro in livros_amostra:
                cenario = rng.choices(
                    ['devolvido', 'ativo', 'atrasado'], weights=[78, 15, 7], k=1
                )[0]

                if cenario != 'devolvido':
                    if concorrentes_criados >= max_concorrentes:
                        cenario = 'devolvido'
                    else:
                        exemplar = escolher_exemplar_livre(livro)
                        if exemplar is None:
                            cenario = 'devolvido'

                if cenario == 'devolvido':
                    exemplar = rng.choice(exemplares_por_livro[livro.id])
                    dias_saida_atras = rng.randint(15, 360)
                    self._criar_emprestimo_historico(
                        escola, usuario, livro, exemplar, responsavel, dias_saida_atras, prazo, 'devolvido', rng
                    )
                elif cenario == 'ativo':
                    dias_saida_atras = rng.randint(0, max(1, prazo - 2))
                    self._criar_emprestimo_historico(
                        escola, usuario, livro, exemplar, responsavel, dias_saida_atras, prazo, 'ativo', rng
                    )
                    emprestados_agora[livro.id].add(exemplar.id)
                    concorrentes_criados += 1
                else:  # atrasado
                    dias_saida_atras = prazo + rng.randint(1, 20)
                    self._criar_emprestimo_historico(
                        escola, usuario, livro, exemplar, responsavel, dias_saida_atras, prazo, 'atrasado', rng
                    )
                    emprestados_agora[livro.id].add(exemplar.id)
                    concorrentes_criados += 1

        for professor in professores:
            gerar_para_usuario(professor, eh_professor=True)
        for aluno in alunos:
            gerar_para_usuario(aluno, eh_professor=False)

        # Sincroniza contadores de disponibilidade do acervo.
        for livro in livros:
            livro.exemplares_disponiveis = livro.exemplares.filter(status='disponivel').count()
            livro.save(update_fields=['exemplares_disponiveis'])

    # ------------------------------------------------------------------
    # Saída
    # ------------------------------------------------------------------

    def _imprimir_credenciais(self, credenciais):
        linhas = ['CREDENCIAIS DE TESTE — Biblioteca Escolar (multi-escola)', '=' * 100]
        for papel, escola_nome, email, senha in credenciais:
            linhas.append(f'{papel:<28} | {escola_nome:<32} | {email:<32} | {senha}')
        linhas.append('=' * 100)
        linhas.append('Guarde este arquivo em local seguro e não o commite no git.')
        texto = '\n'.join(linhas)
        self.stdout.write(texto)

        from pathlib import Path
        destino = Path(__file__).resolve().parents[4] / 'CREDENCIAIS_TESTE.txt'
        destino.write_text(texto, encoding='utf-8')
        self.stdout.write(self.style.WARNING(f'\nCredenciais também salvas em: {destino}'))
