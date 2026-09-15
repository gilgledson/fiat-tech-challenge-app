# Documentação de Arquitetura — Fase 3

Índice da documentação arquitetural exigida pela Fase 3 do Tech Challenge.

## Diagramas

| Diagrama | Descrição |
|---|---|
| [Diagrama de Componentes](diagrama-componentes.png) ([fonte .mmd](diagrama-componentes.mmd)) | Visão de nuvem completa: API Gateway, cluster AKS, Function Serverless, banco gerenciado, storage, observabilidade e CI/CD |
| [Diagrama de Sequência — Autenticação por CPF](diagrama-sequencia-autenticacao-cpf.png) ([fonte .mmd](diagrama-sequencia-autenticacao-cpf.mmd)) | Fluxo completo: Function valida CPF → consulta Postgres → emite JWT → API valida o token |
| [Diagrama de Sequência — Abertura de Ordem de Serviço](diagrama-sequencia-abertura-os.png) ([fonte .mmd](diagrama-sequencia-abertura-os.mmd)) | Fluxo de negócio: validação de cliente/veículo, persistência da OS, evento assíncrono de notificação |
| [Diagrama ER (DER)](der-oficina-api.png) ([fonte .mmd](der-oficina-api.mmd)) | Modelo relacional completo: 11 tabelas, 14 relacionamentos, levantado diretamente das migrations Flyway |

## RFCs (Request for Comments) — decisões técnicas

| RFC | Decisão |
|---|---|
| [RFC-001](rfc-001-escolha-da-nuvem.md) | Escolha do provedor de nuvem (Azure) |
| [RFC-002](rfc-002-escolha-do-banco-de-dados.md) | Escolha do banco de dados (PostgreSQL / Azure Flexible Server) |
| [RFC-003](rfc-003-estrategia-de-autenticacao.md) | Estratégia de autenticação (dois modos de login + JWT compartilhado) |

## ADRs (Architecture Decision Records) — decisões arquiteturais permanentes

| ADR | Decisão |
|---|---|
| [ADR-001](adr-001-padrao-de-comunicacao.md) | Padrão de comunicação: REST síncrono + Event Bus interno assíncrono |
| [ADR-002](adr-002-uso-de-hpa.md) | Uso de HorizontalPodAutoscaler (HPA) |
| [ADR-003](adr-003-function-app-service-plan.md) | Plano de hospedagem da Function (Consumption Plan) |
| [ADR-004](adr-004-jwt-compartilhado-entre-servicos.md) | Chave JWT compartilhada entre API e Function |

## Banco de dados

[Justificativa formal da escolha do banco de dados](justificativa-banco-de-dados.md)
— complementa o RFC-002 com o detalhamento do modelo relacional real
(relacionamentos, padrão de soft delete, e achados de auditoria do schema).

## Diagramas anteriores (Fase 2)

A [Fase 2](../diagrama-arquitetura-infraestrutura.mmd) já tinha um diagrama
de infraestrutura (CI/CD → Docker Hub → AKS, Terraform → RG/AKS/DB/Storage) e
um [diagrama de comunicação entre módulos](../diagrama-de-comunicação-entre-modulos.mmd)
do monólito. O [Diagrama de Componentes](diagrama-componentes.mmd) desta
pasta os estende com as peças da Fase 3 (Gateway, Function, observabilidade).
