from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_redirect, name='dashboard'),

    path('minha-senha/', views.MinhaSenhaChangeView.as_view(), name='password-change'),
    path('minha-senha/sucesso/', views.MinhaSenhaChangeDoneView.as_view(), name='password-change-done'),
    path('dashboard/admin-geral/', views.DashboardAdminGeralView.as_view(), name='dashboard-admin-geral'),
    path('dashboard/professor/', views.DashboardProfessorView.as_view(), name='dashboard-professor'),
    path('dashboard/aluno/', views.DashboardAlunoView.as_view(), name='dashboard-aluno'),

    path('emprestimos/<int:pk>/renovar/', views.RenovarEmprestimoView.as_view(), name='emprestimo-renovar-self'),

    path('admin-geral/alunos/', views.ListaAlunosView.as_view(), name='aluno-list'),
    path('admin-geral/alunos/novo/', views.AlunoCreateView.as_view(), name='aluno-create'),
    path('admin-geral/alunos/<int:pk>/editar/', views.AlunoUpdateView.as_view(), name='aluno-update'),
    path('admin-geral/alunos/<int:pk>/toggle/', views.AlunoToggleAtivoView.as_view(), name='aluno-toggle'),
    path('admin-geral/alunos/<int:pk>/resetar-senha/', views.AlunoResetarSenhaView.as_view(), name='aluno-resetar-senha'),
    path('admin-geral/alunos/<int:pk>/excluir/', views.AlunoExcluirView.as_view(), name='aluno-excluir'),

    path('admin-geral/professores/', views.ListaProfessoresView.as_view(), name='professor-list'),
    path('admin-geral/professores/novo/', views.ProfessorCreateView.as_view(), name='professor-create'),
    path('admin-geral/professores/<int:pk>/editar/', views.ProfessorUpdateView.as_view(), name='professor-update'),
    path('admin-geral/professores/<int:pk>/toggle/', views.ProfessorToggleAtivoView.as_view(), name='professor-toggle'),
    path(
        'admin-geral/professores/<int:pk>/resetar-senha/',
        views.ProfessorResetarSenhaView.as_view(),
        name='professor-resetar-senha',
    ),
    path('admin-geral/professores/<int:pk>/excluir/', views.ProfessorExcluirView.as_view(), name='professor-excluir'),

    path('admin-geral/admins-biblioteca/', views.ListaAdminsBibliotecaView.as_view(), name='admin-biblioteca-list'),
    path('admin-geral/admins-biblioteca/novo/', views.AdminBibliotecaCreateView.as_view(), name='admin-biblioteca-create'),
    path(
        'admin-geral/admins-biblioteca/<int:pk>/editar/',
        views.AdminBibliotecaUpdateView.as_view(),
        name='admin-biblioteca-update',
    ),
    path(
        'admin-geral/admins-biblioteca/<int:pk>/toggle/',
        views.AdminBibliotecaToggleAtivoView.as_view(),
        name='admin-biblioteca-toggle',
    ),
    path(
        'admin-geral/admins-biblioteca/<int:pk>/resetar-senha/',
        views.AdminBibliotecaResetarSenhaView.as_view(),
        name='admin-biblioteca-resetar-senha',
    ),
    path(
        'admin-geral/admins-biblioteca/<int:pk>/excluir/',
        views.AdminBibliotecaExcluirView.as_view(),
        name='admin-biblioteca-excluir',
    ),
]
