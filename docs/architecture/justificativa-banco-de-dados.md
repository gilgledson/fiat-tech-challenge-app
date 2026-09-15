# Justificativa da escolha do banco de dados e do modelo relacional

Este documento complementa o [RFC-002](rfc-002-escolha-do-banco-de-dados.md)
(por que PostgreSQL) com o detalhamento do **modelo relacional real** —
levantado diretamente das 21 migrations Flyway
(`src/main/resources/db/migration/*.sql`) e das classes de mapeamento JPA
(`*JpaEntity.java`), não de um desenho teórico. Ver o diagrama completo em
[`der-oficina-api.mmd`](der-oficina-api.mmd) /
[`der-oficina-api.png`](der-oficina-api.png).

## Visão geral: 11 tabelas + 2 views de relatório

| Tabela | Papel no domínio |
|---|---|
| `usuario` | Credenciais de acesso (login por e-mail/senha) e perfil de autorização |
| `cliente` | Cadastro de clientes da oficina, com CPF/CNPJ único |
| `veiculo` | Veículos de um cliente |
| `funcionarios` | Equipe interna (mecânico, atendente, administrador) |
| `servico` | Catálogo de serviços oferecidos (preventivo/corretivo) |
| `produto` | Catálogo de peças/produtos, com controle de estoque físico e reservado |
| `servico_produto_sugerido` | Associação N:N — quais produtos costumam ser usados em cada serviço |
| `ordem_de_servico` | A entidade central do domínio — uma OS por veículo/cliente |
| `ordem_de_servico_servicos` | Serviços efetivamente incluídos em uma OS (com seu próprio ciclo de status) |
| `ordem_de_servico_produtos` | Produtos efetivamente consumidos em uma OS |
| `orcamento` | Orçamento/fatura gerado a partir de uma OS finalizada (1:1) |

Views: `vw_relatorio_esforco_os` e `vw_relatorio_tempo_medio_servico`,
mapeadas como entidades JPA `@Immutable` (só leitura), usadas pelos
endpoints `GET /api/relatorios/*`.

## Relacionamentos e por que cada um existe

- **`cliente` → `veiculo` (1:N obrigatório)**: um cliente pode ter vários
  veículos; todo veículo precisa de um cliente (`cliente_id NOT NULL`).
- **`cliente` + `veiculo` → `ordem_de_servico` (1:N obrigatório em ambos)**:
  toda OS nasce vinculada a um cliente **e** a um veículo específico
  daquele cliente — a validação de que o veículo pertence ao cliente é
  feita na camada de aplicação (`AbrirOrdemDeServicoUseCaseImpl`), não por
  uma constraint composta no banco (ver seção de limitações abaixo).
- **`usuario` → `cliente` (0..1:1, opcional)**: um cliente *pode* ter uma
  conta de usuário vinculada (para login por e-mail/senha), mas não
  precisa — desde a Fase 3, um cliente pode se autenticar só pelo CPF
  (ver [RFC-003](rfc-003-estrategia-de-autenticacao.md)) sem nunca ter um
  `Usuario`. Essa nullability já existia no schema antes da Fase 3 e se
  tornou ainda mais relevante agora.
- **`usuario` → `funcionarios` (0..1:1, opcional no schema)**: mesma ideia,
  para a equipe interna.
- **`ordem_de_servico` → `ordem_de_servico_servicos` /
  `ordem_de_servico_produtos` (1:N)**: uma OS agrega múltiplos itens de
  serviço e produto, cada um com seu próprio valor e (no caso dos
  serviços) seu próprio ciclo de status independente do status geral da
  OS — é o que permite, por exemplo, que um serviço específico dentro de
  uma OS `EM_EXECUCAO` já esteja `FINALIZADO` enquanto outro ainda está
  `PENDENTE`.
- **`ordem_de_servico_produtos` → `ordem_de_servico_servicos` (N:1
  opcional)**: uma peça consumida pode estar associada a um serviço
  específico da OS (`os_servico_id`), ou a nenhum (produto avulso) —
  campo nullable de propósito.
- **`servico` ↔ `produto` via `servico_produto_sugerido` (N:N)**: catálogo
  de sugestão ("ao vender este serviço, sugira estas peças") — desacoplado
  do consumo real (`ordem_de_servico_produtos`), que é o que efetivamente
  baixa estoque.
- **`ordem_de_servico` → `orcamento` (1:1, `ordem_servico_id UNIQUE`)**:
  cada OS gera no máximo um orçamento — o `UNIQUE` na FK é o que garante
  essa cardinalidade no banco, não só na aplicação.
- **`usuario` → `ordem_de_servico_servicos.usuario_executor_id` (0..N,
  opcional)**: registra qual mecânico executou cada item de serviço, para
  fins de auditoria/relatório — nullable porque nem todo item
  necessariamente tem executor registrado (ex.: ainda não iniciado).

## Por que soft delete nas entidades "cadastrais"

`produto`, `servico`, `cliente`, `veiculo`, `ordem_de_servico` e
`funcionarios` usam `deletado_em TIMESTAMP NULL` em vez de `DELETE` físico.
Motivo direto do domínio: **uma OS antiga não pode perder a referência ao
cliente/veículo/serviço/produto que ela usou**, mesmo que esse cadastro
tenha sido "removido" depois — apagar fisicamente um `cliente` referenciado
por uma `ordem_de_servico` quebraria a FK (ou exigiria `ON DELETE CASCADE`,
apagando o histórico de OS junto, o que seria pior). Soft delete preserva
integridade referencial e histórico ao mesmo tempo.

`usuario` e `orcamento` **não têm** soft delete — usuário aparenta ser
gerenciado só pelo campo `ativo` (não removido), e orçamento não tem
mecanismo de remoção lógica nenhum documentado nas migrations (provável
tratamento como registro imutável, uma vez emitido).

## Achados da auditoria de schema (pontos de atenção, não bloqueantes)

Levantados durante a produção desta documentação, comparando migrations
(schema real) com o código Java (`*JpaEntity`, enums de domínio):

1. **`orcamento.status` é o único campo de estado sem `CHECK` constraint no
   banco.** Todos os outros 7 campos de status/categoria do domínio
   (`usuario.perfil`, `funcionarios.cargo`, `servico.tipo`,
   `produto.unidade_medida`, `ordem_de_servico.status`,
   `ordem_de_servico_servicos.status`, `orcamento.metodo_pagamento`) têm
   `CHECK` redundante com o enum Java (`StatusOrcamento`). `orcamento.status`
   depende só de `@Enumerated(EnumType.STRING)` no Hibernate — um `UPDATE`
   direto no banco (fora da aplicação) poderia gravar um valor fora do
   enum. **Recomendação para uma próxima iteração**: adicionar
   `CHECK (status IN ('PENDENTE','PAGO','CANCELADA'))` numa nova migration.
2. **`ordem_de_servico.status` tem 13 valores permitidos no `CHECK`, mas o
   enum Java `OrdemDeServicoStatus` só usa 10.** `ORCAMENTO`, `REPROVADA` e
   `FINALIZADA` são resquícios de uma versão anterior do fluxo de status —
   não representam risco de dado inválido (o Java nunca vai escrever esses
   valores), mas deixam o `CHECK` mais permissivo do que o domínio atual
   exige. Não corrigido nesta fase para não arriscar quebrar dados
   históricos que porventura ainda usem esses valores.
3. **Duas discrepâncias de tipo Java vs SQL em colunas de quantidade**:
   `ordem_de_servico_servicos.quantidade` é `DECIMAL(10,2)` no banco mas
   `int` no Java (risco teórico de truncar um valor fracionário que nunca
   deveria existir para "quantidade de serviço", então baixo risco prático);
   `ordem_de_servico_produtos.quantidade` é `INTEGER` no banco mas
   `BigDecimal` no Java (mais largo no Java que no banco, sem risco de
   perda). Nenhuma das duas causou bug observado, mas ambas valem
   alinhamento numa limpeza futura de schema.
4. **`funcionarios.usuario_id`** é `nullable` no schema SQL (só `UNIQUE`,
   sem `NOT NULL`), mas a `FuncionarioJpaEntity` declara
   `@Column(nullable = false)` — a aplicação é mais restritiva que o banco
   permite. Não é um bug ativo (a aplicação sempre preenche o campo), mas
   documenta uma divergência de contrato entre as duas camadas.
5. **Não há constraint composta impedindo uma `ordem_de_servico` referenciar
   um `veiculo` que não pertence ao `cliente` informado** — essa regra é
   validada só em `AbrirOrdemDeServicoUseCaseImpl` (camada de aplicação).
   Tecnicamente possível de violar via SQL direto; seria necessário um
   `CHECK` ou trigger para blindar isso no banco, o que não foi feito por
   ser uma validação relacional entre três tabelas (mais natural na
   aplicação do que em SQL puro).

Nenhum desses pontos compromete o funcionamento atual do sistema — estão
documentados aqui porque uma "justificativa formal" honesta inclui também
os limites conhecidos do modelo, não só os acertos.
