# RFC-001 — Escolha do provedor de nuvem

- **Status**: Aceito
- **Data**: 2026-09 (Fase 2, mantido na Fase 3)
- **Autores**: Equipe Oficina API

## Contexto

A partir da Fase 2 o projeto precisou sair do ambiente local (Docker Compose)
para uma infraestrutura real de nuvem, com banco de dados gerenciado, cluster
Kubernetes com escalabilidade e, na Fase 3, também Function Serverless, API
Gateway e observabilidade gerenciada. O enunciado do desafio dá liberdade de
escolha de provedor ("livre escolha de nuvem").

## Alternativas consideradas

| Critério | AWS | Azure | GCP |
|---|---|---|---|
| Kubernetes gerenciado | EKS | AKS | GKE |
| Postgres gerenciado | RDS | Azure Database for PostgreSQL Flexible Server | Cloud SQL |
| Function Serverless | Lambda | Azure Functions | Cloud Functions |
| Créditos/free tier disponíveis para o time | Limitado | Assinatura de estudante disponível | Limitado |
| Familiaridade prévia do time | Baixa | Já usada na Fase 2 | Baixa |

Todos os três provedores atendem tecnicamente aos requisitos obrigatórios
(API Gateway, Function Serverless, banco gerenciado, cluster Kubernetes,
Terraform). A decisão não foi motivada por uma limitação técnica de nenhum
concorrente, mas por custo/acesso e continuidade com o que já estava em
produção desde a Fase 2.

## Decisão

Manter **Microsoft Azure** como provedor único, com os seguintes serviços:

- **AKS** (Azure Kubernetes Service) — cluster Kubernetes de produção.
- **Azure Database for PostgreSQL Flexible Server** — banco gerenciado
  (ver [RFC-002](rfc-002-escolha-do-banco-de-dados.md)).
- **Azure Functions** (plano Consumption) — Function Serverless de
  autenticação por CPF.
- **Azure Blob Storage** — armazenamento das assinaturas de aceite de
  orçamento.
- **Terraform** (`provider "azurerm"`) — todo o provisionamento como
  código, em `infra/`.

A região escolhida é **Brazil South**, por latência (usuários/avaliadores no
Brasil) e por ser a região mais completa disponível na assinatura usada.

## Consequências

- **Positivo**: um único provedor simplifica autenticação (uma única
  `az login`), cobrança e o Terraform (`provider "azurerm"` único, sem
  módulos cross-cloud). Continuidade direta com a infraestrutura já validada
  na Fase 2 (AKS + Postgres + Storage já existiam antes da Fase 3).
- **Positivo**: o time já havia resolvido, na Fase 2, problemas comuns de
  Azure (nome de Storage Account globalmente único, HPA em AKS, firewall do
  Postgres) — esse conhecimento foi reaproveitado.
- **Negativo**: a Function Serverless da Fase 3 ficou no mesmo provedor da
  aplicação principal, quando o enunciado cita "Lambda" (AWS) como exemplo
  — usamos Azure Functions como equivalente funcional, documentado
  explicitamente no [RFC-003](rfc-003-estrategia-de-autenticacao.md).
- **Negativo**: dependência de uma única conta/assinatura Azure — se ela for
  suspensa ou os limites de cota mudarem (como aconteceu com a cota de
  Consumption Plan durante o desenvolvimento, ver
  [ADR-003](adr-003-function-app-service-plan.md)), não há fallback
  imediato em outro provedor.
