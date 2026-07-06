from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.accounts.mixins import SuperAdminRequiredMixin

from .forms import EscolaForm
from .models import Escola, Vinculo


class EscolaSelecaoView(LoginRequiredMixin, View):
    template_name = 'escolas/escola_selecao.html'

    def get(self, request):
        vinculos = Vinculo.objects.filter(
            usuario=request.user, ativo=True, escola__ativa=True
        ).select_related('escola')
        if not vinculos:
            messages.error(request, 'Você não possui vínculo ativo com nenhuma escola.')
            return redirect('login')
        if vinculos.count() == 1:
            request.session['vinculo_id'] = vinculos.first().id
            return redirect('dashboard')
        return render(request, self.template_name, {'vinculos': vinculos})

    def post(self, request):
        vinculo = get_object_or_404(
            Vinculo, pk=request.POST.get('vinculo_id'), usuario=request.user, ativo=True, escola__ativa=True
        )
        request.session['vinculo_id'] = vinculo.id
        return redirect('dashboard')


class TrocarEscolaView(LoginRequiredMixin, View):
    def post(self, request):
        request.session.pop('vinculo_id', None)
        return redirect('escola-selecao')


class EscolaListView(SuperAdminRequiredMixin, ListView):
    model = Escola
    template_name = 'escolas/escola_list.html'
    context_object_name = 'escolas'

    def get_queryset(self):
        return Escola.objects.annotate(
            qtd_alunos=Count(
                'vinculos', filter=Q(vinculos__tipo=Vinculo.TIPO_ALUNO, vinculos__ativo=True), distinct=True
            ),
            qtd_professores=Count(
                'vinculos', filter=Q(vinculos__tipo=Vinculo.TIPO_PROFESSOR, vinculos__ativo=True), distinct=True
            ),
            qtd_livros=Count('livros', distinct=True),
        )


class EscolaCreateView(SuperAdminRequiredMixin, CreateView):
    model = Escola
    form_class = EscolaForm
    template_name = 'escolas/escola_form.html'
    success_url = reverse_lazy('escola-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        from apps.biblioteca.models import Configuracao

        Configuracao.objects.get_or_create(escola=self.object)
        messages.success(self.request, 'Escola cadastrada com sucesso.')
        return response


class EscolaUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Escola
    form_class = EscolaForm
    template_name = 'escolas/escola_form.html'
    success_url = reverse_lazy('escola-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Escola atualizada com sucesso.')
        return response


class EscolaToggleAtivaView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        escola = get_object_or_404(Escola, pk=pk)
        escola.ativa = not escola.ativa
        escola.save(update_fields=['ativa'])
        messages.success(request, f'Escola {"ativada" if escola.ativa else "desativada"} com sucesso.')
        return redirect('escola-list')
