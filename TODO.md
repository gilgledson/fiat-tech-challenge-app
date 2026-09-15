# TODO — Tech Challenge Fase 3

Checklist do que ainda falta para atender aos requisitos obrigatórios da Fase 3
(`13SOAT - Fase 3 - Tech Challenge.pdf`), com base no estado atual do repositório
(herdado da Fase 2: Quarkus + AKS + Terraform + Postgres gerenciado + HPA + CI/CD
de deploy já implementados).

> Legenda: o que já está pronto da Fase 2 **não** está listado aqui. Isto é só o
> que falta fazer para a Fase 3.

## Autenticação e API Gateway

- [x] Implementar um API Gateway (Traefik) na frente da aplicação — o
      `oficina-api-service` agora é `ClusterIP` e o tráfego externo entra pelo
      `Service traefik` (LoadBalancer) e é roteado via `Ingress` até a
      aplicação. Ver [`k8s/gateway/`](k8s/gateway) e a seção
      [API Gateway (Traefik)](README.md#-api-gateway-traefik) no README.
      Pendente: validar em cluster real (`terraform apply` + push na `main`)
      e, quando a autenticação por CPF (próximo item) existir, mover a
      validação para o gateway (Middleware `ForwardAuth`).
- [x] Proteger rotas sensíveis com autenticação via **CPF** — os endpoints
      protegidos por `@RolesAllowed({"CLIENTE", ...})` (ex:
      `GET /api/ordens/{id}`, `POST /api/ordens/{id}/aprovar`) já existiam e
      validam qualquer JWT com `groups=CLIENTE`, independente de quem emitiu.
      O login por CPF (item abaixo) é um **segundo modo de login**, só para
      clientes — o login por e-mail/senha da equipe interna
      (`UsuarioController`/`EfetuarLoginUseCaseImpl`) continua intacto.
      Pendente: nenhuma rota valida que o `CLIENTE` autenticado é o **dono**
      da OS que está acessando (gap de autorização pré-existente, não
      introduzido por essa mudança — só ficou mais visível agora).
- [x] Criar uma **Function Serverless** (Azure Functions, Node.js) — agora
      no repositório próprio
      [`oficina-lambda-auth-cpf`](https://github.com/gilgledson/fiat-tech-challenge-lambda-auth-cpf) que:
  - [x] Valida o CPF do cliente (dígito verificador, formato).
  - [x] Consulta a existência e o status (`deletado_em`) do cliente direto no
        Postgres.
  - [x] Gera e devolve um JWT RS256 assinado com a mesma chave/issuer que a
        API já valida (`groups: ["CLIENTE"]`) — sem nenhuma mudança de config
        no lado Java.
  - **Validado localmente de ponta a ponta** (docker-compose + `func start` +
    Newman): criar cliente com CPF válido → login na Function → token aceito
    em rota `CLIENTE` da API principal (200) → rejeitado em rota staff-only
    (403) → sem token (401) → CPF inválido (400) → cliente inexistente (404).
    8 requests / 12 assertions, todas passando. Cobertura em
    [`docs/postman_collection.json`](docs/postman_collection.json), pasta
    "Fase 3 - Autenticação CPF (Function Serverless)".
  - **Publicada e funcionando em produção**: `oficina-lambda-auth-cpf` está
    no ar na Azure (plano `FC1`/Flex Consumption), com as variáveis de
    ambiente configuradas e o código publicado
    (`func azure functionapp publish`). CI/CD configurado para publicar o
    código automaticamente a cada push na `main`
    (`Azure/functions-action@v1`).
  - **Jornada até chegar lá** (documentada em detalhe no
    [ADR-003](docs/architecture/adr-003-function-app-service-plan.md)):
    `Y1` (Consumption) falhou por cota zero em Brazil South → trocar região
    pra East US não resolveu (mesmo erro) → trocar SKU pra `B1` (Basic)
    também não resolveu (mesmo erro, cota 0 pra qualquer família clássica
    de App Service Plan na assinatura) → **criado manualmente pelo Portal
    Azure usando o plano `FC1` (Flex Consumption)**, uma família de cota
    diferente que a assinatura tinha liberada.
  - **Pendência real**: o `infra/function.tf` ainda declara os recursos
    com SKU `B1` e nome `oficina-auth-cpf` — **não bate** com o que existe
    de fato na nuvem (`FC1`, nome `oficina-lambda-auth-cpf`, criado fora do
    Terraform). Terraform não gerencia esse recurso ainda. Para corrigir:
    atualizar `function.tf` para usar o recurso
    `azurerm_function_app_flex_consumption` (SKU `FC1`) com os nomes
    corretos, e rodar `terraform import` nos recursos já existentes.

## Estrutura de Repositórios e CI/CD

- [x] Separar o projeto em **4 repositórios**, todos criados e enviados ao GitHub:
  - [x] Lambda (Function Serverless) — [`fiat-tech-challenge-lambda-auth-cpf`](https://github.com/gilgledson/fiat-tech-challenge-lambda-auth-cpf)
  - [x] Infraestrutura Kubernetes (Terraform) — [`fiat-tech-challenge-infra-kubernetes`](https://github.com/gilgledson/fiat-tech-challenge-infra-kubernetes)
  - [x] Infraestrutura do Banco de Dados Gerenciado (Terraform) — [`fiat-tech-challenge-infra-database`](https://github.com/gilgledson/fiat-tech-challenge-infra-database)
  - [x] Aplicação principal (Kubernetes) — [`fiat-tech-challenge-app`](https://github.com/gilgledson/fiat-tech-challenge-app) (este repositório)
- [x] Configurar CI/CD (GitHub Actions) em cada um dos 4 repositórios — todos
      com `.github/workflows/ci.yml` próprio. **Validado**: pipeline do
      `fiat-tech-challenge-app` rodou de ponta a ponta (build → push da
      imagem → deploy no AKS → pod saudável) depois de configurar os 8
      GitHub Secrets nesse repositório (não herdam do monorepo antigo).
      Repositórios de infraestrutura (`infra-kubernetes`, `infra-database`)
      só precisam do `AZURE_CREDENTIALS` cada (Service Principal próprio,
      escopado ao resource group `oficina-resources`).
- [ ] Proteger a branch `main`/`master` em cada repositório (sem commits diretos,
      PR obrigatório para merge) — **ainda não configurado**.
- [x] Deploy automático para a nuvem: **só o repositório da aplicação
      principal** tem deploy 100% automático (build+push+k8s apply a cada
      push na `main`) — decisão deliberada, documentada nos READMEs dos 3
      repositórios de infraestrutura: `terraform apply` fica manual por
      segurança (evitar drift/custo automático em cluster/banco), só o
      `terraform plan` roda em CI. Não há branches de homologação
      separadas em nenhum repositório ainda — só `main`.
- **Achado durante a separação**: um dos repositórios de infraestrutura foi
  enviado com o nome errado por engano (conteúdo do banco de dados foi pro
  repositório nomeado "infra-kubernetes"). Corrigido apagando o repositório
  mal nomeado e recriando os dois corretamente
  (`fiat-tech-challenge-infra-kubernetes` e
  `fiat-tech-challenge-infra-database`) — sem perda de dado, todo o
  conteúdo continuava íntegro nas pastas locais.

## Monitoramento e Observabilidade

- [x] Integrar uma ferramenta de observabilidade — **New Relic**. **Validado
      em produção**: Java Agent conectado em `collector.newrelic.com` no
      cluster AKS real, reportando dados de verdade.
- [x] Implementar logs estruturados em JSON com correlação entre requisições
      — extensão `quarkus-logging-json` +
      [`CorrelationIdFilter`](src/main/java/br/com/fiap/oficina/api/shared/infrastructure/web/CorrelationIdFilter.java).
      **Validado em produção**: `correlationId` aparece no MDC do log real,
      header devolvido na resposta. Limitação conhecida: não aparece em
      respostas 401 de autenticação — baixo impacto, não persegui.
- [x] Monitorar latência das APIs — New Relic Java Agent
      ([Dockerfile.jvm](src/main/docker/Dockerfile.jvm)) instrumenta
      JAX-RS/JDBC automaticamente. **Validado em produção**: widget de
      latência do dashboard com dado real ao vivo.
- [x] Monitorar healthchecks e uptime — `startupProbe`/`readinessProbe`/
      `livenessProbe` em [k8s/app/deployment.yaml](k8s/app/deployment.yaml)
      (não existiam antes, achado durante a sessão do Gateway). **Validado
      em produção**: widget "Uptime do Healthcheck" mostrando 100%.
- [x] Configurar alertas para falhas no processamento de ordens de serviço —
      `newrelic_alert_policy` + 2 `newrelic_nrql_alert_condition` em
      [infra/newrelic.tf](infra/newrelic.tf). **Aplicado de verdade** na
      conta New Relic (`terraform apply`), 4 recursos criados. Canal de
      notificação por e-mail continua opcional
      (`TF_VAR_alert_notification_email`).
- [x] Expor dashboards com volume diário de OS, tempo médio por status e
      erros/falhas por endpoint — `newrelic_one_dashboard` em
      [infra/newrelic.tf](infra/newrelic.tf). **Aplicado e validado**:
      dashboard "Oficina API - Visão Geral" renderizando com dado real
      (latência, uptime). Link:
      `one.newrelic.com/redirect/entity/ODUxMzk4OXxWSVp8REFTSEJPQVJEfGRhOjEzMTc0NzA2`
- [x] Monitorar consumo de recursos do Kubernetes (CPU, memória) — chart Helm
      oficial `newrelic/nri-bundle`, values em
      [k8s/observability/newrelic-values.yaml](k8s/observability/newrelic-values.yaml).
      Instalação é passo manual (como o `terraform apply`), não entrou no
      `ci.yml`. **Instalado e validado**: 6 pods `Running` no namespace
      `newrelic` (Infrastructure Agent, kube-state-metrics, nri-kube-events,
      nri-metadata-injection, Fluent Bit), sem erro de autenticação nos logs.

**Bugs reais encontrados e corrigidos durante a validação em produção**
(nenhum deles estava relacionado ao código da observabilidade em si — todos
eram credenciais dessincronizadas entre Terraform/GitHub Secrets/cluster,
categoria de bug que já tinha aparecido antes com `DB_APP_PASSWORD`):
1. `ci.yml` ainda usava `envsubst` sobre YAML pra gerar o `Secret` —
   corrigido pra `kubectl create secret --from-literal`.
2. `AZURE_STORAGE_CONNECTION_STRING` desatualizada (Storage Account recriado
   nesta sessão, secret não acompanhou) — causava 403 no aceite de
   orçamento, com efeito cascata em 8 testes da collection Newman.
3. `NEW_RELIC_LICENSE_KEY` no cluster estava com a **User API Key**
   (`NRAK-...`) em vez da **License Key** (termina em `NRAL`) — o agent
   tentava conectar num host inexistente derivado da chave errada e nunca
   reportava dado nenhum.
4. Query do widget "Uptime do Healthcheck" filtrava por `request.uri` (nunca
   populado pelas rotas de health do SmallRye) — trocada pra filtrar pelo
   nome real da transação (`health/ready`).

## Documentação da Arquitetura

Tudo em [`docs/architecture/`](docs/architecture) (índice completo em
[`docs/architecture/README.md`](docs/architecture/README.md)).

- [x] Diagrama de Componentes (visão de nuvem, APIs, banco e monitoramento) —
      [`diagrama-componentes.mmd`](docs/architecture/diagrama-componentes.mmd),
      renderizado e conferido visualmente.
- [x] Diagrama de Sequência para o fluxo de autenticação e abertura de ordens
      de serviço — dois diagramas:
      [autenticação por CPF](docs/architecture/diagrama-sequencia-autenticacao-cpf.mmd)
      e
      [abertura de OS](docs/architecture/diagrama-sequencia-abertura-os.mmd)
      (este último conferido contra o código real de
      `AbrirOrdemDeServicoUseCaseImpl`).
- [x] RFCs para decisões técnicas relevantes —
      [nuvem](docs/architecture/rfc-001-escolha-da-nuvem.md),
      [banco de dados](docs/architecture/rfc-002-escolha-do-banco-de-dados.md),
      [estratégia de autenticação](docs/architecture/rfc-003-estrategia-de-autenticacao.md).
- [x] ADRs para decisões arquiteturais permanentes —
      [padrão de comunicação](docs/architecture/adr-001-padrao-de-comunicacao.md),
      [uso de HPA](docs/architecture/adr-002-uso-de-hpa.md),
      [plano da Function (Consumption)](docs/architecture/adr-003-function-app-service-plan.md),
      [JWT compartilhado entre API e Function](docs/architecture/adr-004-jwt-compartilhado-entre-servicos.md).
- [x] Justificativa formal da escolha do banco de dados e ajustes no modelo
      relacional, com diagrama ER (DER) e explicação dos relacionamentos —
      [`justificativa-banco-de-dados.md`](docs/architecture/justificativa-banco-de-dados.md)
      +
      [`der-oficina-api.mmd`](docs/architecture/der-oficina-api.mmd).
      **Schema real levantado das 21 migrations Flyway** (não um desenho
      teórico) — 11 tabelas, 14 FKs, 2 views de relatório. A auditoria achou
      e documentou 5 divergências reais entre schema/código (ex:
      `orcamento.status` sem `CHECK` constraint, dois campos de quantidade
      com tipo Java/SQL diferente) — não corrigidas nesta fase, registradas
      como recomendação.

## README.md de cada repositório

- [ ] Atualizar/criar README com: descrição do propósito, tecnologias, passos
      de execução/deploy, diagrama de arquitetura específico e link do
      Swagger/Postman — em cada um dos 4 repositórios (o README atual cobre
      bem a Fase 2, mas não os itens novos da Fase 3).

## Vídeo de demonstração

- [ ] Gravar novo vídeo (até 15 min, YouTube/Vimeo) demonstrando:
  - [ ] Autenticação com CPF.
  - [ ] Execução da pipeline CI/CD.
  - [ ] Deploy automatizado.
  - [ ] Consumo das APIs protegidas.
  - [ ] Dashboard de monitoramento com análise ao vivo.
  - [ ] Logs e traces em execução.

## Entrega no Portal do Aluno

- [ ] Montar PDF único com: links dos 4 repositórios, link do vídeo (≤15 min),
      links das documentações e confirmação de que o usuário
      `soat-architecture` foi adicionado a todos os repositórios.

## Achado à parte (segurança, fora do escopo da Fase 3)

- [ ] Revogar/rotacionar o Personal Access Token do GitHub exposto em texto
      puro na URL do remote `origin` (`.git/config`) e reconfigurar o remote
      via SSH ou `gh auth login`.

## Corrigido: regressão no Dockerfile (achada ao validar o teste de CPF)

- [x] `POST /api/orcamentos/{id}/aceitar` retornava 500 (e derrubava em
      cascata 8 outras assertions da collection Newman: aprovação automática
      da OS, baixa de estoque, valor final do orçamento, listagem de OS,
      relatório de esforço). Causa raiz: ao trocar a imagem base do
      [Dockerfile.jvm](src/main/docker/Dockerfile.jvm) de
      `registry.access.redhat.com/ubi8/openjdk-17` para `eclipse-temurin:17-jre`
      (pra resolver o 502 do registry da Red Hat no CI), perdi a convenção do
      OpenShift de deixar `/deployments` gravável pelo grupo `0` — o
      `LocalFileStorageService` (fallback `STORAGE_TYPE=local`) não conseguia
      mais criar `uploads/assinaturas/`. Corrigido com
      `RUN chmod -R g+rwX /deployments` no Dockerfile. Validado: collection
      completa (51 requests / 57 assertions) passando 100% localmente.
