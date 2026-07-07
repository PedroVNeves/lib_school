from datetime import date

from django.core.exceptions import ValidationError
from django.db.models import Count, Sum
from django.utils import timezone

from .models import Avaliacao, Emprestimo, RegistroLeitura

NIVEIS = [
    (0, 'Leitor Iniciante', '🌱'),
    (100, 'Leitor Aprendiz', '📖'),
    (300, 'Leitor Dedicado', '📚'),
    (600, 'Leitor Voraz', '🔥'),
    (1000, 'Leitor Experiente', '⭐'),
    (2000, 'Leitor Mestre', '🏆'),
    (4000, 'Leitor Lendário', '👑'),
    (8000, 'Leitor Imortal', '💎'),
]


class GamificacaoError(ValidationError):
    pass


def registrar_progresso(*, emprestimo, usuario_solicitante, pagina_atual):
    if emprestimo.usuario_id != usuario_solicitante.id:
        raise GamificacaoError('Você só pode registrar progresso nos seus próprios empréstimos.')
    if emprestimo.status not in (Emprestimo.STATUS_ATIVO, Emprestimo.STATUS_ATRASADO):
        raise GamificacaoError('Só é possível registrar progresso em livros emprestados no momento.')

    ultimo = emprestimo.registros_leitura.order_by('-pagina_atual').first()
    pagina_anterior = ultimo.pagina_atual if ultimo else 0

    if pagina_atual <= pagina_anterior:
        raise GamificacaoError(f'Informe uma página maior que a última registrada ({pagina_anterior}).')

    num_paginas = emprestimo.livro.num_paginas
    if num_paginas and pagina_atual > num_paginas:
        raise GamificacaoError(f'O livro tem {num_paginas} páginas — não é possível ultrapassar esse total.')

    registro = RegistroLeitura.objects.create(
        escola=emprestimo.escola,
        emprestimo=emprestimo,
        usuario=usuario_solicitante,
        pagina_atual=pagina_atual,
        paginas_incrementadas=pagina_atual - pagina_anterior,
    )
    return registro


def marcar_livro_concluido(*, emprestimo, usuario_solicitante):
    if emprestimo.usuario_id != usuario_solicitante.id:
        raise GamificacaoError('Você só pode concluir os seus próprios empréstimos.')
    if emprestimo.concluido:
        raise GamificacaoError('Este livro já está marcado como concluído.')

    num_paginas = emprestimo.livro.num_paginas
    if num_paginas:
        ultimo = emprestimo.registros_leitura.order_by('-pagina_atual').first()
        pagina_anterior = ultimo.pagina_atual if ultimo else 0
        if num_paginas > pagina_anterior:
            RegistroLeitura.objects.create(
                escola=emprestimo.escola,
                emprestimo=emprestimo,
                usuario=usuario_solicitante,
                pagina_atual=num_paginas,
                paginas_incrementadas=num_paginas - pagina_anterior,
            )

    emprestimo.concluido = True
    emprestimo.concluido_em = timezone.now()
    emprestimo.save(update_fields=['concluido', 'concluido_em'])
    return emprestimo


def criar_ou_atualizar_avaliacao(*, usuario, livro, nota, comentario):
    ja_pegou_emprestado = Emprestimo.objects.filter(usuario=usuario, livro=livro).exists()
    if not ja_pegou_emprestado:
        raise GamificacaoError('Você só pode avaliar livros que já pegou emprestado.')

    avaliacao, _ = Avaliacao.objects.update_or_create(
        usuario=usuario, livro=livro,
        defaults={'escola': livro.escola, 'nota': nota, 'comentario': comentario},
    )
    return avaliacao


def calcular_nivel(total_paginas):
    atual = NIVEIS[0]
    proximo = None
    for i, limiar in enumerate(NIVEIS):
        if total_paginas >= limiar[0]:
            atual = limiar
            proximo = NIVEIS[i + 1] if i + 1 < len(NIVEIS) else None
        else:
            break

    numero = NIVEIS.index(atual) + 1
    if proximo:
        faixa = proximo[0] - atual[0]
        progresso_pct = max(0, min(100, round((total_paginas - atual[0]) / faixa * 100)))
        paginas_faltantes = proximo[0] - total_paginas
    else:
        progresso_pct = 100
        paginas_faltantes = 0

    return {
        'numero': numero,
        'nome': atual[1],
        'emoji': atual[2],
        'proximo_nome': proximo[1] if proximo else None,
        'paginas_faltantes': paginas_faltantes,
        'progresso_pct': progresso_pct,
    }


def total_paginas_lidas(escola, usuario):
    total = RegistroLeitura.objects.filter(escola=escola, usuario=usuario).aggregate(total=Sum('paginas_incrementadas'))
    return total['total'] or 0


def ranking_paginas(escola, periodo='total'):
    qs = RegistroLeitura.objects.filter(escola=escola)
    if periodo == 'mensal':
        hoje = date.today()
        qs = qs.filter(criado_em__year=hoje.year, criado_em__month=hoje.month)
    return (
        qs.values('usuario_id', 'usuario__first_name', 'usuario__last_name')
        .annotate(total=Sum('paginas_incrementadas'))
        .filter(total__gt=0)
        .order_by('-total')[:20]
    )


def ranking_livros(escola, periodo='total'):
    qs = Emprestimo.objects.filter(escola=escola, concluido=True)
    if periodo == 'mensal':
        hoje = date.today()
        qs = qs.filter(concluido_em__year=hoje.year, concluido_em__month=hoje.month)
    return (
        qs.values('usuario_id', 'usuario__first_name', 'usuario__last_name')
        .annotate(total=Count('id'))
        .order_by('-total')[:20]
    )
