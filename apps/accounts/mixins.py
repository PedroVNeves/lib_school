from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class TipoRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    tipos_permitidos = ()

    def test_func(self):
        vinculo = getattr(self.request, 'vinculo', None)
        return self.request.user.is_authenticated and vinculo is not None and vinculo.tipo in self.tipos_permitidos

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(self.request, 'Você não tem permissão para acessar esta área.')
        return redirect('dashboard')


class AdminGeralRequiredMixin(TipoRequiredMixin):
    tipos_permitidos = ('admin_geral',)


class AdminBibliotecaRequiredMixin(TipoRequiredMixin):
    tipos_permitidos = ('admin_geral', 'admin_biblioteca')


class SuperAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_super_admin

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(self.request, 'Você não tem permissão para acessar esta área.')
        return redirect('dashboard')
