import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Usuario
from apps.biblioteca.models import Configuracao, Exemplar, Genero, Livro
from apps.escolas.models import Escola, Vinculo

try:
    import openpyxl
except ImportError:
    openpyxl = None


def _limpar(valor):
    if valor is None:
        return ''
    return re.sub(r'\s+', ' ', str(valor)).strip()


def _titulo_exibicao(titulo_upper):
    """CAIXA ALTA da planilha -> Título Exibição, preservando siglas curtas comuns."""
    palavras = titulo_upper.title().split(' ')
    minusculas = {'De', 'Da', 'Do', 'Das', 'Dos', 'E', 'A', 'O', 'Em', 'Para', 'Com'}
    resultado = [palavras[0]] + [p if p not in minusculas else p.lower() for p in palavras[1:]]
    return ' '.join(resultado)


class Command(BaseCommand):
    help = 'Importa uma escola e seu acervo a partir de uma planilha BIBLIOTECA.xlsx (uma aba por estante).'

    def add_arguments(self, parser):
        parser.add_argument('--arquivo', default='BIBLIOTECA.xlsx', help='Caminho da planilha .xlsx')
        parser.add_argument('--nome-escola', required=True)
        parser.add_argument('--sigla', required=True, help='Prefixo curto usado nos códigos de tombamento (ex: EEOEA)')
        parser.add_argument('--email-admin', required=True)
        parser.add_argument('--senha-admin', required=True)
        parser.add_argument('--dry-run', action='store_true', help='Só mostra o que seria importado, sem gravar nada.')

    def handle(self, *args, **options):
        if openpyxl is None:
            raise CommandError('openpyxl não instalado. Rode: pip install openpyxl')

        caminho = Path(options['arquivo'])
        if not caminho.is_absolute():
            caminho = Path(settings.BASE_DIR) / caminho
        if not caminho.exists():
            raise CommandError(f'Arquivo não encontrado: {caminho}')

        livros_agregados = self._ler_planilha(caminho)
        total_exemplares = sum(v['total_exemplares'] for v in livros_agregados.values())
        generos_distintos = {g for v in livros_agregados.values() for g in v['generos']}

        self.stdout.write(
            f'Planilha lida: {len(livros_agregados)} títulos distintos, '
            f'{total_exemplares} exemplares, {len(generos_distintos)} gêneros (TIPO).'
        )

        if options['dry_run']:
            for titulo, dado in list(livros_agregados.items())[:10]:
                self.stdout.write(f"  - {dado['titulo_exibicao']!r} | {dado['total_exemplares']}x | "
                                   f"{dado['prateleiras']} | gêneros: {sorted(dado['generos'])}")
            self.stdout.write(self.style.WARNING('Dry-run: nada foi gravado no banco.'))
            return

        with transaction.atomic():
            escola, escola_criada = Escola.objects.get_or_create(nome=options['nome_escola'])
            Configuracao.get_solo(escola)

            admin = self._criar_admin_geral(escola, options['email_admin'], options['senha_admin'])

            generos_cache = {
                nome: Genero.objects.get_or_create(escola=escola, nome=nome)[0] for nome in sorted(generos_distintos)
            }

            proximo_tombamento = Exemplar.objects.count() + 1
            livros_criados = 0
            exemplares_criados = 0

            for dado in livros_agregados.values():
                livro, criado = Livro.objects.get_or_create(
                    escola=escola,
                    titulo=dado['titulo_exibicao'],
                    defaults={
                        'total_exemplares': dado['total_exemplares'],
                        'exemplares_disponiveis': dado['total_exemplares'],
                        'localizacao_prateleira': ', '.join(sorted(dado['prateleiras'])),
                    },
                )
                if not criado:
                    continue
                livros_criados += 1
                livro.generos.add(*[generos_cache[g] for g in dado['generos']])

                novos_exemplares = []
                for _ in range(dado['total_exemplares']):
                    novos_exemplares.append(
                        Exemplar(livro=livro, codigo_tombamento=f"{options['sigla']}-{proximo_tombamento:06d}")
                    )
                    proximo_tombamento += 1
                Exemplar.objects.bulk_create(novos_exemplares)
                exemplares_criados += len(novos_exemplares)

        self.stdout.write(self.style.SUCCESS(
            f"\nEscola {'criada' if escola_criada else 'já existia'}: {escola.nome} (id={escola.id})\n"
            f"Admin geral: {admin.email} (senha padrão informada)\n"
            f'Livros criados: {livros_criados} | Exemplares criados: {exemplares_criados}\n'
            f'Gêneros: {len(generos_cache)}'
        ))

    def _criar_admin_geral(self, escola, email, senha):
        usuario = Usuario.objects.filter(email=email).first()
        if usuario is None:
            username = email.split('@')[0]
            usuario = Usuario.objects.create_user(
                username=username, email=email, password=senha, first_name='Admin', last_name='Geral',
            )
        Vinculo.objects.get_or_create(
            usuario=usuario, escola=escola, defaults={'tipo': Vinculo.TIPO_ADMIN_GERAL, 'ativo': True}
        )
        return usuario

    def _ler_planilha(self, caminho):
        wb = openpyxl.load_workbook(caminho, data_only=True)
        agregados = {}

        for nome_aba in wb.sheetnames:
            if nome_aba.strip().upper() == 'TOTAL':
                continue
            ws = wb[nome_aba]
            prateleira = _limpar(nome_aba).title()
            linhas = list(ws.iter_rows(values_only=True))

            header_idx = None
            for i, linha in enumerate(linhas):
                if linha and linha[0] and 'CATEGORIA' in str(linha[0]).upper():
                    header_idx = i
                    break
            if header_idx is None:
                continue

            for linha in linhas[header_idx + 1:]:
                titulo_bruto = _limpar(linha[1]) if len(linha) > 1 else ''
                if not titulo_bruto:
                    continue
                tipo = _limpar(linha[2]) if len(linha) > 2 else ''
                try:
                    qtd_exemplares = int(linha[4]) if len(linha) > 4 and linha[4] else 1
                except (TypeError, ValueError):
                    qtd_exemplares = 1
                qtd_exemplares = max(qtd_exemplares, 1)

                chave = titulo_bruto.upper()
                if chave not in agregados:
                    agregados[chave] = {
                        'titulo_exibicao': _titulo_exibicao(titulo_bruto),
                        'total_exemplares': 0,
                        'generos': set(),
                        'prateleiras': set(),
                    }
                agregados[chave]['total_exemplares'] += qtd_exemplares
                agregados[chave]['prateleiras'].add(prateleira)
                if tipo:
                    agregados[chave]['generos'].add(_titulo_exibicao(tipo))

        return agregados
