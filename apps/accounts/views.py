from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, View

from apps.biblioteca import gamificacao
from apps.biblioteca.models import AuditLog, Emprestimo, EmprestimoTurma
from apps.biblioteca.services import EmprestimoError, renovar_emprestimo
from apps.escolas.models import Vinculo

from .forms import AdminBibliotecaForm, AlunoForm, ProfessorForm
from .mixins import AdminBibliotecaRequiredMixin, AdminGeralRequiredMixin
from .models import PerfilAdminBiblioteca, PerfilAluno, PerfilProfessor, Usuario
from .utils import gerar_senha


class CustomLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class MinhaSenhaChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('password-change-done')


class MinhaSenhaChangeDoneView(LoginRequiredMixin, auth_views.PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'


@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_super_admin:
        return redirect('escola-list')

    if request.vinculo is None:
        vinculos = list(Vinculo.objects.filter(usuario=user, ativo=True, escola__ativa=True))
        if not vinculos:
            messages.error(request, 'Você não possui vínculo ativo com nenhuma escola.')
            logout(request)
            return redirect('login')
        if len(vinculos) == 1:
            request.session['vinculo_id'] = vinculos[0].id
            return redirect('dashboard')
        return redirect('escola-selecao')

    destino = {
        Vinculo.TIPO_ADMIN_GERAL: 'dashboard-admin-geral',
        Vinculo.TIPO_ADMIN_BIBLIOTECA: 'dashboard-admin-biblioteca',
        Vinculo.TIPO_PROFESSOR: 'dashboard-professor',
        Vinculo.TIPO_ALUNO: 'dashboard-aluno',
    }.get(request.vinculo.tipo, 'login')
    return redirect(destino)


class DashboardAdminGeralView(AdminGeralRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard_admin.html'

    def get_context_data(self, **kwargs):
        import json

        from apps.biblioteca.models import Turma

        escola = self.request.escola
        ctx = super().get_context_data(**kwargs)
        ctx['total_alunos'] = PerfilAluno.objects.filter(vinculo__escola=escola, vinculo__ativo=True).count()
        ctx['total_professores'] = PerfilProfessor.objects.filter(vinculo__escola=escola, vinculo__ativo=True).count()
        ctx['total_admins_biblioteca'] = PerfilAdminBiblioteca.objects.filter(
            vinculo__escola=escola, vinculo__ativo=True
        ).count()
        ctx['logs_recentes'] = AuditLog.objects.filter(escola=escola).select_related('usuario')[:10]

        turmas = (
            Turma.objects.filter(escola=escola, ativa=True)
            .annotate(qtd_alunos=Count('alunos', filter=Q(alunos__vinculo__ativo=True)))
            .order_by('codigo')
        )
        ctx['turmas'] = turmas
        ctx['chart_turmas_labels'] = json.dumps([t.codigo for t in turmas])
        ctx['chart_turmas_valores'] = json.dumps([t.qtd_alunos for t in turmas])
        return ctx


class ListaAlunosView(AdminBibliotecaRequiredMixin, ListView):
    model = PerfilAluno
    template_name = 'accounts/aluno_list.html'
    context_object_name = 'alunos'
    paginate_by = 20

    def get_queryset(self):
        return (
            PerfilAluno.objects.filter(vinculo__escola=self.request.escola)
            .select_related('vinculo__usuario', 'turma')
            .order_by('vinculo__usuario__first_name')
        )


class AlunoCreateView(AdminGeralRequiredMixin, CreateView):
    form_class = AlunoForm
    template_name = 'accounts/aluno_form.html'
    success_url = reverse_lazy('aluno-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['escola'] = self.request.escola
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.objects.create(
            escola=self.request.escola,
            usuario=self.request.user,
            acao=f'Cadastrou aluno {self.object}',
            modelo='Usuario',
            objeto_id=self.object.id,
        )
        messages.success(self.request, 'Aluno cadastrado com sucesso.')
        return response


class AlunoUpdateView(AdminGeralRequiredMixin, UpdateView):
    model = Usuario
    form_class = AlunoForm
    template_name = 'accounts/aluno_form.html'
    success_url = reverse_lazy('aluno-list')

    def get_queryset(self):
        return Usuario.objects.filter(
            vinculos__tipo=Vinculo.TIPO_ALUNO, vinculos__escola=self.request.escola
        ).distinct()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['escola'] = self.request.escola
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Aluno atualizado com sucesso.')
        return response


class AlunoExcluirView(AdminGeralRequiredMixin, View):
    def post(self, request, pk):
        vinculo = get_object_or_404(
            Vinculo, usuario_id=pk, tipo=Vinculo.TIPO_ALUNO, escola=request.escola
        )
        if Emprestimo.objects.filter(
            usuario=vinculo.usuario, escola=request.escola, status__in=[Emprestimo.STATUS_ATIVO, Emprestimo.STATUS_ATRASADO]
        ).exists():
            messages.error(
                request,
                'Não é possível remover: há empréstimos ativos ou atrasados. '
                'Registre a devolução ou apenas desative o cadastro.',
            )
            return redirect('aluno-list')
        nome = str(vinculo.usuario)
        AuditLog.objects.create(
            escola=request.escola,
            usuario=request.user,
            acao=f'Removeu aluno {nome}',
            modelo='Usuario',
            objeto_id=vinculo.usuario_id,
        )
        vinculo.delete()
        messages.success(request, f'Aluno {nome} removido com sucesso.')
        return redirect('aluno-list')


class AlunoToggleAtivoView(AdminGeralRequiredMixin, View):
    def post(self, request, pk):
        vinculo = get_object_or_404(
            Vinculo, usuario_id=pk, tipo=Vinculo.TIPO_ALUNO, escola=request.escola
        )
        vinculo.ativo = not vinculo.ativo
        vinculo.save(update_fields=['ativo'])
        AuditLog.objects.create(
            escola=request.escola,
            usuario=request.user,
            acao=f'{"Ativou" if vinculo.ativo else "Desativou"} aluno {vinculo.usuario}',
            modelo='Usuario',
            objeto_id=vinculo.usuario_id,
        )
        messages.success(request, f'Aluno {"ativado" if vinculo.ativo else "desativado"} com sucesso.')
        return redirect('aluno-list')


class AlunoResetarSenhaView(AdminBibliotecaRequiredMixin, View):
    def post(self, request, pk):
        vinculo = get_object_or_404(Vinculo, usuario_id=pk, tipo=Vinculo.TIPO_ALUNO, escola=request.escola)
        senha = gerar_senha()
        vinculo.usuario.set_password(senha)
        vinculo.usuario.save(update_fields=['password'])
        AuditLog.objects.create(
            escola=request.escola,
            usuario=request.user,
            acao=f'Resetou senha de {vinculo.usuario}',
            modelo='Usuario',
            objeto_id=vinculo.usuario_id,
        )
        messages.success(request, f'Nova senha para {vinculo.usuario.get_full_name()}: {senha}')
        return redirect('aluno-list')


class ListaProfessoresView(AdminBibliotecaRequiredMixin, ListView):
    model = PerfilProfessor
    template_name = 'accounts/professor_list.html'
    context_object_name = 'professores'
    paginate_by = 20

    def get_queryset(self):
        return (
            PerfilProfessor.objects.filter(vinculo__escola=self.request.escola)
            .select_related('vinculo__usuario')
            .prefetch_related('turmas')
            .order_by('vinculo__usuario__first_name')
        )


class ProfessorCreateView(AdminGeralRequiredMixin, CreateView):
    form_class = ProfessorForm
    template_name = 'accounts/professor_form.html'
    success_url = reverse_lazy('professor-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['escola'] = self.request.escola
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.objects.create(
            escola=self.request.escola,
            usuario=self.request.user,
            acao=f'Cadastrou professor {self.object}',
            modelo='Usuario',
            objeto_id=self.object.id,
        )
        messages.success(self.request, 'Professor cadastrado com sucesso.')
        return response


class ProfessorUpdateView(AdminGeralRequiredMixin, UpdateView):
    model = Usuario
    form_class = ProfessorForm
    template_name = 'accounts/professor_form.html'
    success_url = reverse_lazy('professor-list')

    def get_queryset(self):
        return Usuario.objects.filter(
            vinculos__tipo=Vinculo.TIPO_PROFESSOR, vinculos__escola=self.request.escola
        ).distinct()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['escola'] = self.request.escola
        return kwargs


class ProfessorExcluirView(AdminGeralRequiredMixin, View):
    def post(self, request, pk):
        vinculo = get_object_or_404(
            Vinculo, usuario_id=pk, tipo=Vinculo.TIPO_PROFESSOR, escola=request.escola
        )
        if Emprestimo.objects.filter(
            usuario=vinculo.usuario, escola=request.escola, status__in=[Emprestimo.STATUS_ATIVO, Emprestimo.STATUS_ATRASADO]
        ).exists():
            messages.error(
                request,
                'Não é possível remover: há empréstimos ativos ou atrasados. '
                'Registre a devolução ou apenas desative o cadastro.',
            )
            return redirect('professor-list')
        nome = str(vinculo.usuario)
        AuditLog.objects.create(
            escola=request.escola,
            usuario=request.user,
            acao=f'Removeu professor {nome}',
            modelo='Usuario',
            objeto_id=vinculo.usuario_id,
        )
        vinculo.delete()
        messages.success(request, f'Professor {nome} removido com sucesso.')
        return redirect('professor-list')


class ProfessorToggleAtivoView(AdminGeralRequiredMixin, View):
    def post(self, request, pk):
        vinculo = get_object_or_404(
            Vinculo, usuario_id=pk, tipo=Vinculo.TIPO_PROFESSOR, escola=request.escola
        )
        vinculo.ativo = not vinculo.ativo
        vinculo.save(update_fields=['ativo'])
        AuditLog.objects.create(
            escola=request.escola,
            usuario=request.user,
            acao=f'{"Ativou" if vinculo.ativo else "Desativou"} professor {vinculo.usuario}',
            modelo='Usuario',
            objeto_id=vinculo.usuario_id,
        )
        messages.success(request, f'Professor {"ativado" if vinculo.ativo else "desativado"} com sucesso.')
        return redirect('professor-list')


class ProfessorResetarSenhaView(AdminBibliotecaRequiredMixin, View):
    def post(self, request, pk):
        vinculo = get_object_or_404(Vinculo, usuario_id=pk, tipo=Vinculo.TIPO_PROFESSOR, escola=request.escola)
        senha = gerar_senha()
        vinculo.usuario.set_password(senha)
        vinculo.usuario.save(update_fields=['password'])
        AuditLog.objects.create(
            escola=request.escola,
            usuario=request.user,
            acao=f'Resetou senha de {vinculo.usuario}',
            modelo='Usuario',
            objeto_id=vinculo.usuario_id,
        )
        messages.success(request, f'Nova senha para {vinculo.usuario.get_full_name()}: {senha}')
        return redirect('professor-list')


class ListaAdminsBibliotecaView(AdminGeralRequiredMixin, ListView):
    model = PerfilAdminBiblioteca
    template_name = 'accounts/admin_biblioteca_list.html'
    context_object_name = 'admins_biblioteca'

    def get_queryset(self):
        return PerfilAdminBiblioteca.objects.filter(vinculo__escola=self.request.escola).select_related(
            'vinculo__usuario'
        )


class AdminBibliotecaCreateView(AdminGeralRequiredMixin, CreateView):
    form_class = AdminBibliotecaForm
    template_name = 'accounts/admin_biblioteca_form.html'
    success_url = reverse_lazy('admin-biblioteca-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['escola'] = self.request.escola
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.objects.create(
            escola=self.request.escola,
            usuario=self.request.user,
            acao=f'Cadastrou responsável de biblioteca {self.object}',
            modelo='Usuario',
            objeto_id=self.object.id,
        )
        messages.success(self.request, 'Responsável pela biblioteca cadastrado com sucesso.')
        return response


class AdminBibliotecaUpdateView(AdminGeralRequiredMixin, UpdateView):
    model = Usuario
    form_class = AdminBibliotecaForm
    template_name = 'accounts/admin_biblioteca_form.html'
    success_url = reverse_lazy('admin-biblioteca-list')

    def get_queryset(self):
        return Usuario.objects.filter(
            vinculos__tipo=Vinculo.TIPO_ADMIN_BIBLIOTECA, vinculos__escola=self.request.escola
        ).distinct()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['escola'] = self.request.escola
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Responsável pela biblioteca atualizado com sucesso.')
        return response


class AdminBibliotecaExcluirView(AdminGeralRequiredMixin, View):
    def post(self, request, pk):
        vinculo = get_object_or_404(
            Vinculo, usuario_id=pk, tipo=Vinculo.TIPO_ADMIN_BIBLIOTECA, escola=request.escola
        )
        nome = str(vinculo.usuario)
        AuditLog.objects.create(
            escola=request.escola,
            usuario=request.user,
            acao=f'Removeu responsável de biblioteca {nome}',
            modelo='Usuario',
            objeto_id=vinculo.usuario_id,
        )
        vinculo.delete()
        messages.success(request, f'Responsável pela biblioteca {nome} removido com sucesso.')
        return redirect('admin-biblioteca-list')


class AdminBibliotecaToggleAtivoView(AdminGeralRequiredMixin, View):
    def post(self, request, pk):
        vinculo = get_object_or_404(
            Vinculo, usuario_id=pk, tipo=Vinculo.TIPO_ADMIN_BIBLIOTECA, escola=request.escola
        )
        vinculo.ativo = not vinculo.ativo
        vinculo.save(update_fields=['ativo'])
        AuditLog.objects.create(
            escola=request.escola,
            usuario=request.user,
            acao=f'{"Ativou" if vinculo.ativo else "Desativou"} responsável biblioteca {vinculo.usuario}',
            modelo='Usuario',
            objeto_id=vinculo.usuario_id,
        )
        messages.success(request, 'Status atualizado com sucesso.')
        return redirect('admin-biblioteca-list')


class AdminBibliotecaResetarSenhaView(AdminGeralRequiredMixin, View):
    def post(self, request, pk):
        vinculo = get_object_or_404(Vinculo, usuario_id=pk, tipo=Vinculo.TIPO_ADMIN_BIBLIOTECA, escola=request.escola)
        senha = gerar_senha()
        vinculo.usuario.set_password(senha)
        vinculo.usuario.save(update_fields=['password'])
        AuditLog.objects.create(
            escola=request.escola,
            usuario=request.user,
            acao=f'Resetou senha de {vinculo.usuario}',
            modelo='Usuario',
            objeto_id=vinculo.usuario_id,
        )
        messages.success(request, f'Nova senha para {vinculo.usuario.get_full_name()}: {senha}')
        return redirect('admin-biblioteca-list')


class DashboardProfessorView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard_professor.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (
            request.vinculo is None or request.vinculo.tipo != Vinculo.TIPO_PROFESSOR
        ):
            messages.error(request, 'Acesso restrito a professores.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        emprestimos = list(
            Emprestimo.objects.filter(usuario=self.request.user, escola=self.request.escola)
            .select_related('livro')
            .prefetch_related('registros_leitura')
        )
        for e in emprestimos:
            ultimo = max(e.registros_leitura.all(), key=lambda r: r.pagina_atual, default=None)
            e.pagina_atual_lida = ultimo.pagina_atual if ultimo else 0
        ctx['emprestimos'] = emprestimos
        total_paginas = gamificacao.total_paginas_lidas(self.request.escola, self.request.user)
        ctx['nivel'] = gamificacao.calcular_nivel(total_paginas)
        ctx['total_paginas_lidas'] = total_paginas

        perfil = getattr(self.request.vinculo, 'perfil_professor', None)
        turmas = list(perfil.turmas.all()) if perfil else []

        emprestimos_ativos_por_usuario = {
            e.usuario_id: e
            for e in Emprestimo.objects.filter(
                escola=self.request.escola, status__in=['ativo', 'atrasado']
            ).select_related('livro')
        }
        for turma in turmas:
            alunos = list(
                PerfilAluno.objects.filter(turma=turma, vinculo__escola=self.request.escola)
                .select_related('vinculo__usuario')
            )
            for aluno in alunos:
                aluno.emprestimo_atual = emprestimos_ativos_por_usuario.get(aluno.vinculo.usuario_id)
            turma.alunos_com_status = alunos
            turma.historico_emprestimos_turma = list(
                EmprestimoTurma.objects.filter(turma=turma, escola=self.request.escola)
                .select_related('professor_responsavel')
                .prefetch_related('itens__livro')[:10]
            )

        ctx['turmas'] = turmas
        return ctx


class DashboardAlunoView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard_aluno.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (
            request.vinculo is None or request.vinculo.tipo != Vinculo.TIPO_ALUNO
        ):
            messages.error(request, 'Acesso restrito a alunos.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        emprestimos = list(
            Emprestimo.objects.filter(usuario=self.request.user, escola=self.request.escola)
            .select_related('livro')
            .prefetch_related('registros_leitura')
        )
        for e in emprestimos:
            ultimo = max(e.registros_leitura.all(), key=lambda r: r.pagina_atual, default=None)
            e.pagina_atual_lida = ultimo.pagina_atual if ultimo else 0
        ctx['emprestimos'] = emprestimos
        total_paginas = gamificacao.total_paginas_lidas(self.request.escola, self.request.user)
        ctx['nivel'] = gamificacao.calcular_nivel(total_paginas)
        ctx['total_paginas_lidas'] = total_paginas
        return ctx


class RenovarEmprestimoView(LoginRequiredMixin, View):
    def post(self, request, pk):
        emprestimo = get_object_or_404(Emprestimo, pk=pk, escola=request.escola)
        try:
            renovar_emprestimo(emprestimo=emprestimo, usuario_solicitante=request.user)
            messages.success(request, f'Empréstimo renovado até {emprestimo.data_prevista_devolucao:%d/%m/%Y}.')
        except EmprestimoError as exc:
            messages.error(request, str(exc.message) if hasattr(exc, 'message') else str(exc))
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect('dashboard')
