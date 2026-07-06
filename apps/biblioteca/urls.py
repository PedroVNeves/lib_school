from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.DashboardAdminBibliotecaView.as_view(), name='dashboard-admin-biblioteca'),

    path('livros/', views.CatalogoListView.as_view(), name='livro-list'),
    path('livros/novo/', views.LivroCreateView.as_view(), name='livro-create'),
    path('livros/<int:pk>/', views.LivroDetailView.as_view(), name='livro-detail'),
    path('livros/<int:pk>/editar/', views.LivroUpdateView.as_view(), name='livro-update'),
    path('livros/<int:pk>/exemplares/', views.LivroAddExemplaresView.as_view(), name='livro-add-exemplares'),
    path('livros/<int:pk>/toggle/', views.LivroToggleAtivoView.as_view(), name='livro-toggle'),

    path('autores/', views.AutorListView.as_view(), name='autor-list'),
    path('generos/', views.GeneroListView.as_view(), name='genero-list'),

    path('turmas/', views.TurmaListView.as_view(), name='turma-list'),
    path('turmas/nova/', views.TurmaCreateView.as_view(), name='turma-create'),
    path('turmas/<int:pk>/editar/', views.TurmaUpdateView.as_view(), name='turma-update'),

    path('emprestimos/', views.EmprestimoListView.as_view(), name='emprestimo-list'),
    path('emprestimos/novo/', views.EmprestimoCreateView.as_view(), name='emprestimo-create'),
    path('emprestimos/<int:pk>/devolver/', views.EmprestimoDevolverView.as_view(), name='emprestimo-devolver'),

    path('configuracoes/', views.ConfiguracaoView.as_view(), name='configuracoes'),
    path('logs/', views.AuditLogListView.as_view(), name='auditlog-list'),
]
