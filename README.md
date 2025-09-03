# TireInspect (PneuCheck)

Sistema web para inspeção de pneus de caminhões. Permite cadastrar empresas e caminhões, registrar inspeções (com dados por pneu) e gerar relatórios em PDF — individuais ou combinados por período.

## Visão Geral

- Objetivo: centralizar e padronizar inspeções de pneus por veículo, tornando simples acompanhar medidas, estado e histórico.
- Apps/Domínios:
  - `core`: modelos, formulários, views e templates (login, dashboard, CRUDs, inspeções).
  - `reports`: geração de PDFs (individual e lote com índice).
  - `inspection_reports`: filtro por intervalo de meses e listagem com ações de exportação.
- Autenticação: usuários Django; cada empresa tem um dono (`Company.created_by`), e os dados são sempre filtrados pelo usuário logado.

## Stack

- Django 5.x (Auth, templates), Crispy Forms + Tailwind (CDN) para UI.
- ReportLab para renderizar PDF e PyPDF2 para mesclar documentos.
- WhiteNoise para servir estáticos em produção.
- Banco por padrão: SQLite (configuração para Postgres via `dj-database-url` pronta).

## Estrutura do Projeto

- `tireinspect/`: settings, urls e WSGI/ASGI.
- `core/`: modelos, formulários, views e templates principais (login, home, CRUDs, inspeções).
- `reports/`: views e utilitários de PDF (individual e em lote com índice).
- `inspection_reports/`: filtro por período e listagem com seleção para PDF em lote.
- `static/`: imagens (logo e diagramas de pneus por configuração).
- `staticfiles/`: saída de coletados (produção).

## Modelos (core/models.py)

- Company: nome, CNPJ, contato, `created_by` (usuário dono).
- TruckType: catálogo de configurações (código, descrição, `axle_count`, `tire_count`). Inicializado por migração com 8 tipos comuns.
- Truck: placa, tipo (`TruckType`), empresa, marca/modelo, hodômetro.
- Inspection: data, hodômetro, observações; pertence a um caminhão.
- Tire: pertence a uma inspeção; posição sequencial (1..N), 3 sulcos (D, M, F), marca, desenho, nº fogo, DOT, `rec` (recapado).

Migrações relevantes:
- `0005_trucktype_initial_data`: popula `TruckType`.
- `0009_*`: remove `groove_4` e renomeia os rótulos dos sulcos para D/M/F.

## Fluxos Principais

Autenticação e entrada
- `/` redireciona para login ou `core:home` se autenticado.
- Telas de Login e Cadastro (`core:login`, `core:register`).

Empresas
- Listagem: `core:company_list` (filtrada por `created_by`).
- Criação: `core:company_create` (grava `created_by`).
- Exclusão: `core:company_delete` (POST, só do dono).

Caminhões
- Por empresa: `core:truck_list` e `core:truck_create`.
- Placa única por empresa (`unique_ + validação na view).

Inspeções
- Listar: `core:inspection_list` (por caminhão).
- Criar/Editar: `core:inspection_create` / `core:inspection_edit`, com `inlineformset_factory` para pneus.
- Detalhar: `core:inspection_detail` (tabela de pneus, link para PDF).
- Excluir: `core:inspection_delete` (POST).

## Lógica de Posição dos Pneus

Função `core.views.gerar_posicoes_personalizadas(axles, tires)` gera labels humanos e ordenados para exibição:
- Primeiro lado esquerdo (E): `1E, 2E, ...`; onde houver “rodado duplo”, substitui por `ED/EF` do eixo mais alto para baixo.
- Depois lado direito (D): `1D, 2D, ...` com `DD/DF` análogo.
- Sempre retorna exatamente `tire_count` labels.

Uso:
- Durante criação/edição, cada formulário do formset recebe `position_label` (p. ex., `3ED`) apenas para exibir. A posição persistida é sequencial 1..N.
- Exibição de sulcos considera o lado: E mostra F–M–D; D mostra D–M–F.

## Formulários e Formsets

- InspectionForm: dados gerais da inspeção.
- TireForm: inclui campo `rec` como escolha (Sim/Não) com `RadioSelect` e conversão para boolean em `clean_rec`.
- TireFormSet: `inlineformset_factory(Inspection, Tire)`; na criação, `extra` = `tire_count` do caminhão; na edição, `extra=0`.

## Relatórios (PDF)

PDF individual
- Rota: `reports:inspection_pdf` (verifica posse: a inspeção deve pertencer a empresa do usuário).
- Geração: `reports/utils.py::gerar_inspecao_pdf` desenha cabeçalho, dados, tabela de pneus (com coloração para “Novo/Recapado”) e diagrama por tipo (`static/img/ca-<axles>eixos_<tires>pneus.png`).

PDF em lote com índice (bulk)
- Tela: `inspection_reports:report_by_month` (`/relatorios/intervalo/meses/`), filtro “Mês inicial/final” (MM/AAAA) e empresa (opcional), tudo restrito ao usuário logado.
- Ações: seleção das inspeções listadas e geração de um único PDF via POST JSON para `reports:bulk_inspection_pdf`.
- Geração: `gerar_indice_pdf` produz capa/índice estilizado; `gerar_inspecoes_bulk_pdf` concatena índice + PDFs individuais com PyPDF2.

## Permissões e Segurança

- Escopo por usuário: todas as consultas filtram por `created_by` via relacionamentos.
- CSRF: formulários Django e chamadas `fetch` enviam `X-CSRFToken` (lido do cookie `csrftoken`).
- Admin: `core/admin.py` registra os modelos para gestão interna.

## Como Rodar Localmente

Pré-requisitos
- Python 3.11+ e virtualenv.

Instalação
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ambiente
- Crie `.env.local` na raiz:
```
SECRET_KEY=uma_chave_segura
DEBUG=True
```
- Para produção, use `.env` (e configure `ALLOWED_HOStogether`TS` e `DATABASE_URL`).

Banco de dados
```bash
python manage.py migrate
python manage.py createsuperuser  # opcional
```

Executar
```bash
python manage.py runserver
# http://localhost:8000/
```

Estáticos (produção)
```bash
python manage.py collectstatic
```
WhiteNoise serve de `STATIC_ROOT` conforme settings.

## URLs Principais

- `admin/` — painel administrativo Django.
- `accounts/login/` e `login/` — autenticação.
- `home/` — dashboard.
- `empresas/`, `empresa/nova/` — empresas (listagem e criação).
- `empresa/<id>/caminhoes/`, `empresa/<id>/caminhao/novo/` — caminhões.
- `caminhao/<id>/inspecoes/`, `caminhao/<id>/inspecao/nova/` — inspeções por caminhão.
- `inspecao/<id>/`, `inspecao/<id>/editar/`, `inspecao/<id>/delete/` — detalhe/edição/exclusão de inspeção.
- `reports/inspecao/<id>/pdf/` — PDF individual (há rota duplicada `inspection/<id>/pdf/`).
- `relatorios/intervalo/meses/` — filtro por meses, seleção e PDF em lote.

## Templates-Chave

- `core/templates/core/base.html`: layout base com Tailwind (CDN) e tema (`primary`/`secondary`).
- `core/templates/core/*`: login, home, listagens, formulários (Crispy Forms com classes utilitárias).
- `core/templates/core/inspection_detail.html`: tabela de pneus com regra de sulcos por lado e link “Gerar PDF”.

## Observações e Melhorias

- `rec` (modelo) está rotulado como “Novo” no formulário; alinhar nomenclatura (exibir “Recapado” ou “Novo” conforme regra do negócio).
- `reports/urls.py` tem duas rotas para o mesmo PDF; manter apenas uma canônica.
- `LANGUAGE_CODE`/`TIME_ZONE` aparecem duplicados em settings; consolidar.
- Alguns SVGs em `inspection_detail` têm `path` truncado; substituir por path completo se ícones não aparecerem.
- `requirements.txt` inclui Flask, não utilizado no Django; considerar remover se não houver uso futuro.
- Para Postgres em produção, descomentar bloco `dj-database-url` no settings e definir `DATABASE_URL`.

## Roadmap (sugestões)

- Exportação CSV por período.
- Upload de fotos e observações por pneu.
- Regras de validação das medidas (limites por posição/eixo).
- Times e compartilhamento por empresa (multiusuário com permissões).