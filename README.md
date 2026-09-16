![Coverage](.github/badges/jacoco.svg)

# 🔧 Oficina API — Aplicação Principal

> API RESTful para gestão de uma **Oficina Mecânica**, desenvolvida como parte
> do **Tech Challenge da FIAP**, aplicando **Domain-Driven Design (DDD)** e
> **Clean Architecture**. Este é o repositório da **aplicação principal**,
> um dos 4 repositórios do Tech Challenge Fase 3 — ver os outros:

- [oficina-infra-kubernetes](https://github.com/gilgledson/fiat-tech-challenge-infra-kubernetes) — Terraform do cluster AKS + API Gateway (Traefik)
- [oficina-infra-banco-dados](https://github.com/gilgledson/fiat-tech-challenge-infra-database) — Terraform do Postgres gerenciado
- [oficina-lambda-auth-cpf](https://github.com/gilgledson/fiat-tech-challenge-lambda-auth-cpf) — Function Serverless de autenticação por CPF

---

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Arquitetura](#-arquitetura)
- [Documentação de Arquitetura (Fase 3)](#-documentação-de-arquitetura-fase-3)
- [Módulos](#-módulos)
- [Tecnologias](#-tecnologias)
- [Banco de Dados](#-banco-de-dados)
- [Como Executar (local)](#-como-executar-local)
- [Deploy](#-deploy)
- [Endpoints](#-endpoints)
- [Testes](#-testes)
- [Observabilidade (New Relic)](#-observabilidade-new-relic)

---

## 🚀 Sobre o Projeto

A **Oficina API** é um sistema backend para gerenciamento completo de uma
oficina mecânica, cobrindo desde o catálogo de produtos e serviços até o
controle de clientes, veículos e ordens de serviço — do orçamento à entrega
do veículo.

Desenvolvido com **Quarkus**, o framework Java nativo em nuvem, com foco em
alta performance e arquitetura limpa.

Na Fase 3, a aplicação passou a rodar atrás de um **API Gateway** (Traefik,
provisionado pelo repositório `oficina-infra-kubernetes`), com um segundo
modo de autenticação **por CPF** (via Function Serverless, repositório
`oficina-lambda-auth-cpf`), observabilidade completa (New Relic) e
documentação arquitetural formal.

---

## 🏛️ Arquitetura

Clean Architecture + DDD, organizada por módulos de domínio (não por
camada técnica): `identidade`, `atendimento` (cliente/veículo), `catalogo`
(produto/serviço), `operacional` (ordem de serviço/funcionário),
`orcamento`, `relatorios`, `notificacao`. Cada módulo segue:

```
api/            → controllers REST, DTOs (adapter de entrada)
application/    → usecases (portas de entrada), interfaces de repositório (portas de saída)
domain/         → entidades e value objects puros, sem dependência de framework
infrastructure/ → implementações Panache/JPA, beans CDI, segurança
```

## 📐 Documentação de Arquitetura (Fase 3)

Toda a documentação arquitetural formal está em
[`docs/architecture/`](docs/architecture) — índice completo em
[`docs/architecture/README.md`](docs/architecture/README.md):

- **Diagrama de Componentes** — visão completa de nuvem, API Gateway,
  Function Serverless, banco, storage e observabilidade.
- **Diagramas de Sequência** — autenticação por CPF, abertura de ordem de
  serviço.
- **RFCs** — escolha da nuvem, do banco de dados, estratégia de
  autenticação.
- **ADRs** — padrão de comunicação, uso de HPA, plano da Function, JWT
  compartilhado entre serviços.
- **Diagrama ER (DER) + justificativa formal do banco de dados** — modelo
  relacional completo, levantado diretamente das migrations.

---

## 📦 Módulos

| Módulo | Responsabilidade |
|---|---|
| `identidade` | Login (e-mail/senha), usuários, perfis |
| `atendimento` | Clientes, veículos |
| `catalogo` | Produtos (estoque), serviços |
| `operacional` | Ordens de serviço, funcionários |
| `orcamento` | Aceite, pagamento e PDF do orçamento |
| `relatorios` | Relatórios de esforço e tempo médio |
| `notificacao` | Notificação assíncrona ao cliente (Event Bus interno) |

---

## ⚙️ Tecnologias

- **Quarkus 3.15** (Java 17) — REST, Hibernate ORM + Panache, Flyway, SmallRye JWT/Health/OpenAPI
- **PostgreSQL** — banco relacional (ver [justificativa](docs/architecture/justificativa-banco-de-dados.md))
- **New Relic Java Agent** — APM (embutido na imagem Docker)
- **Docker** (`eclipse-temurin:17-jre`) + **Kubernetes** (AKS)
- **JaCoCo** — cobertura de testes (gate 80%)
- **Newman/Postman** — testes de integração E2E

---

## 🗄️ Banco de Dados

Provisionado pelo repositório
[`oficina-infra-banco-dados`](https://github.com/gilgledson/fiat-tech-challenge-infra-database)
(Terraform, PostgreSQL Flexible Server). Migrations Flyway em
[`src/main/resources/db/migration/`](src/main/resources/db/migration).
Modelo relacional completo (11 tabelas, 14 relacionamentos) documentado em
[`docs/architecture/der-oficina-api.png`](docs/architecture/der-oficina-api.png).

---

## ▶️ Como Executar (local)

```bash
docker compose up -d
```

Sobe Postgres local + a aplicação (build da própria imagem,
`STORAGE_TYPE=local`). API disponível em `http://localhost:8383`, Swagger
UI em `http://localhost:8383/q/swagger-ui/`.

Para testar contra Azure Blob Storage localmente, defina `STORAGE_TYPE=azure`
e `AZURE_STORAGE_CONNECTION_STRING`.

---

## 🚀 Deploy

Este repositório assume que os seguintes recursos **já existem**
(provisionados pelos repositórios irmãos):

1. Resource Group + cluster AKS → `oficina-infra-kubernetes`
2. Postgres Flexible Server → `oficina-infra-banco-dados`
3. API Gateway (Traefik) já aplicado no cluster → `oficina-infra-kubernetes`

### Infraestrutura própria (Storage de assinaturas + New Relic)

```bash
cd infra
terraform init
export TF_VAR_newrelic_account_id="sua-account-id"
export TF_VAR_newrelic_api_key="sua-user-api-key"  # NRAK-...
terraform plan
terraform apply
```

### CI/CD

[`.github/workflows/ci.yml`](.github/workflows/ci.yml): a cada push na
`main`, roda testes + JaCoCo, builda e publica a imagem Docker (Docker Hub),
e aplica os manifests em [`k8s/app/`](k8s/app) no cluster AKS — **deploy
100% automático**. É o único dos 4 repositórios com deploy automatizado
(os 3 repositórios de infraestrutura mantêm `terraform apply` manual, por
segurança — ver justificativa nos READMEs deles).

Segredos necessários no GitHub (Settings → Secrets and variables → Actions):
`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `AZURE_CREDENTIALS`,
`DB_APP_USERNAME`, `DB_APP_PASSWORD`, `WEBHOOK_APROVACAO_SECRET`,
`AZURE_STORAGE_CONNECTION_STRING`, `NEW_RELIC_LICENSE_KEY`.

### Deploy manual

```bash
az aks get-credentials --resource-group oficina-resources --name oficina-aks-cluster

kubectl apply -f k8s/app/configMap.yaml

kubectl create secret generic oficina-db-app \
  --from-literal=username=adminuser \
  --from-literal=password="sua-senha" \
  --from-literal=webhook-aprovacao-secret="seu-secret" \
  --from-literal=azure-storage-connection-string="sua-connection-string" \
  --from-literal=new-relic-license-key="sua-license-key" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f k8s/app/deployment.yaml
kubectl apply -f k8s/app/service.yaml
kubectl apply -f k8s/app/hpa.yaml

kubectl rollout status deployment/oficina-api
```

Depois disso, o `Ingress` do repositório `oficina-infra-kubernetes` (que
roteia pro `oficina-api-service` criado aqui) já pode ser aplicado.

---

## 🌐 Endpoints

Documentação interativa completa: **Swagger UI**
(`/q/swagger-ui/#/` depois de subir a aplicação) e a
**[collection Postman](docs/postman_collection.json)** — inclui a pasta
"Fase 3 - Autenticação CPF (Function Serverless)" com o fluxo completo de
ponta a ponta.

Principais grupos de endpoints: `/api/produtos`, `/api/servicos`,
`/api/clientes`, `/api/veiculos`, `/api/ordens`, `/api/orcamentos`,
`/api/relatorios`, `/api/usuarios` (login por e-mail/senha).

---

## 🧪 Testes

```bash
mvn clean test                # unitários + JaCoCo
newman run docs/postman_collection.json --env-var "baseUrl=http://localhost:8383"
```

Ver [`docs/architecture/diagrama-sequencia-abertura-os.mmd`](docs/architecture/diagrama-sequencia-abertura-os.mmd)
para o fluxo completo de abertura de OS testado pela collection.

---

## 📊 Observabilidade (New Relic)

- **Logs estruturados em JSON** com correlation-id —
  [`CorrelationIdFilter`](src/main/java/br/com/fiap/oficina/api/shared/infrastructure/web/CorrelationIdFilter.java).
- **APM** — New Relic Java Agent embutido em
  [`src/main/docker/Dockerfile.jvm`](src/main/docker/Dockerfile.jvm).
- **Alertas + Dashboard** — provisionados via Terraform em
  [`infra/newrelic.tf`](infra/newrelic.tf).
- **CPU/memória do cluster** — Helm chart no repositório
  `oficina-infra-kubernetes` (`k8s/observability/`).

---

## 👥 Equipe

Ver commits do repositório.
