from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView, View

from apps.accounts.mixins import AdminBibliotecaRequiredMixin, AdminGeralRequiredMixin
from apps.accounts.models import Usuario
from apps.escolas.models import Vinculo

from . import gamificacao
from .forms import (
    AvaliacaoForm,
    ConfiguracaoForm,
    EmprestimoCreateForm,
    EmprestimoTurmaCreateForm,
    ExemplarQuantidadeForm,
    LivroForm,
    RegistroLeituraForm,
    TurmaForm,
)
from .gamificacao import GamificacaoError
from .models import (
    AuditLog,
    Autor,
    Avaliacao,
    Configuracao,
    Emprestimo,
    EmprestimoTurma,
    Exemplar,
    Genero,
    ItemEmprestimoTurma,
    Livro,
    Turma,
)
from .services import (
    EmprestimoError,
    atualizar_status_atrasados,
    devolver_item_emprestimo_turma,
    registrar_devolucao,
    registrar_emprestimo,
    registrar_emprestimo_turma,
)


class CatalogoListView(LoginRequiredMixin, ListView):
    model = Livro
    template_name = 'biblioteca/livro_list.html'
    context_object_name = 'livros'
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Livro.objects.filter(escola=self.request.escola, ativo=True)
            .prefetch_related('autores', 'generos')
            .annotate(nota_media=Avg('avaliacoes__nota'), qtd_avaliacoes=Count('avaliacoes'))
        )
        busca = self.request.GET.get('q')
        genero = self.request.GET.get('genero')
        disponivel = self.request.GET.get('disponivel')
        if busca:
            qs = qs.filter(
                Q(titulo__icontains=busca) | Q(autores__nome__icontains=busca) | Q(isbn__icontains=busca)
            ).distinct()
        if genero:
            qs = qs.filter(generos__id=genero)
        if disponivel == '1':
            qs = qs.filter(exemplares_disponiveis__gt=0)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['generos'] = Genero.objects.filter(escola=self.request.escola)
        return ctx


class LivroDetailView(LoginRequiredMixin, DetailView):
    model = Livro
    template_name = 'biblioteca/livro_detail.html'
    context_object_name = 'livro'

    def get_queryset(self):
        return Livro.objects.filter(escola=self.request.escola).annotate(
            nota_media=Avg('avaliacoes__nota'), qtd_avaliacoes=Count('avaliacoes')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        avaliacoes = self.object.avaliacoes.select_related('usuario').exclude(usuario=self.request.user)
        minha_avaliacao = self.object.avaliacoes.filter(usuario=self.request.user).first()
        ctx['avaliacoes'] = avaliacoes
        ctx['minha_avaliacao'] = minha_avaliacao
        ctx['avaliacao_form'] = AvaliacaoForm(instance=minha_avaliacao)
        ctx['ja_pegou_emprestado'] = Emprestimo.objects.filter(
            usuario=self.request.user, livro=self.object
        ).exists()
        return ctx


class AvaliacaoCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        livro = get_object_or_404(Livro, pk=pk, escola=request.escola)
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            try:
                gamificacao.criar_ou_atualizar_avaliacao(
                    usuario=request.user, livro=livro,
                    nota=form.cleaned_data['nota'], comentario=form.cleaned_data['comentario'],
                )
                messages.success(request, 'Avaliação registrada com sucesso.')
            except GamificacaoError as exc:
                messages.error(request, str(exc.message) if hasattr(exc, 'message') else str(exc))
        else:
            messages.error(request, 'Não foi possível salvar a avaliação — confira a nota informada.')
        return redirect('livro-detail', pk=pk)


class RegistrarProgressoView(LoginRequiredMixin, View):
    def post(self, request, emprestimo_id):
        emprestimo = get_object_or_404(Emprestimo, pk=emprestimo_id, escola=request.escola)
        form = RegistroLeituraForm(request.POST)
        if form.is_valid():
            try:
                gamificacao.registrar_progresso(
                    emprestimo=emprestimo, usuario_solicitante=request.user,
                    pagina_atual=form.cleaned_data['pagina_atual'],
                )
                messages.success(request, 'Progresso de leitura atualizado!')
            except GamificacaoError as exc:
                messages.error(request, str(exc.message) if hasattr(exc, 'message') else str(exc))
        else:
            messages.error(request, 'Informe uma página válida.')
        return redirect('dashboard')


class MarcarConcluidoView(LoginRequiredMixin, View):
    def post(self, request, emprestimo_id):
        emprestimo = get_object_or_404(Emprestimo, pk=emprestimo_id, escola=request.escola)
        try:
            gamificacao.marcar_livro_concluido(emprestimo=emprestimo, usuario_solicitante=request.user)
            messages.success(request, f'Parabéns por terminar "{emprestimo.livro.titulo}"!')
        except GamificacaoError as exc:
            messages.error(request, str(exc.message) if hasattr(exc, 'message') else str(exc))
        return redirect('dashboard')


class RankingView(LoginRequiredMixin, TemplateView):
    template_name = 'biblioteca/ranking.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tipo = self.request.GET.get('tipo', 'paginas')
        periodo = self.request.GET.get('periodo', 'total')
        if tipo == 'livros':
            ctx['ranking'] = gamificacao.ranking_livros(self.request.escola, periodo)
        else:
            tipo = 'paginas'
            ctx['ranking'] = gamificacao.ranking_paginas(self.request.escola, periodo)
        ctx['tipo'] = tipo
        ctx['periodo'] = periodo
        return ctx


class LivroCreateView(AdminBibliotecaRequiredMixin, CreateView):
    model = Livro
    form_class = LivroForm
    template_name = 'biblioteca/livro_form.html'
    success_url = reverse_lazy('livro-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['escola'] = self.request.escola
        return kwargs

    def form_valid(self, form):
        form.instance.escola = self.request.escola
        response = super().form_valid(form)
        qtd = int(self.request.POST.get('exemplares_iniciais') or 1)
        _criar_exemplares(self.object, qtd)
        AuditLog.objects.create(
            escola=self.request.escola,
            usuario=self.request.user,
            acao=f'Cadastrou livro "{self.object.titulo}"',
            modelo='Livro',
            objeto_id=self.object.id,
        )
        messages.success(self.request, 'Livro cadastrado com sucesso.')
        return response


class LivroUpdateView(AdminBibliotecaRequiredMixin, UpdateView):
    model = Livro
    form_class = LivroForm
    template_name = 'biblioteca/livro_form.html'
    success_url = reverse_lazy('livro-list')

    def get_queryset(self):
        return Livro.objects.filter(escola=self.request.escola)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['escola'] = self.request.escola
        return kwargs


def _criar_exemplares(livro, quantidade):
    ultimo = Exemplar.objects.count()
    for i in range(quantidade):
        ultimo += 1
        Exemplar.objects.create(livro=livro, codigo_tombamento=f'LIV-{ultimo:05d}')
    livro.total_exemplares = livro.exemplares.count()
    livro.exemplares_disponiveis = livro.exemplares.filter(status='disponivel').count()
    livro.save(update_fields=['total_exemplares', 'exemplares_disponiveis'])


class LivroAddExemplaresView(AdminBibliotecaRequiredMixin, View):
    def post(self, request, pk):
        livro = get_object_or_404(Livro, pk=pk, escola=request.escola)
        form = ExemplarQuantidadeForm(request.POST)
        if form.is_valid():
            _criar_exemplares(livro, form.cleaned_data['quantidade'])
            messages.success(request, 'Exemplares adicionados com sucesso.')
        return redirect('livro-detail', pk=pk)


class LivroToggleAtivoView(AdminBibliotecaRequiredMixin, View):
    def post(self, request, pk):
        livro = get_object_or_404(Livro, pk=pk, escola=request.escola)
        livro.ativo = not livro.ativo
        livro.save(update_fields=['ativo'])
        messages.success(request, 'Livro atualizado com sucesso.')
        return redirect('livro-list')


class AutorListView(AdminBibliotecaRequiredMixin, ListView):
    model = Autor
    template_name = 'biblioteca/autor_list.html'
    context_object_name = 'autores'

    def get_queryset(self):
        return Autor.objects.filter(escola=self.request.escola)


class GeneroListView(AdminBibliotecaRequiredMixin, ListView):
    model = Genero
    template_name = 'biblioteca/genero_list.html'
    context_object_name = 'generos'

    def get_queryset(self):
        return Genero.objects.filter(escola=self.request.escola)


class TurmaListView(AdminBibliotecaRequiredMixin, ListView):
    model = Turma
    template_name = 'biblioteca/turma_list.html'
    context_object_name = 'turmas'

    def get_queryset(self):
        return Turma.objects.filter(escola=self.request.escola).prefetch_related('alunos', 'professores')


class TurmaCreateView(AdminBibliotecaRequiredMixin, CreateView):
    model = Turma
    form_class = TurmaForm
    template_name = 'biblioteca/turma_form.html'
    success_url = reverse_lazy('turma-list')

    def form_valid(self, form):
        form.instance.escola = self.request.escola
        return super().form_valid(form)


class TurmaUpdateView(AdminBibliotecaRequiredMixin, UpdateView):
    model = Turma
    form_class = TurmaForm
    template_name = 'biblioteca/turma_form.html'
    success_url = reverse_lazy('turma-list')

    def get_queryset(self):
        return Turma.objects.filter(escola=self.request.escola)


class EmprestimoListView(AdminBibliotecaRequiredMixin, ListView):
    model = Emprestimo
    template_name = 'biblioteca/emprestimo_list.html'
    context_object_name = 'emprestimos'
    paginate_by = 25

    def get_queryset(self):
        atualizar_status_atrasados(self.request.escola)
        qs = Emprestimo.objects.filter(escola=self.request.escola).select_related('usuario', 'livro')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class EmprestimoCreateView(AdminBibliotecaRequiredMixin, View):
    template_name = 'biblioteca/emprestimo_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': EmprestimoCreateForm(escola=request.escola)})

    def post(self, request):
        form = EmprestimoCreateForm(request.POST, escola=request.escola)
        if form.is_valid():
            busca = form.cleaned_data['usuario_busca'].strip()
            livro = form.cleaned_data['livro']
            vinculo = (
                Vinculo.objects.filter(escola=request.escola, ativo=True)
                .filter(
                    Q(perfil_aluno__matricula__iexact=busca)
                    | Q(perfil_professor__matricula_funcional__iexact=busca)
                    | Q(usuario__email__iexact=busca)
                )
                .select_related('usuario')
                .first()
            )
            if not vinculo:
                messages.error(request, 'Usuário não encontrado (busque por matrícula ou e-mail).')
                return render(request, self.template_name, {'form': form})
            try:
                emprestimo = registrar_emprestimo(vinculo=vinculo, livro=livro, registrado_por=request.user)
                messages.success(
                    request,
                    f'Empréstimo registrado para {vinculo.usuario}. Devolução prevista: '
                    f'{emprestimo.data_prevista_devolucao:%d/%m/%Y}.',
                )
                return redirect('emprestimo-list')
            except EmprestimoError as exc:
                messages.error(request, str(exc.message) if hasattr(exc, 'message') else str(exc))
        return render(request, self.template_name, {'form': form})


class EmprestimoDevolverView(AdminBibliotecaRequiredMixin, View):
    def post(self, request, pk):
        emprestimo = get_object_or_404(Emprestimo, pk=pk, escola=request.escola)
        try:
            registrar_devolucao(emprestimo=emprestimo, registrado_por=request.user)
            messages.success(request, 'Devolução registrada com sucesso.')
        except EmprestimoError as exc:
            messages.error(request, str(exc.message) if hasattr(exc, 'message') else str(exc))
        return redirect('emprestimo-list')


class DashboardAdminBibliotecaView(AdminBibliotecaRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard_biblioteca.html'

    def get_context_data(self, **kwargs):
        import json

        from django.db.models import Prefetch

        escola = self.request.escola
        atualizar_status_atrasados(escola)
        ctx = super().get_context_data(**kwargs)
        ctx['total_titulos'] = Livro.objects.filter(escola=escola, ativo=True).count()
        ctx['total_exemplares'] = Exemplar.objects.filter(livro__escola=escola).count()
        ctx['emprestimos_ativos'] = Emprestimo.objects.filter(escola=escola, status__in=['ativo', 'atrasado']).count()
        ctx['emprestimos_atrasados'] = Emprestimo.objects.filter(escola=escola, status='atrasado').count()
        hoje = date.today()
        ctx['devolucoes_hoje'] = Emprestimo.objects.filter(escola=escola, data_real_devolucao=hoje).count()
        ctx['devolucoes_semana'] = Emprestimo.objects.filter(
            escola=escola, data_real_devolucao__gte=hoje - timedelta(days=7)
        ).count()

        emprestimos_qs = (
            Emprestimo.objects.filter(escola=escola)
            .select_related('usuario', 'livro')
            .prefetch_related(
                'livro__generos',
                Prefetch(
                    'usuario__vinculos',
                    queryset=Vinculo.objects.filter(escola=escola).select_related('perfil_aluno__turma'),
                ),
            )
            .annotate(paginas=Sum('registros_leitura__paginas_incrementadas'))
        )

        meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        eventos = []
        for emp in emprestimos_qs:
            vinculo = next(iter(emp.usuario.vinculos.all()), None)
            turma_codigo = None
            if vinculo is not None:
                perfil = getattr(vinculo, 'perfil_aluno', None)
                if perfil is not None and perfil.turma_id:
                    turma_codigo = perfil.turma.codigo
            dt = emp.data_saida
            base = {
                'mes': dt.strftime('%Y-%m'),
                'mes_label': f'{meses_pt[dt.month - 1]}/{dt.strftime("%y")}',
                'ano': dt.year,
                'turma': turma_codigo,
                'livro': emp.livro.titulo,
                'usuario': emp.usuario.get_full_name() or emp.usuario.email,
                'livros': 1,
                'paginas': emp.paginas or 0,
            }
            generos = list(emp.livro.generos.all())
            if generos:
                for genero in generos:
                    eventos.append({**base, 'genero': genero.nome})
            else:
                eventos.append({**base, 'genero': None})

        ctx['eventos_json'] = json.dumps(eventos)
        return ctx


class ConfiguracaoView(AdminBibliotecaRequiredMixin, View):
    template_name = 'biblioteca/configuracoes.html'

    def get(self, request):
        config = Configuracao.get_solo(request.escola)
        return render(request, self.template_name, {'form': ConfiguracaoForm(instance=config)})

    def post(self, request):
        config = Configuracao.get_solo(request.escola)
        form = ConfiguracaoForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações atualizadas com sucesso.')
            return redirect('configuracoes')
        return render(request, self.template_name, {'form': form})


class AuditLogListView(AdminGeralRequiredMixin, ListView):
    model = AuditLog
    template_name = 'biblioteca/auditlog_list.html'
    context_object_name = 'logs'
    paginate_by = 30

    def get_queryset(self):
        return AuditLog.objects.filter(escola=self.request.escola).select_related('usuario')


class EmprestimoTurmaCreateView(AdminBibliotecaRequiredMixin, View):
    template_name = 'biblioteca/emprestimo_turma_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': EmprestimoTurmaCreateForm(escola=request.escola)})

    def post(self, request):
        form = EmprestimoTurmaCreateForm(request.POST, escola=request.escola)
        if form.is_valid():
            try:
                emprestimo_turma = registrar_emprestimo_turma(
                    vinculo=form.cleaned_data['professor_responsavel'],
                    turma=form.cleaned_data['turma'],
                    itens=form.itens_selecionados(),
                    data_prevista_devolucao=form.cleaned_data['data_prevista_devolucao'],
                    registrado_por=request.user,
                )
                messages.success(request, 'Empréstimo de turma registrado com sucesso.')
                return redirect('emprestimo-turma-detail', pk=emprestimo_turma.pk)
            except EmprestimoError as exc:
                messages.error(request, str(exc.message) if hasattr(exc, 'message') else str(exc))
        else:
            messages.error(request, 'Confira os dados do formulário.')
        return render(request, self.template_name, {'form': form})


class EmprestimoTurmaDetailView(LoginRequiredMixin, DetailView):
    model = EmprestimoTurma
    template_name = 'biblioteca/emprestimo_turma_detail.html'
    context_object_name = 'emprestimo_turma'

    def get_queryset(self):
        return EmprestimoTurma.objects.filter(escola=self.request.escola).select_related('turma', 'professor_responsavel')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['itens'] = self.object.itens.select_related('livro', 'exemplar')
        return ctx


class ItemEmprestimoTurmaDevolverView(AdminBibliotecaRequiredMixin, View):
    def post(self, request, pk, item_id):
        item = get_object_or_404(
            ItemEmprestimoTurma, pk=item_id, emprestimo_turma_id=pk, emprestimo_turma__escola=request.escola
        )
        try:
            devolver_item_emprestimo_turma(item=item, registrado_por=request.user)
            messages.success(request, f'Devolução de "{item.livro.titulo}" registrada.')
        except EmprestimoError as exc:
            messages.error(request, str(exc.message) if hasattr(exc, 'message') else str(exc))
        return redirect('emprestimo-turma-detail', pk=pk)
