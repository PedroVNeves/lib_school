from datetime import date, timedelta

from django.core.exceptions import PermissionDenied, ValidationError

from apps.escolas.models import Vinculo

from .models import AuditLog, Configuracao, Emprestimo, Exemplar, Renovacao


class EmprestimoError(ValidationError):
    pass


def _prazo_para_usuario(vinculo, config):
    if vinculo.tipo == Vinculo.TIPO_PROFESSOR:
        return config.prazo_emprestimo_professor
    return config.prazo_emprestimo_aluno


def _limite_para_usuario(vinculo, config):
    if vinculo.tipo == Vinculo.TIPO_PROFESSOR:
        return config.max_livros_professor
    return config.max_livros_aluno


def registrar_emprestimo(*, vinculo, livro, registrado_por, exemplar=None):
    if vinculo.escola_id != livro.escola_id:
        raise EmprestimoError('Usuário e livro pertencem a escolas diferentes.')

    config = Configuracao.get_solo(vinculo.escola)
    usuario = vinculo.usuario

    if not vinculo.ativo:
        raise EmprestimoError('Usuário está desativado e não pode pegar livros emprestados.')

    em_atraso = Emprestimo.objects.filter(
        usuario=usuario, escola=vinculo.escola, status=Emprestimo.STATUS_ATRASADO
    ).exists()
    if em_atraso:
        raise EmprestimoError('Usuário possui empréstimos em atraso. Regularize antes de um novo empréstimo.')

    ativos = Emprestimo.objects.filter(
        usuario=usuario, escola=vinculo.escola, status__in=[Emprestimo.STATUS_ATIVO, Emprestimo.STATUS_ATRASADO]
    ).count()
    limite = _limite_para_usuario(vinculo, config)
    if ativos >= limite:
        raise EmprestimoError(f'Usuário atingiu o limite de {limite} livros simultâneos.')

    if not livro.disponivel:
        raise EmprestimoError('Não há exemplares disponíveis deste livro.')

    if exemplar is None:
        exemplar = livro.exemplares.filter(status='disponivel').first()
    if exemplar is None:
        raise EmprestimoError('Não há exemplar disponível para empréstimo.')

    prazo = _prazo_para_usuario(vinculo, config)
    data_prevista = date.today() + timedelta(days=prazo)

    emprestimo = Emprestimo.objects.create(
        escola=vinculo.escola,
        usuario=usuario,
        livro=livro,
        exemplar=exemplar,
        data_prevista_devolucao=data_prevista,
        registrado_por=registrado_por,
    )

    exemplar.status = 'emprestado'
    exemplar.save(update_fields=['status'])
    livro.exemplares_disponiveis = livro.exemplares.filter(status='disponivel').count()
    livro.save(update_fields=['exemplares_disponiveis'])

    AuditLog.objects.create(
        escola=vinculo.escola,
        usuario=registrado_por,
        acao=f'Registrou empréstimo #{emprestimo.id} para {usuario}',
        modelo='Emprestimo',
        objeto_id=emprestimo.id,
    )
    return emprestimo


def registrar_devolucao(*, emprestimo, registrado_por):
    if emprestimo.status == Emprestimo.STATUS_DEVOLVIDO:
        raise EmprestimoError('Este empréstimo já foi devolvido.')

    emprestimo.data_real_devolucao = date.today()
    emprestimo.status = Emprestimo.STATUS_DEVOLVIDO
    emprestimo.save(update_fields=['data_real_devolucao', 'status', 'atualizado_em'])

    exemplar = emprestimo.exemplar
    if exemplar:
        exemplar.status = 'disponivel'
        exemplar.save(update_fields=['status'])

    livro = emprestimo.livro
    livro.exemplares_disponiveis = livro.exemplares.filter(status='disponivel').count()
    livro.save(update_fields=['exemplares_disponiveis'])

    AuditLog.objects.create(
        escola=emprestimo.escola,
        usuario=registrado_por,
        acao=f'Registrou devolução do empréstimo #{emprestimo.id}',
        modelo='Emprestimo',
        objeto_id=emprestimo.id,
    )
    return emprestimo


def renovar_emprestimo(*, emprestimo, usuario_solicitante):
    if emprestimo.usuario_id != usuario_solicitante.id and not usuario_solicitante.is_staff:
        raise PermissionDenied('Você só pode renovar seus próprios empréstimos.')

    if not emprestimo.pode_renovar():
        raise EmprestimoError('Este empréstimo não é elegível para renovação.')

    vinculo = Vinculo.objects.filter(usuario=emprestimo.usuario, escola=emprestimo.escola).first()
    if vinculo is None:
        raise EmprestimoError('Usuário não possui vínculo ativo com a escola deste empréstimo.')

    config = Configuracao.get_solo(emprestimo.escola)
    prazo = _prazo_para_usuario(vinculo, config)
    nova_data = date.today() + timedelta(days=prazo)

    Renovacao.objects.create(
        emprestimo=emprestimo,
        nova_data_devolucao=nova_data,
        renovado_por=usuario_solicitante,
    )
    emprestimo.data_prevista_devolucao = nova_data
    emprestimo.renovacoes_realizadas += 1
    if emprestimo.status == Emprestimo.STATUS_ATRASADO:
        emprestimo.status = Emprestimo.STATUS_ATIVO
    emprestimo.save(update_fields=['data_prevista_devolucao', 'renovacoes_realizadas', 'status', 'atualizado_em'])
    return emprestimo


def atualizar_status_atrasados(escola=None):
    hoje = date.today()
    qs = Emprestimo.objects.filter(status=Emprestimo.STATUS_ATIVO, data_prevista_devolucao__lt=hoje)
    if escola is not None:
        qs = qs.filter(escola=escola)
    return qs.update(status=Emprestimo.STATUS_ATRASADO)
