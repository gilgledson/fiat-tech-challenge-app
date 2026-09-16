# Roteiro — Vídeo de Demonstração (Fase 3)

Duração alvo: **~13:30 min** (limite do desafio: 15 min). Upload no YouTube ou
Vimeo, público ou não-listado.

## Checklist antes de gravar

- [x] `kubectl get svc -n gateway` — `EXTERNAL-IP` do Traefik confirmado
      agora: **`20.206.175.32`** (confere de novo antes de gravar, vai mudar
      se o LoadBalancer for recriado). Todas as chamadas à API principal
      usam `http://20.206.175.32/...` — healthcheck testado, `200 OK`.
- [ ] Abrir abas já logadas: GitHub (4 repositórios), New Relic
      (`one.newrelic.com`), Postman (collection
      `docs/postman_collection.json` importada, com a variável de ambiente
      `baseUrl` trocada pra `http://20.206.175.32` só na sua sessão do
      Postman — o valor padrão salvo no arquivo continua `localhost:8080`,
      de propósito, não mexer nele).
- [x] Terminal com `kubectl` configurado (`kubectl get pods` funcionando,
      pod `oficina-api` `Running`) e outro terminal/aba pronto pra
      `kubectl logs -f deployment/oficina-api`.
- [ ] Ter um CPF **válido e já cadastrado** de um cliente de teste em mãos
      (dígito verificador correto) — usar o pré-request script da collection
      Postman pra gerar um novo, se precisar.
- [ ] Ter uma alteração pequena e inofensiva pronta pra commitar ao vivo
      (ex: um comentário, ou reverter/reaplicar uma linha do README) pra
      disparar a pipeline de verdade durante a gravação.
- [x] Revisar se o README de cada repo já está com os links reais (com
      `gilgledson`, sem placeholder `SEU_USUARIO`) antes de mostrar na tela —
      já corrigido em todos os 4 repositórios.

---

## 0:00 – 0:40 | Abertura

Fala rápida, direto ao ponto:

> "Esse é o Tech Challenge Fase 3 da FIAP — evoluí a API da oficina mecânica
> pra um nível de operação corporativa: API Gateway, autenticação serverless
> por CPF, observabilidade completa com New Relic, e o projeto separado em
> 4 repositórios com CI/CD independente. Vou mostrar tudo funcionando ao
> vivo, em produção na Azure."

Mostrar rapidamente a tela com os 4 repositórios abertos em abas (nomes
visíveis) — app, infra-kubernetes, infra-database, lambda-auth-cpf.

## 0:40 – 2:00 | Arquitetura (visão geral)

- Abrir [`docs/architecture/diagrama-componentes.mmd`](architecture/diagrama-componentes.mmd)
  renderizado (print ou Mermaid Live).
- Narrar o fluxo em 1 frase por componente: **Traefik como API Gateway**
  (único ponto de entrada externo, roteia pra API) → AKS (API Quarkus) →
  Postgres Flexible Server; Function Azure separada pra login por CPF, mesma
  chave JWT que a API valida; New Relic observando tudo.
- Citar rapidamente os 4 repositórios e o motivo da separação (requisito do
  desafio + isolamento de CI/CD).

## 2:00 – 4:30 | API Gateway + Autenticação por CPF + Consumo de API protegida

0. **Mostrar o Gateway antes de usar ele** (~20s): terminal,
   `kubectl get svc -n gateway` — apontar o `Service traefik` como
   `LoadBalancer` com o `EXTERNAL-IP` real, e o pod do Traefik `Running`
   (`kubectl get pods -n gateway`). Narrar: "esse IP é a única porta de
   entrada externa do cluster — o `oficina-api-service` é `ClusterIP`, não
   tem IP público próprio, só o Traefik na frente decide o roteamento." Se
   sobrar tempo/confiança, `kubectl port-forward svc/traefik-dashboard 8080:8080
   -n gateway` e abrir `localhost:8080` rapidinho pra mostrar o router
   configurado no dashboard do próprio Traefik.

Via Postman (ou `curl`), ao vivo:

1. **CPF inválido** → `POST` na Function
   (`https://oficina-lambda-auth-cpf-efedakf9cfh7dtbd.brazilsouth-01.azurewebsites.net/api/auth/cpf`)
   com CPF mal formado → mostrar `400`.
2. **CPF válido de cliente cadastrado** → mesma rota → mostrar `200` e o
   `access_token` (JWT) na resposta.
3. **Usar o token** num endpoint protegido da API principal, batendo direto
   no **IP do Gateway** (ex: `GET http://20.206.175.32/api/ordens`, header
   `Authorization: Bearer <token>`) → `200`, dados reais. Reforçar: "essa
   chamada passou pelo Traefik antes de chegar na API."
4. **Sem token** na mesma rota → `401`.
5. (Opcional, reforça o requisito "proteger rotas sensíveis") token de
   `CLIENTE` numa rota exclusiva de staff → `403`.

Narrar enquanto isso: "o JWT é assinado pela Function com a mesma chave RSA
que a API Quarkus já usa pro login da equipe interna — não precisei mudar
nada no código Java pra aceitar esse segundo modo de login."

## 4:30 – 7:30 | Pipeline CI/CD + Deploy automatizado

1. Fazer o commit pequeno preparado no checklist, `git push` na `main` do
   `oficina-app`, **ao vivo, na tela**.
2. Abrir a aba **Actions** do GitHub imediatamente — mostrar o workflow
   iniciando.
3. Enquanto builda (pode acelerar/cortar na edição), explicar os estágios:
   build da imagem → push pro Docker Hub → `kubectl apply` no AKS.
4. Quando o job de deploy terminar: voltar pro terminal,
   `kubectl get pods` → mostrar o pod novo `Running`, o antigo terminando
   (rolling update).
5. Bater rapidamente num endpoint de novo (ou `/q/health/ready`) pra provar
   que a versão nova está respondendo.
6. Citar em 1 frase os outros repositórios de infra: `terraform plan`
   roda automático em CI a cada PR, `apply` é manual por segurança (evitar
   mudar banco/cluster de produção sem revisão humana) — mostrar rapidamente
   o `ci.yml` de um deles se sobrar tempo.

## 7:30 – 11:00 | Dashboard de monitoramento (análise ao vivo)

Esse é o item que o PDF pede explicitamente "ao vivo" — gerar tráfego real
enquanto o dashboard está na tela:

1. Abrir o dashboard **"Oficina API - Visão Geral"** no New Relic
   (`one.newrelic.com/redirect/entity/ODUxMzk4OXxWSVp8REFTSEJPQVJEfGRhOjEzMTc0NzA2`).
2. Rodar a collection do Postman (ou um loop simples de `curl`) contra a API
   em produção, **enquanto a tela do dashboard está visível**.
3. Apontar o widget de **latência** reagindo, o de **uptime do healthcheck**
   em 100%, e o volume de OS/erros.
4. Mostrar a **alert policy** configurada (`Oficina API - Alertas`) — 2
   condições NRQL (falhas no processamento de OS, latência alta) — não
   precisa disparar um alerta de verdade, só mostrar que existe e está
   `Enabled`.
5. Mostrar rapidamente o painel de **Kubernetes** (`newrelic/nri-bundle`) —
   CPU/memória dos pods do cluster.

## 11:00 – 13:00 | Logs e traces em execução

1. Terminal: `kubectl logs -f deployment/oficina-api -n default` (ajustar
   nome/namespace reais) — disparar uma requisição em paralelo e mostrar a
   linha de log JSON aparecendo, apontando o campo `correlationId`.
2. Voltar pro New Relic → **APM & Services → Oficina API → Transactions** —
   abrir uma transação recente e mostrar o **trace** (breakdown de tempo por
   camada: JAX-RS, JDBC).
3. Frase de fechamento desse bloco: "o `correlationId` do log bate com o que
   a aplicação devolve no header da resposta — dá pra rastrear uma
   requisição específica do log até o trace no New Relic."

## 13:00 – 13:30 | Encerramento

> "Isso cobre os requisitos da Fase 3: gateway, autenticação serverless por
> CPF, observabilidade completa e os 4 repositórios com CI/CD independente.
> Toda a documentação de arquitetura — RFCs, ADRs, diagramas, DER — está no
> repositório principal, `docs/architecture`. Obrigado!"

---

## Notas de gravação

- Cortes na edição são bem-vindos nos trechos de "esperando o CI terminar"
  — não precisa gravar os ~2-3min de build parado.
- Se algo falhar ao vivo (ex: token expirado, pod não subiu a tempo), é
  melhor cortar e regravar só aquele trecho do que tentar explicar o erro —
  a não ser que você queira mostrar troubleshooting de propósito.
- Ordem dos blocos pode mudar se for mais natural pra você narrar, mas os
  6 itens obrigatórios (autenticação CPF, pipeline CI/CD, deploy
  automatizado, consumo de API protegida, dashboard ao vivo, logs/traces)
  precisam aparecer todos.
- O **API Gateway** (Traefik) não é um dos 6 itens explicitamente listados
  no PDF pra demonstrar no vídeo, mas é requisito obrigatório da Fase 3 —
  por isso ganhou um passo dedicado (bloco 0, antes da autenticação) em vez
  de aparecer só implicitamente nas chamadas HTTP.
