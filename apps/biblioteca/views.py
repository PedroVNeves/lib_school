from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView, View

from apps.accounts.mixins import AdminBibliotecaRequiredMixin, AdminGeralRequiredMixin
from apps.accounts.models import Usuario
from apps.escolas.models import Vinculo

from .forms import ConfiguracaoForm, EmprestimoCreateForm, ExemplarQuantidadeForm, LivroForm, TurmaForm
from .models import AuditLog, Autor, Configuracao, Emprestimo, EmprestimoTurma, Exemplar, Genero, Livro, Turma
from .services import EmprestimoError, atualizar_status_atrasados, registrar_devolucao, registrar_emprestimo


class CatalogoListView(LoginRequiredMixin, ListView):
    model = Livro
    template_name = 'biblioteca/livro_list.html'
    context_object_name = 'livros'
    paginate_by = 12

    def get_queryset(self):
        qs = Livro.objects.filter(escola=self.request.escola, ativo=True).prefetch_related('autores', 'generos')
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
        return Livro.objects.filter(escola=self.request.escola)


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

        from django.db.models.functions import TruncMonth

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

        ctx['top_livros'] = (
            Livro.objects.filter(escola=escola)
            .annotate(qtd=Count('emprestimos'))
            .filter(qtd__gt=0)
            .order_by('-qtd')[:10]
        )
        ctx['top_generos'] = (
            Genero.objects.filter(escola=escola)
            .annotate(qtd=Count('livros__emprestimos'))
            .filter(qtd__gt=0)
            .order_by('-qtd')[:5]
        )
        ctx['top_turmas'] = (
            Turma.objects.filter(escola=escola)
            .annotate(qtd=Count('alunos__vinculo__usuario__emprestimos'))
            .filter(qtd__gt=0)
            .order_by('-qtd')[:5]
        )
        ctx['top_usuarios'] = (
            Usuario.objects.filter(
                vinculos__escola=escola, vinculos__tipo__in=[Vinculo.TIPO_ALUNO, Vinculo.TIPO_PROFESSOR]
            )
            .annotate(qtd=Count('emprestimos', filter=Q(emprestimos__escola=escola)))
            .filter(qtd__gt=0)
            .order_by('-qtd')[:8]
        )

        inicio = (hoje.replace(day=1) - timedelta(days=335)).replace(day=1)
        por_mes = (
            Emprestimo.objects.filter(escola=escola, data_saida__date__gte=inicio)
            .annotate(mes=TruncMonth('data_saida'))
            .values('mes')
            .annotate(qtd=Count('id'))
            .order_by('mes')
        )
        contagem_por_mes = {item['mes'].strftime('%Y-%m'): item['qtd'] for item in por_mes}
        labels_meses, valores_meses = [], []
        cursor = inicio
        for _ in range(12):
            chave = cursor.strftime('%Y-%m')
            labels_meses.append(cursor.strftime('%b/%y'))
            valores_meses.append(contagem_por_mes.get(chave, 0))
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

        ctx['chart_meses'] = json.dumps(labels_meses)
        ctx['chart_meses_valores'] = json.dumps(valores_meses)
        ctx['chart_livros_labels'] = json.dumps([l.titulo for l in ctx['top_livros']])
        ctx['chart_livros_valores'] = json.dumps([l.qtd for l in ctx['top_livros']])
        ctx['chart_generos_labels'] = json.dumps([g.nome for g in ctx['top_generos']])
        ctx['chart_generos_valores'] = json.dumps([g.qtd for g in ctx['top_generos']])
        ctx['chart_turmas_labels'] = json.dumps([t.codigo for t in ctx['top_turmas']])
        ctx['chart_turmas_valores'] = json.dumps([t.qtd for t in ctx['top_turmas']])
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
