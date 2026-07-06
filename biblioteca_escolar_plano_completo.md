# 📚 SISTEMA DE BIBLIOTECA ESCOLAR — PLANO COMPLETO DE DESENVOLVIMENTO

> **Versão:** 1.0  
> **Stack:** Python 3.12 · Django 5.x · Django REST Framework · PostgreSQL 16 · Docker  
> **Interface:** Web Responsiva (Bootstrap 5 / HTMX)  
> **Extras:** E-mail, Relatórios PDF/Excel, API REST  

---

## SUMÁRIO

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Tipos de Usuário e Permissões](#2-tipos-de-usuário-e-permissões)
3. [Requisitos Funcionais (RF)](#3-requisitos-funcionais)
4. [Requisitos Não Funcionais (RNF)](#4-requisitos-não-funcionais)
5. [Regras de Negócio (RN)](#5-regras-de-negócio)
6. [Modelagem de Dados (Entidades)](#6-modelagem-de-dados)
7. [Fluxogramas](#7-fluxogramas)
8. [Estrutura de Rotas (URLs)](#8-estrutura-de-rotas)
9. [Endpoints da API REST](#9-endpoints-da-api-rest)
10. [Estrutura do Projeto Django](#10-estrutura-do-projeto-django)
11. [Configuração Docker](#11-configuração-docker)
12. [Configurações e Parâmetros do Sistema](#12-configurações-e-parâmetros-do-sistema)
13. [Templates e Componentes de Interface](#13-templates-e-componentes-de-interface)
14. [Tarefas Agendadas (Celery)](#14-tarefas-agendadas-celery)
15. [Segurança](#15-segurança)
16. [Checklist de Implementação](#16-checklist-de-implementação)

---

## 1. VISÃO GERAL DO SISTEMA

O **BibliotecaEscolar** é uma plataforma web para gerenciamento completo de uma biblioteca em ambiente escolar. O sistema controla o acervo de livros, empréstimos para alunos e turmas, renovações online, notificações de atraso e geração de relatórios estatísticos.

### Objetivos Principais
- Digitalizar e centralizar o controle de empréstimos de livros
- Permitir que alunos e professores acompanhem seus empréstimos online
- Fornecer relatórios para a coordenação sobre uso do acervo
- Automatizar notificações de devolução e atraso
- Registrar estatísticas por turma, gênero, autor e livro

### Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12, Django 5.x |
| API | Django REST Framework (DRF) |
| Banco de Dados | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Tarefas Assíncronas | Celery 5.x |
| Frontend | Django Templates + Bootstrap 5 + HTMX |
| Relatórios PDF | WeasyPrint |
| Relatórios Excel | openpyxl |
| E-mail | Django Email (SMTP / SendGrid) |
| Containerização | Docker + Docker Compose |
| Servidor Web | Nginx + Gunicorn |
| Autenticação | Django Auth + JWT (API) |

---

## 2. TIPOS DE USUÁRIO E PERMISSÕES

### 2.1 Matriz de Permissões Completa

| Funcionalidade | Admin Geral (Coordenação) | Admin Biblioteca | Professor | Aluno |
|---|:---:|:---:|:---:|:---:|
| Cadastrar alunos | ✅ | ❌ | ❌ | ❌ |
| Editar/desativar alunos | ✅ | ❌ | ❌ | ❌ |
| Cadastrar professores | ✅ | ❌ | ❌ | ❌ |
| Cadastrar responsável biblioteca | ✅ | ❌ | ❌ | ❌ |
| Gerenciar turmas | ✅ | ✅ | ❌ | ❌ |
| Cadastrar livros | ✅ | ✅ | ❌ | ❌ |
| Editar livros | ✅ | ✅ | ❌ | ❌ |
| Registrar empréstimo | ✅ | ✅ | ❌ | ❌ |
| Registrar devolução | ✅ | ✅ | ❌ | ❌ |
| Configurar prazo de empréstimo | ✅ | ✅ | ❌ | ❌ |
| Configurar limite de renovações | ✅ | ✅ | ❌ | ❌ |
| Ver todos os empréstimos | ✅ | ✅ | ❌ | ❌ |
| Ver empréstimos de turma | ✅ | ✅ | ✅ (próprias) | ❌ |
| Ver próprios empréstimos | ✅ | ✅ | ✅ | ✅ |
| Renovar próprio empréstimo | ❌ | ❌ | ✅ | ✅ |
| Ver catálogo de livros | ✅ | ✅ | ✅ | ✅ |
| Visualizar relatórios e estatísticas | ✅ | ✅ | ❌ | ❌ |
| Exportar relatórios PDF/Excel | ✅ | ✅ | ❌ | ❌ |
| Gerenciar configurações do sistema | ✅ | ❌ | ❌ | ❌ |

### 2.2 Descrição Detalhada de Cada Perfil

#### 🔴 Admin Geral (Coordenação)
- **Django Group:** `admin_geral`
- Acesso completo ao sistema
- Único que pode criar, editar e desativar o responsável pela biblioteca
- Único que pode criar e gerenciar professores e alunos
- Acesso ao painel de estatísticas completo
- Pode alterar qualquer configuração do sistema
- Visualiza logs de ações

#### 🟠 Admin Biblioteca (Responsável pela Biblioteca)
- **Django Group:** `admin_biblioteca`
- Gerencia livros: cadastro, edição, categorias, autores, gêneros, exemplares
- Gerencia empréstimos: registra saída e devolução de livros
- Configura parâmetros: prazo de empréstimo, limite de renovações
- Visualiza relatórios e exporta PDF/Excel
- **NÃO pode** criar ou modificar o próprio perfil de responsável ou de outro responsável
- **NÃO pode** cadastrar alunos, professores ou outros administradores

#### 🟡 Professor
- **Django Group:** `professor`
- Visualiza o catálogo de livros disponíveis
- Visualiza seus próprios empréstimos individuais e de suas turmas
- Pode renovar empréstimos individuais (dentro do limite configurado)
- Vê status de atraso dos próprios livros e dos livros da turma
- Não acessa dados de outros professores

#### 🟢 Aluno
- **Django Group:** `aluno`
- Visualiza o catálogo de livros disponíveis (somente leitura)
- Visualiza seus próprios empréstimos
- Vê se está em atraso e há quantos dias
- Pode renovar seus empréstimos (dentro do limite configurado)
- Vê histórico completo de empréstimos passados

---

## 3. REQUISITOS FUNCIONAIS

### RF001 — Autenticação e Sessão
- **RF001.1** O sistema deve permitir login com e-mail e senha
- **RF001.2** O sistema deve suportar autenticação via JWT para a API REST
- **RF001.3** Sessões web devem expirar após período de inatividade configurável
- **RF001.4** Deve haver tela de "Esqueci minha senha" com envio de link por e-mail
- **RF001.5** O sistema deve redirecionar o usuário para o painel correspondente ao seu perfil após login
- **RF001.6** Deve registrar data/hora do último login

### RF002 — Gerenciamento de Usuários

#### RF002.1 — Alunos
- **RF002.1.1** Admin Geral pode cadastrar alunos com: nome completo, matrícula (única), e-mail, turma, data de nascimento, responsável (nome/contato)
- **RF002.1.2** Admin Geral pode editar dados de alunos
- **RF002.1.3** Admin Geral pode desativar alunos (soft delete — mantém histórico)
- **RF002.1.4** Sistema deve impedir empréstimos para alunos desativados
- **RF002.1.5** Admin pode importar lista de alunos via CSV

#### RF002.2 — Professores
- **RF002.2.1** Admin Geral pode cadastrar professores com: nome completo, matrícula funcional (única), e-mail, disciplinas, turmas vinculadas
- **RF002.2.2** Admin Geral pode editar e desativar professores
- **RF002.2.3** Professor pode atualizar próprio e-mail e senha

#### RF002.3 — Responsável pela Biblioteca
- **RF002.3.1** Apenas Admin Geral pode cadastrar responsável pela biblioteca
- **RF002.3.2** Pode haver mais de um responsável cadastrado (equipe da biblioteca)
- **RF002.3.3** Admin Geral pode desativar responsável da biblioteca

### RF003 — Gerenciamento de Turmas
- **RF003.1** Admin Geral e Admin Biblioteca podem criar turmas com: código (ex: "6A", "7B"), ano letivo, nível (fundamental I, fundamental II, médio), turno (manhã, tarde, noite), professor(es) vinculado(s)
- **RF003.2** Turmas podem ter múltiplos professores vinculados
- **RF003.3** Alunos são vinculados a uma turma por vez
- **RF003.4** Turmas podem ser arquivadas ao final do ano letivo (mantém histórico)

### RF004 — Gerenciamento do Acervo

#### RF004.1 — Livros
- **RF004.1.1** Admin Biblioteca pode cadastrar livros com: título, autor(es), editora, ISBN, ano de publicação, gênero(s), número de exemplares físicos, número de páginas, capa (imagem), sinopse, localização na prateleira (código)
- **RF004.1.2** Cada livro pode ter múltiplos autores e múltiplos gêneros
- **RF004.1.3** Sistema controla quantidade de exemplares disponíveis automaticamente
- **RF004.1.4** Admin pode adicionar ou remover exemplares de um livro existente
- **RF004.1.5** Livros podem ser cadastrados via ISBN com busca automática de dados (Open Library API)
- **RF004.1.6** Livros podem ser desativados (retirados do acervo sem exclusão)

#### RF004.2 — Categorias e Gêneros
- **RF004.2.1** Admin pode gerenciar lista de gêneros literários (ficção, não-ficção, didático, etc.)
- **RF004.2.2** Admin pode gerenciar lista de autores com: nome, nacionalidade, biografia curta

### RF005 — Gerenciamento de Empréstimos

#### RF005.1 — Empréstimo Individual (Aluno ou Professor)
- **RF005.1.1** Admin Biblioteca registra empréstimo informando: usuário (aluno ou professor), livro, exemplar, data de saída (auto: hoje), data prevista de devolução (calculada automaticamente pelo prazo configurado)
- **RF005.1.2** Sistema verifica se há exemplares disponíveis antes de permitir empréstimo
- **RF005.1.3** Sistema verifica se o usuário já tem empréstimos em atraso antes de permitir novo empréstimo
- **RF005.1.4** Sistema verifica se o usuário atingiu o limite máximo de livros simultâneos (configurável)
- **RF005.1.5** Sistema verifica se o usuário está ativo (não desativado)
- **RF005.1.6** Empréstimo gera registro com: ID único, data/hora de saída, responsável que registrou, status (ativo, devolvido, atrasado, renovado)

#### RF005.2 — Empréstimo para Turma (Professor)
- **RF005.2.1** Admin Biblioteca pode registrar empréstimo de múltiplos livros para uma turma
- **RF005.2.2** O empréstimo de turma é vinculado ao professor responsável e à turma
- **RF005.2.3** Deve-se informar: turma, professor responsável, lista de livros (título + quantidade de exemplares), data de saída, data prevista de devolução
- **RF005.2.4** Cada livro do empréstimo de turma é um registro separado, mas todos vinculados ao mesmo "Empréstimo de Turma" (agrupamento)
- **RF005.2.5** Professor visualiza todos os livros do empréstimo da sua turma
- **RF005.2.6** Empréstimos de turma aparecem nos relatórios separados dos individuais

#### RF005.3 — Devolução
- **RF005.3.1** Admin Biblioteca registra devolução informando: ID do empréstimo ou busca por usuário/livro
- **RF005.3.2** Sistema calcula automaticamente se houve atraso e quantos dias
- **RF005.3.3** Devolução atualiza a quantidade de exemplares disponíveis
- **RF005.3.4** Sistema registra data/hora real da devolução e responsável que registrou

#### RF005.4 — Renovação Online
- **RF005.4.1** Aluno e Professor podem renovar empréstimos pelo painel próprio
- **RF005.4.2** Renovação só é permitida se o empréstimo não estiver atrasado
- **RF005.4.3** Cada renovação estende a data de devolução pelo prazo padrão configurado
- **RF005.4.4** O número máximo de renovações por empréstimo é configurável pelo Admin Biblioteca
- **RF005.4.5** Sistema registra: quantidade de renovações feitas, datas de cada renovação, usuário que renovou
- **RF005.4.6** Após atingir o limite, o botão de renovar é desabilitado com mensagem explicativa
- **RF005.4.7** Renovação envia e-mail de confirmação com nova data de devolução

### RF006 — Notificações por E-mail
- **RF006.1** Sistema envia e-mail de confirmação quando empréstimo é registrado (com data de devolução)
- **RF006.2** Sistema envia e-mail de lembrete 3 dias antes do vencimento (configurável)
- **RF006.3** Sistema envia e-mail de lembrete 1 dia antes do vencimento
- **RF006.4** Sistema envia e-mail no dia do vencimento
- **RF006.5** Sistema envia e-mail diário enquanto o empréstimo estiver atrasado (até limite configurável de dias)
- **RF006.6** Sistema envia e-mail de confirmação de devolução
- **RF006.7** Sistema envia e-mail de confirmação de renovação com nova data
- **RF006.8** Para empréstimos de turma, e-mail é enviado ao professor responsável
- **RF006.9** Admin pode configurar quais tipos de notificação estão ativos

### RF007 — Painel e Estatísticas

#### RF007.1 — Dashboard Geral (Admin Geral e Admin Biblioteca)
- **RF007.1.1** Total de livros no acervo (títulos e exemplares)
- **RF007.1.2** Quantidade de empréstimos ativos no momento
- **RF007.1.3** Quantidade de empréstimos em atraso (com lista)
- **RF007.1.4** Quantidade de devoluções hoje e na semana
- **RF007.1.5** Gráfico de empréstimos por mês (últimos 12 meses)
- **RF007.1.6** Top 10 livros mais emprestados
- **RF007.1.7** Top 5 gêneros mais emprestados
- **RF007.1.8** Top 5 autores mais emprestados
- **RF007.1.9** Top 5 turmas que mais emprestam livros
- **RF007.1.10** Quantidade de alunos e professores cadastrados e ativos

#### RF007.2 — Relatórios Exportáveis
- **RF007.2.1** Relatório de empréstimos ativos (PDF/Excel)
- **RF007.2.2** Relatório de empréstimos em atraso (PDF/Excel)
- **RF007.2.3** Relatório de histórico de empréstimos por período (PDF/Excel)
- **RF007.2.4** Relatório de empréstimos por turma (PDF/Excel)
- **RF007.2.5** Relatório do acervo completo (PDF/Excel)
- **RF007.2.6** Relatório de livros mais emprestados (PDF/Excel)
- **RF007.2.7** Relatório de usuários com empréstimos em atraso (PDF/Excel)
- **RF007.2.8** Todos os relatórios incluem: data de geração, filtros aplicados, nome do sistema

#### RF007.3 — Painel do Professor
- **RF007.3.1** Lista dos próprios empréstimos ativos com status e dias restantes
- **RF007.3.2** Lista de empréstimos das suas turmas
- **RF007.3.3** Alerta visual para empréstimos vencidos ou próximos do vencimento
- **RF007.3.4** Histórico de empréstimos devolvidos
- **RF007.3.5** Botão de renovação para empréstimos elegíveis

#### RF007.4 — Painel do Aluno
- **RF007.4.1** Lista dos empréstimos ativos com: capa do livro, título, data de devolução, dias restantes, status (ok / próximo do vencimento / atrasado)
- **RF007.4.2** Indicador visual claro de atraso (dias em atraso)
- **RF007.4.3** Botão de renovação para empréstimos elegíveis
- **RF007.4.4** Histórico de empréstimos devolvidos
- **RF007.4.5** Número de renovações utilizadas e restantes por empréstimo

### RF008 — Configurações do Sistema
- **RF008.1** Admin pode configurar prazo padrão de empréstimo para alunos (em dias)
- **RF008.2** Admin pode configurar prazo padrão de empréstimo para professores (em dias)
- **RF008.3** Admin pode configurar prazo padrão de empréstimo de turma (em dias)
- **RF008.4** Admin pode configurar número máximo de renovações por empréstimo
- **RF008.5** Admin pode configurar número máximo de livros simultâneos por aluno
- **RF008.6** Admin pode configurar número máximo de livros simultâneos por professor
- **RF008.7** Admin pode configurar dias de antecedência para lembrete de vencimento
- **RF008.8** Admin pode configurar dados da escola (nome, logo, endereço) para cabeçalho dos relatórios

### RF009 — Catálogo Público Interno
- **RF009.1** Todos os usuários logados podem buscar livros no catálogo
- **RF009.2** Busca por: título, autor, ISBN, gênero, disponibilidade
- **RF009.3** Página de detalhes do livro mostra: capa, sinopse, autores, gêneros, quantidade disponível (sem revelar quem está com o livro)
- **RF009.4** Filtros: disponível agora, gênero, autor, ano de publicação

### RF010 — Logs e Auditoria
- **RF010.1** Sistema registra log de todas as ações administrativas (quem fez, o quê, quando)
- **RF010.2** Admin Geral pode visualizar log de auditoria com filtros por usuário, data e ação
- **RF010.3** Logs não podem ser deletados pela interface

---

## 4. REQUISITOS NÃO FUNCIONAIS

| Código | Categoria | Descrição |
|---|---|---|
| RNF001 | Performance | Páginas devem carregar em menos de 2 segundos para até 200 usuários simultâneos |
| RNF002 | Disponibilidade | Sistema deve ter uptime mínimo de 99% em horário escolar |
| RNF003 | Segurança | Senhas armazenadas com hashing bcrypt |
| RNF004 | Segurança | Proteção contra CSRF em todos os formulários |
| RNF005 | Segurança | Rate limiting em endpoints de login (máx 10 tentativas / 10 min) |
| RNF006 | Segurança | Tokens JWT com expiração de 24h para API |
| RNF007 | Usabilidade | Interface responsiva (mobile-first), compatível com Chrome, Firefox, Safari, Edge |
| RNF008 | Usabilidade | Feedbacks visuais claros: mensagens de sucesso, erro e alerta |
| RNF009 | Manutenibilidade | Cobertura de testes unitários mínima de 70% |
| RNF010 | Manutenibilidade | Código documentado com docstrings |
| RNF011 | Portabilidade | Toda a aplicação containerizada via Docker Compose |
| RNF012 | Escalabilidade | Arquitetura preparada para adicionar novos tipos de relatório |
| RNF013 | Acessibilidade | Interface com contraste adequado e labels em formulários (WCAG AA) |
| RNF014 | Dados | Backups automáticos diários do banco de dados |
| RNF015 | E-mail | Envio de e-mails de forma assíncrona (não bloqueia a interface) |

---

## 5. REGRAS DE NEGÓCIO

| Código | Regra |
|---|---|
| RN001 | Um livro só pode ser emprestado se houver ao menos 1 exemplar disponível |
| RN002 | Um aluno/professor com empréstimo em atraso não pode pegar novo livro |
| RN003 | Um aluno não pode ter mais livros simultâneos que o limite configurado (padrão: 3) |
| RN004 | Um professor não pode ter mais livros simultâneos que o limite configurado (padrão: 10) |
| RN005 | Renovação só pode ser feita se o empréstimo não estiver atrasado |
| RN006 | Renovação só pode ser feita até o limite máximo de renovações configurado |
| RN007 | A nova data de devolução após renovação é calculada a partir da data atual + prazo padrão |
| RN008 | Status do empréstimo é calculado dinamicamente: Ativo, Próximo do vencimento (≤ 3 dias), Atrasado, Devolvido |
| RN009 | Empréstimo de turma pode incluir múltiplos títulos e múltiplos exemplares do mesmo título |
| RN010 | A quantidade de exemplares emprestados para turma não pode exceder o total disponível |
| RN011 | Ao desativar um aluno/professor, seus empréstimos ativos continuam visíveis para o Admin |
| RN012 | Soft delete: nenhum dado é deletado permanentemente (apenas desativado) |
| RN013 | O ISBN deve ser único por livro (quando informado) |
| RN014 | A matrícula do aluno e a matrícula funcional do professor devem ser únicas |
| RN015 | Empréstimos de turma são contabilizados separadamente dos individuais nas estatísticas |
| RN016 | Um professor só pode renovar empréstimos de turma das suas próprias turmas |
| RN017 | Logs de auditoria são somente leitura para qualquer usuário via interface |
| RN018 | Configurações do sistema só podem ser alteradas por Admin Geral ou Admin Biblioteca (exceto RF008.8, somente Admin Geral) |

---

## 6. MODELAGEM DE DADOS

### 6.1 Diagrama de Entidades (descrição textual)

```
Escola
├── Turma (N) ──── Ano Letivo
│   ├── Aluno (N)
│   └── Professor (N) [many-to-many]
│
Usuário (auth.User estendido)
├── PerfilAdminGeral
├── PerfilAdminBiblioteca
├── PerfilProfessor ────── Turma (many-to-many)
└── PerfilAluno ─────────── Turma (FK)
│
Acervo
├── Autor (N)
├── Genero (N)
└── Livro (N)
    ├── Autor (many-to-many)
    ├── Genero (many-to-many)
    └── Exemplar (N) [quantidade física]
│
Empréstimo
├── EmprestimoIndividual ──── Usuário + Livro + Exemplar
│   └── Renovacao (N)
└── EmprestimoTurma ──────── Professor + Turma
    └── ItemEmprestimoTurma (N) ──── Livro + Exemplar(es)
│
Configuracao (singleton)
Notificacao
AuditLog
```

### 6.2 Modelos Django Detalhados

```python
# ============================================================
# APP: accounts
# ============================================================

class Usuario(AbstractUser):
    """Usuário base do sistema."""
    TIPO_CHOICES = [
        ('admin_geral', 'Admin Geral'),
        ('admin_biblioteca', 'Admin Biblioteca'),
        ('professor', 'Professor'),
        ('aluno', 'Aluno'),
    ]
    tipo = CharField(max_length=20, choices=TIPO_CHOICES)
    email = EmailField(unique=True)
    foto = ImageField(upload_to='usuarios/', null=True, blank=True)
    ativo = BooleanField(default=True)
    criado_em = DateTimeField(auto_now_add=True)
    atualizado_em = DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class PerfilAluno(Model):
    usuario = OneToOneField(Usuario, on_delete=CASCADE, related_name='perfil_aluno')
    matricula = CharField(max_length=20, unique=True)
    turma = ForeignKey('biblioteca.Turma', on_delete=SET_NULL, null=True)
    data_nascimento = DateField()
    responsavel_nome = CharField(max_length=200)
    responsavel_contato = CharField(max_length=20)


class PerfilProfessor(Model):
    usuario = OneToOneField(Usuario, on_delete=CASCADE, related_name='perfil_professor')
    matricula_funcional = CharField(max_length=20, unique=True)
    disciplinas = CharField(max_length=500)
    turmas = ManyToManyField('biblioteca.Turma', related_name='professores', blank=True)


class PerfilAdminBiblioteca(Model):
    usuario = OneToOneField(Usuario, on_delete=CASCADE, related_name='perfil_biblioteca')
    registro_funcional = CharField(max_length=20, unique=True)


# ============================================================
# APP: biblioteca
# ============================================================

class Turma(Model):
    NIVEL_CHOICES = [
        ('fund1', 'Fundamental I'),
        ('fund2', 'Fundamental II'),
        ('medio', 'Ensino Médio'),
    ]
    TURNO_CHOICES = [
        ('manha', 'Manhã'),
        ('tarde', 'Tarde'),
        ('noite', 'Noite'),
        ('integral', 'Integral'),
    ]
    codigo = CharField(max_length=10)          # ex: "6A", "9B"
    ano_letivo = IntegerField()                # ex: 2025
    nivel = CharField(max_length=10, choices=NIVEL_CHOICES)
    turno = CharField(max_length=10, choices=TURNO_CHOICES)
    ativa = BooleanField(default=True)
    criado_em = DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['codigo', 'ano_letivo']


class Autor(Model):
    nome = CharField(max_length=200)
    nacionalidade = CharField(max_length=100, blank=True)
    biografia = TextField(blank=True)


class Genero(Model):
    nome = CharField(max_length=100, unique=True)   # ex: Ficção, Romance, Didático
    descricao = TextField(blank=True)


class Livro(Model):
    titulo = CharField(max_length=500)
    autores = ManyToManyField(Autor, related_name='livros')
    editora = CharField(max_length=200, blank=True)
    isbn = CharField(max_length=20, unique=True, null=True, blank=True)
    ano_publicacao = IntegerField(null=True, blank=True)
    generos = ManyToManyField(Genero, related_name='livros')
    total_exemplares = IntegerField(default=1)
    exemplares_disponiveis = IntegerField(default=1)  # calculado automaticamente
    num_paginas = IntegerField(null=True, blank=True)
    capa = ImageField(upload_to='capas/', null=True, blank=True)
    sinopse = TextField(blank=True)
    localizacao_prateleira = CharField(max_length=50, blank=True)  # ex: "A-12"
    ativo = BooleanField(default=True)
    criado_em = DateTimeField(auto_now_add=True)
    atualizado_em = DateTimeField(auto_now=True)
    
    @property
    def disponivel(self):
        return self.exemplares_disponiveis > 0


class Exemplar(Model):
    """Representa um exemplar físico de um livro."""
    STATUS_CHOICES = [
        ('disponivel', 'Disponível'),
        ('emprestado', 'Emprestado'),
        ('reservado', 'Reservado'),
        ('danificado', 'Danificado'),
        ('perdido', 'Perdido'),
    ]
    livro = ForeignKey(Livro, on_delete=CASCADE, related_name='exemplares')
    codigo_tombamento = CharField(max_length=50, unique=True)   # ex: "LIV-00123"
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='disponivel')
    condicao = CharField(max_length=100, blank=True)            # observações físicas
    adquirido_em = DateField(null=True, blank=True)


class Emprestimo(Model):
    """Empréstimo individual para aluno ou professor."""
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('atrasado', 'Atrasado'),
        ('devolvido', 'Devolvido'),
        ('renovado', 'Renovado'),
    ]
    usuario = ForeignKey(Usuario, on_delete=PROTECT, related_name='emprestimos')
    livro = ForeignKey(Livro, on_delete=PROTECT)
    exemplar = ForeignKey(Exemplar, on_delete=PROTECT, null=True)
    data_saida = DateTimeField(auto_now_add=True)
    data_prevista_devolucao = DateField()
    data_real_devolucao = DateField(null=True, blank=True)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    registrado_por = ForeignKey(Usuario, on_delete=SET_NULL, null=True, related_name='emprestimos_registrados')
    renovacoes_realizadas = IntegerField(default=0)
    observacoes = TextField(blank=True)
    criado_em = DateTimeField(auto_now_add=True)
    atualizado_em = DateTimeField(auto_now=True)
    
    @property
    def dias_atraso(self):
        if self.status != 'devolvido' and date.today() > self.data_prevista_devolucao:
            return (date.today() - self.data_prevista_devolucao).days
        return 0
    
    @property
    def pode_renovar(self):
        config = Configuracao.get_solo()
        return (
            self.dias_atraso == 0 and
            self.status != 'devolvido' and
            self.renovacoes_realizadas < config.max_renovacoes
        )


class Renovacao(Model):
    emprestimo = ForeignKey(Emprestimo, on_delete=CASCADE, related_name='renovacoes')
    data_renovacao = DateTimeField(auto_now_add=True)
    nova_data_devolucao = DateField()
    renovado_por = ForeignKey(Usuario, on_delete=SET_NULL, null=True)


class EmprestimoTurma(Model):
    """Agrupamento de empréstimos feitos para uma turma."""
    turma = ForeignKey(Turma, on_delete=PROTECT)
    professor_responsavel = ForeignKey(Usuario, on_delete=PROTECT, related_name='emprestimos_turma')
    data_saida = DateTimeField(auto_now_add=True)
    data_prevista_devolucao = DateField()
    data_real_devolucao = DateField(null=True, blank=True)
    devolvido = BooleanField(default=False)
    registrado_por = ForeignKey(Usuario, on_delete=SET_NULL, null=True, related_name='emprestimos_turma_registrados')
    observacoes = TextField(blank=True)
    criado_em = DateTimeField(auto_now_add=True)


class ItemEmprestimoTurma(Model):
    """Item individual dentro de um empréstimo de turma."""
    emprestimo_turma = ForeignKey(EmprestimoTurma, on_delete=CASCADE, related_name='itens')
    livro = ForeignKey(Livro, on_delete=PROTECT)
    exemplar = ForeignKey(Exemplar, on_delete=PROTECT)
    devolvido = BooleanField(default=False)
    data_devolucao = DateField(null=True, blank=True)


class Configuracao(Model):
    """Singleton de configurações do sistema."""
    prazo_emprestimo_aluno = IntegerField(default=14)          # dias
    prazo_emprestimo_professor = IntegerField(default=30)      # dias
    prazo_emprestimo_turma = IntegerField(default=7)           # dias
    max_renovacoes = IntegerField(default=2)
    max_livros_aluno = IntegerField(default=3)
    max_livros_professor = IntegerField(default=10)
    dias_lembrete_vencimento = IntegerField(default=3)         # enviar lembrete X dias antes
    max_dias_notificacao_atraso = IntegerField(default=30)     # parar de notificar após X dias
    # Dados da escola
    nome_escola = CharField(max_length=200, default='Escola')
    logo = ImageField(upload_to='escola/', null=True, blank=True)
    endereco_escola = CharField(max_length=500, blank=True)
    # Notificações ativas
    notif_confirmacao_emprestimo = BooleanField(default=True)
    notif_lembrete_vencimento = BooleanField(default=True)
    notif_atraso = BooleanField(default=True)
    notif_confirmacao_devolucao = BooleanField(default=True)
    notif_confirmacao_renovacao = BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Configuração'


class Notificacao(Model):
    """Registro de notificações enviadas."""
    TIPO_CHOICES = [
        ('confirmacao_emprestimo', 'Confirmação de Empréstimo'),
        ('lembrete_vencimento', 'Lembrete de Vencimento'),
        ('atraso', 'Atraso'),
        ('confirmacao_devolucao', 'Confirmação de Devolução'),
        ('confirmacao_renovacao', 'Confirmação de Renovação'),
    ]
    usuario = ForeignKey(Usuario, on_delete=CASCADE)
    emprestimo = ForeignKey(Emprestimo, on_delete=CASCADE, null=True)
    tipo = CharField(max_length=50, choices=TIPO_CHOICES)
    enviado_em = DateTimeField(auto_now_add=True)
    sucesso = BooleanField(default=True)
    erro_msg = TextField(blank=True)


class AuditLog(Model):
    """Log de ações administrativas."""
    usuario = ForeignKey(Usuario, on_delete=SET_NULL, null=True)
    acao = CharField(max_length=200)                 # ex: "Registrou empréstimo #45"
    modelo = CharField(max_length=100)               # ex: "Emprestimo"
    objeto_id = IntegerField(null=True)
    detalhes = JSONField(default=dict)
    ip = CharField(max_length=50, blank=True)
    criado_em = DateTimeField(auto_now_add=True)
```

---

## 7. FLUXOGRAMAS

### 7.1 Fluxo de Login e Redirecionamento

```
[Acesso ao Sistema]
        │
        ▼
[Tela de Login: E-mail + Senha]
        │
   ┌────┴────┐
   │Credenciais│
   │ inválidas │──────► [Exibir erro + contagem tentativas]
   └────┬────┘              │ (após 10 tentativas: bloqueio 10min)
        │ válidas
        ▼
  [Verificar tipo de usuário]
        │
   ┌────┴───────────────────────────┐
   │                                │
   ▼                                ▼
[Admin Geral]  [Admin Biblioteca]  [Professor]  [Aluno]
   │                │                 │            │
   ▼                ▼                 ▼            ▼
[Dashboard     [Dashboard        [Painel       [Painel
 Coordenação]   Biblioteca]       Professor]    Aluno]
```

### 7.2 Fluxo de Registro de Empréstimo Individual

```
[Admin Biblioteca acessa "Novo Empréstimo"]
        │
        ▼
[Busca Usuário (nome/matrícula)]
        │
   ┌────┴────┐
   │Usuário  │──► [Erro: usuário não encontrado]
   │inativo  │
   └────┬────┘
        │ ativo
        ▼
[Verificar empréstimos em atraso?]
        │
   ┌────┴────┐
   │   SIM   │──► [Bloquear + Mostrar lista de atrasos]
   └────┬────┘
        │ NÃO
        ▼
[Verificar limite de livros simultâneos?]
        │
   ┌────┴────┐
   │atingiu  │──► [Bloquear + Informar limite]
   └────┬────┘
        │ dentro do limite
        ▼
[Buscar Livro (título/ISBN/autor)]
        │
        ▼
[Verificar exemplares disponíveis]
        │
   ┌────┴────┐
   │  0 disp │──► [Informar indisponibilidade]
   └────┬────┘
        │ disponível
        ▼
[Selecionar exemplar específico (ou auto-selecionar)]
        │
        ▼
[Confirmar: Usuário + Livro + Data prevista devolução]
        │
        ▼
[Criar Emprestimo → Atualizar exemplares_disponiveis]
        │
        ▼
[Criar AuditLog → Enviar e-mail de confirmação (async)]
        │
        ▼
[Redirecionar para detalhes do empréstimo]
```

### 7.3 Fluxo de Renovação Online (Aluno/Professor)

```
[Usuário acessa "Meus Empréstimos"]
        │
        ▼
[Lista de empréstimos ativos]
        │
        ▼
[Clica em "Renovar" em um empréstimo]
        │
        ▼
[Verificar: está atrasado?]
        │
   ┌────┴────┐
   │   SIM   │──► [Exibir erro: "Não é possível renovar empréstimos em atraso"]
   └────┬────┘
        │ NÃO
        ▼
[Verificar: atingiu limite de renovações?]
        │
   ┌────┴────┐
   │   SIM   │──► [Exibir erro: "Limite de renovações atingido. Devolva o livro."]
   └────┴────┘
        │ NÃO
        ▼
[Calcular nova data: hoje + prazo_emprestimo_aluno/professor]
        │
        ▼
[Criar Renovacao → Atualizar Emprestimo (nova data + contador)]
        │
        ▼
[Enviar e-mail de confirmação (async)]
        │
        ▼
[Atualizar tela com nova data e renovações restantes]
```

### 7.4 Fluxo de Empréstimo de Turma

```
[Admin Biblioteca: "Novo Empréstimo de Turma"]
        │
        ▼
[Selecionar Turma]
        │
        ▼
[Selecionar Professor Responsável]
        │
        ▼
[Adicionar livros à lista]
        │ (loop para cada livro)
        ▼
[Buscar Livro → Informar quantidade de exemplares]
        │
        ▼
[Verificar: quantidade solicitada ≤ exemplares disponíveis?]
        │
   ┌────┴────┐
   │   NÃO   │──► [Erro: disponível apenas X exemplares]
   └────┬────┘
        │ SIM
        ▼
[Confirmar lista completa]
        │
        ▼
[Criar EmprestimoTurma + ItemEmprestimoTurma(s)]
[Atualizar exemplares_disponiveis para cada livro]
        │
        ▼
[Criar AuditLog → Enviar e-mail ao professor (async)]
        │
        ▼
[Exibir resumo do empréstimo de turma]
```

### 7.5 Fluxo de Devolução

```
[Admin Biblioteca: "Registrar Devolução"]
        │
        ▼
[Busca por: ID empréstimo / nome usuário / título livro]
        │
        ▼
[Exibir detalhes: usuário, livro, data prevista, status]
        │
        ▼
[Confirmar devolução]
        │
        ▼
[Registrar data_real_devolucao = hoje]
[Status = 'devolvido']
[Exemplar status = 'disponivel']
[Atualizar exemplares_disponiveis do Livro]
        │
        ▼
[Calcular dias de atraso (se houver) → registrar em log]
        │
        ▼
[Criar AuditLog → Enviar e-mail de confirmação (async)]
        │
        ▼
[Confirmação na tela + opção de novo empréstimo para o mesmo usuário]
```

### 7.6 Fluxo de Notificações Automáticas (Celery)

```
[Tarefa Celery: executada diariamente às 08:00]
        │
        ▼
[Buscar todos Emprestimos com status != 'devolvido']
        │
        ▼ (para cada empréstimo)
[Calcular dias para vencimento]
        │
        ├── dias == 3 → Enviar "Lembrete: vence em 3 dias"
        ├── dias == 1 → Enviar "Lembrete: vence amanhã"
        ├── dias == 0 → Enviar "Atenção: vence hoje"
        └── dias < 0  → Enviar "Atraso: X dias em atraso"
                              │
                         [Verificar: já foram notificados hoje?]
                         [Verificar: dentro do limite de notificações?]
                              │
                         [Registrar em Notificacao]
                         [Enviar e-mail async]
```

---

## 8. ESTRUTURA DE ROTAS (URLs)

```python
# urls raiz
urlpatterns = [
    # Auth
    path('', views.redirect_dashboard, name='home'),
    path('login/', auth_views.LoginView, name='login'),
    path('logout/', auth_views.LogoutView, name='logout'),
    path('senha/resetar/', ..., name='password_reset'),
    
    # Dashboard (redireciona por tipo)
    path('dashboard/', views.DashboardView, name='dashboard'),
    
    # Admin Geral
    path('admin-geral/', include('accounts.urls_admin')),
    
    # Gestão da Biblioteca (Admin Geral + Admin Biblioteca)
    path('biblioteca/', include('biblioteca.urls')),
    
    # Painel do Professor
    path('professor/', include('accounts.urls_professor')),
    
    # Painel do Aluno
    path('aluno/', include('accounts.urls_aluno')),
    
    # API REST
    path('api/v1/', include('api.urls')),
    
    # Admin Django (superuser)
    path('admin/', admin.site.urls),
]

# biblioteca/urls.py
urlpatterns = [
    # Livros
    path('livros/', LivroListView, name='livro-list'),
    path('livros/novo/', LivroCreateView, name='livro-create'),
    path('livros/<int:pk>/', LivroDetailView, name='livro-detail'),
    path('livros/<int:pk>/editar/', LivroUpdateView, name='livro-update'),
    
    # Empréstimos
    path('emprestimos/', EmprestimoListView, name='emprestimo-list'),
    path('emprestimos/novo/', EmprestimoCreateView, name='emprestimo-create'),
    path('emprestimos/<int:pk>/', EmprestimoDetailView, name='emprestimo-detail'),
    path('emprestimos/<int:pk>/devolver/', EmprestimoDevolverView, name='emprestimo-devolver'),
    
    # Empréstimos de Turma
    path('emprestimos/turma/', EmprestimoTurmaListView, name='emprestimo-turma-list'),
    path('emprestimos/turma/novo/', EmprestimoTurmaCreateView, name='emprestimo-turma-create'),
    path('emprestimos/turma/<int:pk>/', EmprestimoTurmaDetailView, name='emprestimo-turma-detail'),
    
    # Turmas
    path('turmas/', TurmaListView, name='turma-list'),
    path('turmas/nova/', TurmaCreateView, name='turma-create'),
    path('turmas/<int:pk>/', TurmaDetailView, name='turma-detail'),
    
    # Relatórios
    path('relatorios/', RelatorioIndexView, name='relatorio-index'),
    path('relatorios/ativos/pdf/', RelatorioAtivosPDFView, name='relatorio-ativos-pdf'),
    path('relatorios/ativos/excel/', RelatorioAtivosExcelView, name='relatorio-ativos-excel'),
    path('relatorios/atrasos/pdf/', RelatorioAtrasosPDFView, name='relatorio-atrasos-pdf'),
    path('relatorios/historico/pdf/', RelatorioHistoricoPDFView, name='relatorio-historico-pdf'),
    path('relatorios/turmas/pdf/', RelatorioTurmasPDFView, name='relatorio-turmas-pdf'),
    path('relatorios/acervo/pdf/', RelatorioAcervoPDFView, name='relatorio-acervo-pdf'),
    
    # Configurações
    path('configuracoes/', ConfiguracaoView, name='configuracoes'),
    
    # Logs
    path('logs/', AuditLogListView, name='auditlog-list'),
    
    # Dashboard Estatísticas
    path('estatisticas/', EstatisticasView, name='estatisticas'),
    path('estatisticas/dados/', EstatisticasDadosView, name='estatisticas-dados'),  # AJAX/HTMX
]
```

---

## 9. ENDPOINTS DA API REST

### Autenticação
```
POST   /api/v1/auth/token/            → Obter token JWT
POST   /api/v1/auth/token/refresh/    → Renovar token JWT
POST   /api/v1/auth/token/verify/     → Verificar token JWT
```

### Usuários
```
GET    /api/v1/usuarios/              → Listar usuários [Admin]
POST   /api/v1/usuarios/              → Criar usuário [Admin Geral]
GET    /api/v1/usuarios/{id}/         → Detalhe do usuário [Admin]
PUT    /api/v1/usuarios/{id}/         → Atualizar usuário [Admin Geral]
PATCH  /api/v1/usuarios/{id}/         → Atualização parcial [Admin Geral]
DELETE /api/v1/usuarios/{id}/         → Desativar usuário [Admin Geral]

GET    /api/v1/usuarios/me/           → Perfil do usuário logado
PATCH  /api/v1/usuarios/me/           → Atualizar próprio perfil
```

### Livros
```
GET    /api/v1/livros/                → Listar livros (com busca e filtros) [Todos]
POST   /api/v1/livros/                → Criar livro [Admin Biblioteca]
GET    /api/v1/livros/{id}/           → Detalhe do livro [Todos]
PUT    /api/v1/livros/{id}/           → Atualizar livro [Admin Biblioteca]
PATCH  /api/v1/livros/{id}/           → Atualização parcial [Admin Biblioteca]
DELETE /api/v1/livros/{id}/           → Desativar livro [Admin Biblioteca]

GET    /api/v1/livros/?search=        → Busca por título/autor/ISBN
GET    /api/v1/livros/?genero=        → Filtro por gênero
GET    /api/v1/livros/?disponivel=true → Filtro por disponibilidade
```

### Autores e Gêneros
```
GET    /api/v1/autores/               → Listar autores
POST   /api/v1/autores/               → Criar autor [Admin Biblioteca]
GET    /api/v1/generos/               → Listar gêneros
POST   /api/v1/generos/               → Criar gênero [Admin Biblioteca]
```

### Turmas
```
GET    /api/v1/turmas/                → Listar turmas [Admin]
POST   /api/v1/turmas/                → Criar turma [Admin]
GET    /api/v1/turmas/{id}/           → Detalhe da turma [Admin + Prof da turma]
PUT    /api/v1/turmas/{id}/           → Atualizar turma [Admin]
```

### Empréstimos
```
GET    /api/v1/emprestimos/           → Listar empréstimos [Admin] / próprios [Aluno/Prof]
POST   /api/v1/emprestimos/           → Criar empréstimo [Admin Biblioteca]
GET    /api/v1/emprestimos/{id}/      → Detalhe do empréstimo
PATCH  /api/v1/emprestimos/{id}/devolver/ → Registrar devolução [Admin Biblioteca]

POST   /api/v1/emprestimos/{id}/renovar/ → Renovar empréstimo [Aluno/Professor]

GET    /api/v1/emprestimos/turma/     → Listar empréstimos de turma [Admin + Prof]
POST   /api/v1/emprestimos/turma/     → Criar empréstimo de turma [Admin Biblioteca]
GET    /api/v1/emprestimos/turma/{id}/  → Detalhe do empréstimo de turma
```

### Relatórios (endpoints de download)
```
GET    /api/v1/relatorios/ativos/?formato=pdf     → PDF empréstimos ativos
GET    /api/v1/relatorios/ativos/?formato=excel   → Excel empréstimos ativos
GET    /api/v1/relatorios/atrasos/?formato=pdf    → PDF em atraso
GET    /api/v1/relatorios/historico/?formato=pdf&data_inicio=&data_fim= → Histórico
GET    /api/v1/relatorios/turmas/?formato=excel   → Excel por turma
GET    /api/v1/relatorios/acervo/?formato=pdf     → PDF acervo completo
```

### Estatísticas
```
GET    /api/v1/estatisticas/dashboard/    → Dados do dashboard [Admin]
GET    /api/v1/estatisticas/livros/top/   → Top livros emprestados [Admin]
GET    /api/v1/estatisticas/turmas/top/   → Top turmas [Admin]
GET    /api/v1/estatisticas/generos/      → Empréstimos por gênero [Admin]
GET    /api/v1/estatisticas/mensal/       → Empréstimos por mês [Admin]
```

### Configurações
```
GET    /api/v1/configuracoes/             → Ver configurações [Admin]
PATCH  /api/v1/configuracoes/             → Atualizar configurações [Admin Biblioteca / Admin Geral]
```

---

## 10. ESTRUTURA DO PROJETO DJANGO

```
biblioteca_escolar/
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── .env.example
├── .env
├── requirements.txt
├── requirements-dev.txt
├── manage.py
├── pytest.ini
├── .gitignore
│
├── config/                          # Configurações do projeto Django
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py                  # Configurações comuns
│   │   ├── development.py           # Dev: DEBUG=True, SQLite opcional
│   │   └── production.py            # Prod: segurança, CORS, etc
│   ├── urls.py                      # URLs raiz
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   │
│   ├── accounts/                    # Usuários e autenticação
│   │   ├── migrations/
│   │   ├── templates/accounts/
│   │   │   ├── login.html
│   │   │   ├── dashboard_admin.html
│   │   │   ├── dashboard_biblioteca.html
│   │   │   ├── dashboard_professor.html
│   │   │   ├── dashboard_aluno.html
│   │   │   ├── aluno_list.html
│   │   │   ├── aluno_form.html
│   │   │   ├── professor_list.html
│   │   │   └── professor_form.html
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── models.py                # Usuario, PerfilAluno, PerfilProfessor, etc
│   │   ├── permissions.py           # Custom permissions
│   │   ├── serializers.py           # DRF Serializers
│   │   ├── signals.py               # Criar perfil ao criar usuário
│   │   ├── urls.py
│   │   ├── urls_admin.py
│   │   ├── urls_professor.py
│   │   ├── urls_aluno.py
│   │   └── views.py
│   │
│   ├── biblioteca/                  # Core da biblioteca
│   │   ├── migrations/
│   │   ├── templates/biblioteca/
│   │   │   ├── livro_list.html
│   │   │   ├── livro_detail.html
│   │   │   ├── livro_form.html
│   │   │   ├── emprestimo_list.html
│   │   │   ├── emprestimo_detail.html
│   │   │   ├── emprestimo_form.html
│   │   │   ├── emprestimo_turma_form.html
│   │   │   ├── turma_list.html
│   │   │   ├── turma_form.html
│   │   │   ├── relatorio_index.html
│   │   │   ├── estatisticas.html
│   │   │   ├── configuracoes.html
│   │   │   └── auditlog_list.html
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── models.py                # Livro, Exemplar, Emprestimo, etc
│   │   ├── permissions.py
│   │   ├── serializers.py
│   │   ├── services.py              # Lógica de negócio (registrar empréstimo, devolver, renovar)
│   │   ├── signals.py
│   │   ├── urls.py
│   │   └── views.py
│   │
│   ├── api/                         # API REST (DRF)
│   │   ├── v1/
│   │   │   ├── urls.py
│   │   │   └── views.py             # ViewSets da API
│   │   ├── authentication.py        # JWT setup
│   │   └── pagination.py
│   │
│   ├── notificacoes/                # E-mails e notificações
│   │   ├── templates/notificacoes/emails/
│   │   │   ├── confirmacao_emprestimo.html
│   │   │   ├── lembrete_vencimento.html
│   │   │   ├── atraso.html
│   │   │   ├── confirmacao_devolucao.html
│   │   │   └── confirmacao_renovacao.html
│   │   ├── apps.py
│   │   ├── models.py                # Notificacao
│   │   ├── services.py              # Funções de envio
│   │   └── tasks.py                 # Tasks Celery
│   │
│   └── relatorios/                  # Geração de PDF e Excel
│       ├── templates/relatorios/
│       │   ├── base_relatorio.html
│       │   ├── emprestimos_ativos.html
│       │   ├── emprestimos_atraso.html
│       │   ├── historico.html
│       │   ├── turmas.html
│       │   └── acervo.html
│       ├── apps.py
│       ├── generators_pdf.py        # WeasyPrint
│       ├── generators_excel.py      # openpyxl
│       └── views.py
│
├── static/
│   ├── css/
│   │   └── custom.css
│   ├── js/
│   │   └── app.js
│   └── img/
│
├── media/                           # uploads (capas, logos, fotos)
│
└── templates/
    ├── base.html                    # Template base com navbar e sidebar
    ├── base_auth.html               # Template para telas de autenticação
    └── components/
        ├── sidebar_admin.html
        ├── sidebar_biblioteca.html
        ├── sidebar_professor.html
        ├── sidebar_aluno.html
        ├── card_emprestimo.html
        ├── card_livro.html
        ├── alert.html
        └── pagination.html
```

---

## 11. CONFIGURAÇÃO DOCKER

### 11.1 Serviços

```yaml
# docker-compose.yml
version: '3.9'

services:
  db:
    image: postgres:16-alpine
    container_name: biblioteca_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: biblioteca_redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    container_name: biblioteca_web
    restart: unless-stopped
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    env_file:
      - .env
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    expose:
      - "8000"

  celery:
    build: .
    container_name: biblioteca_celery
    restart: unless-stopped
    command: celery -A config worker --loglevel=info --concurrency=2
    env_file:
      - .env
    depends_on:
      - redis
      - db
    volumes:
      - .:/app

  celery-beat:
    build: .
    container_name: biblioteca_celery_beat
    restart: unless-stopped
    command: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file:
      - .env
    depends_on:
      - redis
      - db
    volumes:
      - .:/app

  nginx:
    image: nginx:alpine
    container_name: biblioteca_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### 11.2 Dockerfile

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000
```

### 11.3 Variáveis de Ambiente (.env.example)

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados PostgreSQL
POSTGRES_DB=biblioteca_escolar
POSTGRES_USER=biblioteca_user
POSTGRES_PASSWORD=senha_segura_aqui
DATABASE_URL=postgresql://biblioteca_user:senha_segura_aqui@db:5432/biblioteca_escolar

# Redis
REDIS_URL=redis://redis:6379/0

# E-mail (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=escola@gmail.com
EMAIL_HOST_PASSWORD=senha_app_gmail
DEFAULT_FROM_EMAIL=Biblioteca Escolar <escola@gmail.com>

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Admin padrão
DJANGO_SUPERUSER_EMAIL=admin@escola.com.br
DJANGO_SUPERUSER_PASSWORD=adminsenha123
```

---

## 12. CONFIGURAÇÕES E PARÂMETROS DO SISTEMA

### 12.1 settings/base.py — pontos importantes

```python
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'django_celery_beat',
    'django_celery_results',
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_htmx',
    'solo',                          # django-solo (Configuracao singleton)
    # Projeto
    'apps.accounts',
    'apps.biblioteca',
    'apps.notificacoes',
    'apps.relatorios',
    'apps.api',
]

AUTH_USER_MODEL = 'accounts.Usuario'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Celery
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_BEAT_SCHEDULE = {
    'verificar-vencimentos-diario': {
        'task': 'apps.notificacoes.tasks.verificar_vencimentos',
        'schedule': crontab(hour=8, minute=0),
    },
}
```

---

## 13. TEMPLATES E COMPONENTES DE INTERFACE

### 13.1 Hierarquia de Templates

```
base.html
├── Navbar (logo + nome escola + usuário logado + logout)
├── Sidebar (dinâmica por tipo de usuário)
└── Content Block
    ├── Breadcrumb
    ├── Flash Messages
    └── Page Content

base_auth.html (login, reset senha)
└── Formulário centralizado
```

### 13.2 Paleta de Cores e Status

| Status | Cor | Classe Bootstrap |
|---|---|---|
| Disponível / OK | Verde | `text-success` / `badge bg-success` |
| Próximo do vencimento (≤3 dias) | Amarelo | `text-warning` / `badge bg-warning` |
| Atrasado | Vermelho | `text-danger` / `badge bg-danger` |
| Devolvido | Cinza | `text-secondary` / `badge bg-secondary` |
| Empréstimo de Turma | Azul | `text-primary` / `badge bg-primary` |

### 13.3 Componentes Principais

**Card de Empréstimo (para Aluno/Professor):**
- Capa do livro (thumbnail)
- Título e autor
- Data de devolução
- Badge de status
- Barra de progresso (dias restantes / total do prazo)
- Renovações: "X de Y utilizadas"
- Botão "Renovar" (desabilitado se não elegível, com tooltip explicativo)

**Dashboard de Estatísticas:**
- Cards de resumo (totais)
- Gráfico de linhas: empréstimos por mês (Chart.js via CDN)
- Gráfico de barras: Top 10 livros
- Gráfico de pizza: Distribuição por gênero
- Tabela: Top 5 turmas

---

## 14. TAREFAS AGENDADAS (CELERY)

```python
# apps/notificacoes/tasks.py

@shared_task
def verificar_vencimentos():
    """
    Executada diariamente às 08:00.
    Verifica todos os empréstimos ativos e envia notificações.
    """
    config = Configuracao.get_solo()
    hoje = date.today()
    emprestimos_ativos = Emprestimo.objects.filter(
        status__in=['ativo', 'atrasado', 'renovado']
    ).select_related('usuario', 'livro')
    
    for emprestimo in emprestimos_ativos:
        dias_para_vencer = (emprestimo.data_prevista_devolucao - hoje).days
        
        if dias_para_vencer in [3, 1, 0] and config.notif_lembrete_vencimento:
            enviar_lembrete_vencimento.delay(emprestimo.id, dias_para_vencer)
        
        elif dias_para_vencer < 0 and config.notif_atraso:
            dias_atraso = abs(dias_para_vencer)
            if dias_atraso <= config.max_dias_notificacao_atraso:
                # Verificar se já foi notificado hoje
                ja_notificado = Notificacao.objects.filter(
                    emprestimo=emprestimo,
                    tipo='atraso',
                    enviado_em__date=hoje
                ).exists()
                if not ja_notificado:
                    enviar_notificacao_atraso.delay(emprestimo.id, dias_atraso)
            
            # Atualizar status para 'atrasado'
            emprestimo.status = 'atrasado'
            emprestimo.save(update_fields=['status'])


@shared_task
def enviar_email_confirmacao_emprestimo(emprestimo_id):
    """Enviada imediatamente ao registrar empréstimo."""
    ...

@shared_task
def enviar_lembrete_vencimento(emprestimo_id, dias):
    """Enviada por verificar_vencimentos."""
    ...

@shared_task
def enviar_notificacao_atraso(emprestimo_id, dias_atraso):
    """Enviada por verificar_vencimentos."""
    ...

@shared_task
def enviar_email_devolucao(emprestimo_id):
    """Enviada ao registrar devolução."""
    ...

@shared_task
def enviar_email_renovacao(renovacao_id):
    """Enviada ao renovar empréstimo."""
    ...
```

---

## 15. SEGURANÇA

### 15.1 Permissões Customizadas (apps/*/permissions.py)

```python
class IsAdminGeral(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.tipo == 'admin_geral'

class IsAdminBiblioteca(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.tipo in [
            'admin_geral', 'admin_biblioteca'
        ]

class IsProprioUsuario(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.usuario == request.user

class CanRenovar(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            obj.usuario == request.user and
            obj.pode_renovar
        )
```

### 15.2 Middlewares e Proteções

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    # Custom: log de auditoria
    'apps.accounts.middleware.AuditLogMiddleware',
]

# Segurança em produção
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 16. CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1 — Setup e Fundação
- [ ] Criar projeto Django com estrutura de apps
- [ ] Configurar Docker Compose (web, db, redis, celery, nginx)
- [ ] Configurar `settings/base.py`, `development.py`, `production.py`
- [ ] Criar modelo `Usuario` customizado (AbstractUser)
- [ ] Criar perfis: PerfilAluno, PerfilProfessor, PerfilAdminBiblioteca
- [ ] Configurar autenticação por e-mail
- [ ] Criar template base + tela de login + dashboard por tipo de usuário
- [ ] Configurar Django Admin para todos os modelos

### Fase 2 — Acervo
- [ ] Modelos: Autor, Genero, Livro, Exemplar
- [ ] CRUD de livros (Admin Biblioteca)
- [ ] CRUD de autores e gêneros
- [ ] Upload de capa
- [ ] Busca e filtro de livros (catálogo)
- [ ] Busca por ISBN via Open Library API

### Fase 3 — Turmas e Usuários
- [ ] Modelo Turma + CRUD (Admin Geral)
- [ ] CRUD de Alunos (Admin Geral) com vínculo a turma
- [ ] CRUD de Professores (Admin Geral) com vínculo a turmas
- [ ] Importação CSV de alunos
- [ ] Modelo Configuracao (django-solo) + form de configurações

### Fase 4 — Empréstimos
- [ ] Modelo Emprestimo + lógica de criação (service)
- [ ] Modelo Exemplar com controle de status
- [ ] Validações: atraso, limite de livros, disponibilidade
- [ ] Registro de devolução
- [ ] Modelo Renovacao + endpoint de renovação online
- [ ] Modelo EmprestimoTurma + ItemEmprestimoTurma
- [ ] Formulário de empréstimo de turma (múltiplos livros)

### Fase 5 — Painéis de Usuário
- [ ] Painel do Aluno: lista de empréstimos com status visual
- [ ] Painel do Professor: empréstimos individuais + de turma
- [ ] Dashboard Admin: cards de resumo + gráficos (Chart.js)

### Fase 6 — Notificações
- [ ] Configurar Celery + Redis
- [ ] Task: verificar_vencimentos (agendamento diário)
- [ ] Templates de e-mail HTML para cada tipo
- [ ] Tasks de envio individual (async)
- [ ] Modelo Notificacao para registro de envios

### Fase 7 — Relatórios
- [ ] Configurar WeasyPrint
- [ ] Configurar openpyxl
- [ ] Templates HTML de relatórios (com logo e cabeçalho da escola)
- [ ] Gerador PDF para cada tipo de relatório
- [ ] Gerador Excel para cada tipo de relatório
- [ ] Filtros de período nos relatórios

### Fase 8 — API REST
- [ ] Configurar DRF + JWT
- [ ] Serializers para todos os modelos
- [ ] ViewSets com permissões corretas
- [ ] Endpoints de autenticação
- [ ] Paginação e filtros
- [ ] Documentação automática (drf-spectacular / Swagger)

### Fase 9 — Segurança e Auditoria
- [ ] Permissões customizadas por tipo de usuário
- [ ] Middleware de audit log
- [ ] Tela de logs para Admin Geral
- [ ] Rate limiting no login
- [ ] Testes unitários (mínimo 70% cobertura)

### Fase 10 — Deploy e Finalização
- [ ] Configurar Nginx
- [ ] Script de criação do superusuário inicial
- [ ] Documentação de instalação (README.md)
- [ ] Backup automático do banco de dados

---

## DEPENDÊNCIAS PYTHON (requirements.txt)

```txt
Django==5.1.*
djangorestframework==3.15.*
djangorestframework-simplejwt==5.3.*
psycopg2-binary==2.9.*
redis==5.0.*
celery==5.3.*
django-celery-beat==2.6.*
django-celery-results==2.5.*
django-cors-headers==4.3.*
django-crispy-forms==2.3.*
crispy-bootstrap5==2024.*
django-htmx==1.19.*
django-solo==2.3.*
WeasyPrint==62.*
openpyxl==3.1.*
Pillow==10.*
gunicorn==22.*
python-decouple==3.8.*
drf-spectacular==0.27.*
requests==2.31.*            # para busca de ISBN na Open Library
```

---

*Documento gerado para o projeto BibliotecaEscolar — Versão 1.0*  
*Para uso com Claude CLI / Claude Code na geração automática do sistema completo.*
