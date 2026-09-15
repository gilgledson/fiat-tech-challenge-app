# RFC-002 — Escolha do banco de dados

- **Status**: Aceito
- **Data**: 2026-09 (Fase 2, mantido e justificado formalmente na Fase 3)
- **Autores**: Equipe Oficina API

## Contexto

O domínio da Oficina API é fortemente **relacional e transacional**: uma
Ordem de Serviço referencia Cliente, Veículo, múltiplos Serviços e Produtos
(com controle de estoque físico vs. reservado), e um Orçamento em relação
1:1 com a OS. Há regras de integridade que precisam ser garantidas de forma
consistente (ex.: `quantidade_estoque_reservado <= quantidade_estoque_fisico`,
enums de status validados via `CHECK`, chaves estrangeiras entre praticamente
todas as tabelas). O enunciado da Fase 3 pede explicitamente um banco
gerenciado e uma "justificativa formal" para a escolha.

## Alternativas consideradas

| Opção | Prós | Contras para este domínio |
|---|---|---|
| **PostgreSQL** (escolhida) | Relacional, `CHECK` constraints nativos, `EXTRACT(EPOCH ...)` e views para os relatórios, tipos `DECIMAL` precisos para valores monetários/estoque, gratuito/open-source, gerenciado nativamente na Azure (Flexible Server) | — |
| MySQL | Relacional, também gerenciado na Azure | Suporte mais fraco a `CHECK` constraints em versões mais antigas, menos expressivo em funções de data/hora usadas nos relatórios |
| SQL Server | Relacional, gerenciado na Azure, integração nativa com o ecossistema Microsoft | Licenciamento mais caro em produção, sem vantagem técnica relevante sobre Postgres para este domínio |
| Banco NoSQL (ex.: Cosmos DB / MongoDB) | Escalabilidade horizontal facilitada | Domínio tem **11 tabelas fortemente relacionadas por FK** (ver `docs/architecture/der-oficina-api.mmd`) e regras de integridade referencial/CHECK — modelar isso em documentos exigiria desnormalização manual e reimplementar na aplicação garantias que o banco relacional já oferece de graça (ex.: um Orçamento não pode existir sem uma Ordem de Serviço válida) |

## Decisão

Manter **PostgreSQL**, provisionado como **Azure Database for PostgreSQL
Flexible Server** (SKU `B_Standard_B1ms`, versão 13), gerenciado via
Terraform em [`infra/database.tf`](https://github.com/SEU_USUARIO/oficina-infra-banco-dados/blob/main/infra/database.tf)
(repositório `oficina-infra-banco-dados`).

Motivos técnicos concretos, com base no schema real (ver
[`der-oficina-api.mmd`](der-oficina-api.mmd) e
[`justificativa-banco-de-dados.md`](justificativa-banco-de-dados.md)):

1. **Integridade referencial nativa**: 14 foreign keys conectam as 11
   tabelas do domínio (ex.: `ordem_de_servico_servicos.ordem_de_servico_id`
   → `ordem_de_servico.id`). Um banco relacional impede, por construção,
   uma OS "órfã" sem cliente/veículo válido.
2. **`CHECK` constraints para os enums de estado**: 7 dos 9 campos de
   estado do domínio (perfil de usuário, cargo, tipo de serviço, unidade de
   medida, status de OS, status de item de OS, método de pagamento) têm
   `CHECK` no próprio banco, redundante com o enum Java — proteção mesmo
   contra escrita fora da aplicação (migração manual, outro serviço, etc.).
3. **Tipos numéricos exatos**: `DECIMAL(10,2)` para preços, estoque e
   valores de orçamento evita os erros de arredondamento de `FLOAT`/`DOUBLE`
   em cálculos financeiros.
4. **Suporte a views materializadas por consulta** (não persistidas, mas
   computadas): `vw_relatorio_esforco_os` e `vw_relatorio_tempo_medio_servico`
   usam `EXTRACT(EPOCH FROM (data_fim - data_inicio))` para calcular
   duração — função nativa do Postgres, mapeada como `@Entity @Immutable`
   no Hibernate, sem precisar de código de agregação na aplicação.
5. **Flyway** (já em uso desde a Fase 2) tem suporte de primeira classe a
   Postgres, com histórico de 21 migrations aplicadas de forma incremental
   e reprodutível.
6. **Managed service equivalente** disponível na Azure (Flexible Server),
   com backup automático, patching gerenciado e firewall configurável —
   sem precisar operar o banco manualmente.

## Consequências

- **Positivo**: todas as regras de integridade estrutural (FKs, enums,
  1:1 entre Orçamento e OS) são garantidas pelo próprio SGBD, reduzindo a
  superfície de bugs de consistência na aplicação.
- **Positivo**: `DECIMAL` em todos os campos monetários/estoque evita uma
  classe inteira de bugs de arredondamento.
- **Negativo conhecido** (registrado durante a auditoria de schema para
  esta RFC): `orcamento.status` é o único campo de estado **sem** `CHECK`
  constraint no banco — depende só da validação Java
  (`@Enumerated(EnumType.STRING)`). Ver
  [`justificativa-banco-de-dados.md`](justificativa-banco-de-dados.md) para
  o detalhe e a recomendação de correção futura.
- **Negativo**: escala verticalmente (SKU `B_Standard_B1ms`, baixo custo) —
  se o volume de OS crescer muito, será necessário migrar para um SKU maior
  ou considerar read-replicas; não há sharding nativo como em soluções
  NoSQL, mas o volume atual do domínio não justifica essa complexidade.
