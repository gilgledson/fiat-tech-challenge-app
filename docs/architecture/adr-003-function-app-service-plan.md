# ADR-003 — Plano de hospedagem da Function Serverless (Consumption Plan)

- **Status**: Resolvido — publicado em produção no plano FC1/Flex
  Consumption (ver "Atualização 3" no final). O Terraform deste repositório
  ainda não reflete essa decisão final (pendência registrada no TODO.md).

## Contexto

A Function `oficina-auth-cpf` precisa de um plano de hospedagem no Azure. A
Azure oferece basicamente três opções para Azure Functions:

1. **Consumption Plan (Y1)** — paga só pelo tempo de execução real, escala
   a zero quando ociosa, é o modelo "serverless" no sentido estrito.
2. **Premium Plan** — sempre tem instâncias quentes (sem cold start),
   custo fixo mais alto.
3. **App Service Plan dedicado** — VM sempre ligada, custo fixo, sem
   vantagem de "serverless".

## Decisão

Usar **Consumption Plan (SKU `Y1`)**, definido em
[`infra/function.tf`](https://github.com/SEU_USUARIO/oficina-lambda-auth-cpf/blob/main/infra/function.tf)
(repositório `oficina-lambda-auth-cpf`)
(`azurerm_service_plan.function_plan`, `os_type = "Linux"`,
`sku_name = "Y1"`). É a opção que corresponde literalmente ao requisito do
desafio ("Function Serverless"): paga-se por execução, sem custo de
infraestrutura ociosa — adequado para uma function de baixo volume como a
autenticação por CPF (chamada só no login, não em toda requisição).

## Consequências

- **Positivo**: custo mínimo — sem tráfego, sem cobrança de compute.
- **Negativo (documentado, não resolvido nesta fase)**: durante o
  `terraform apply`, a criação do `azurerm_service_plan` com SKU `Y1`
  falhou com `401 Unauthorized — Operation cannot be completed without
  additional quota (Current Limit (Y1 VMs): 0)`. Isso indica que a
  assinatura Azure usada não tem cota de Consumption Plan liberada por
  padrão na região `Brazil South`. Como consequência, **a infraestrutura da
  Function ficou provisionada apenas parcialmente** (Storage Account e o
  código validados localmente, mas o `Service Plan`/`Function App` em si
  não foram criados na nuvem) — ver pendência registrada em
  [`TODO.md`](../../TODO.md).
- **Caminhos de resolução considerados**:
  1. Solicitar aumento de cota via Azure Portal (Help + Support → Service
     and subscription limits (quotas) → App Service → Consumption Y1 VMs)
     — descartado por não ser imediato (depende de aprovação, incerta em
     assinaturas de estudante/trial).
  2. Provisionar em outra região com cota disponível (cota de Consumption
     Plan é por região/assinatura) — **adotado**, ver "Atualização" abaixo.
  3. Trocar para um App Service Plan Basic (B1) dedicado — descartado por
     sair da definição estrita de "serverless paga por execução"; mantido
     como fallback caso a opção 2 também esbarre em cota em outra região.

## Atualização — resolvido via região diferente

A criação do `azurerm_service_plan`/`azurerm_linux_function_app` com SKU
`Y1` continuava falhando em `Brazil South`
(`401 — Current Limit (Y1 VMs): 0`). Como o Resource Group já existia
provisionado por outro repositório (`oficina-infra-kubernetes`) e não podia
ser recriado em outra região sem afetar o AKS/Postgres, a solução foi
provisionar **só os recursos da Function** (Storage Account, Service Plan,
Function App) numa região diferente do Resource Group — `East US`, via a
nova variável `var.function_location` em
[`infra/variables.tf`](https://github.com/SEU_USUARIO/oficina-lambda-auth-cpf/blob/main/infra/variables.tf)
(repositório `oficina-lambda-auth-cpf`). Azure permite recursos em qualquer
região dentro de um Resource Group, independente da região "padrão" do
próprio Resource Group — não há acoplamento técnico entre as duas.

Isso preserva a decisão original desta ADR (Consumption Plan de verdade,
sem custo de infraestrutura ociosa) sem depender de aprovação de aumento de
cota. Se a região `East US` também não tiver cota disponível numa
assinatura específica, a variável pode ser sobrescrita
(`TF_VAR_function_location`) para qualquer outra região sem alterar código.

## Atualização 2 — a restrição é da assinatura inteira, não da região

A troca de região **não resolveu**: o `terraform apply` em `East US` falhou
com o **mesmo erro exato** (`401 — Current Limit (Y1 VMs): 0`) que já
tinha acontecido em `Brazil South`. Evidência direta de que essa
assinatura Azure específica tem cota zero para VMs "Dynamic" (a família
usada pelo Consumption Plan) em **toda a assinatura**, não por região —
comum em assinaturas de estudante/trial com restrições agregadas.

Decisão final: trocar `sku_name` de `Y1` (Consumption) para **`B1`
(Basic)**, via nova variável `var.function_plan_sku` (padrão `"B1"`, pode
ser sobrescrita de volta para `"Y1"` se a cota for aprovada no futuro).
B1 é compute "normal" (família B-series), sem a restrição de cota que
bloqueava o Y1.

**Isso reabre a consequência negativa original desta ADR** (custo fixo,
plano sempre ligado, sem escalar a zero) — mas é uma troca deliberada e
documentada, não um desvio silencioso: a Function continua sendo uma
"Function Serverless" do ponto de vista do requisito do desafio (código
event-driven via HTTP trigger, deploy via Azure Functions Core Tools), só
o **plano de hospedagem** deixou de ser Consumption puro. Custo estimado do
B1: baixo (~R$50-80/mês se ligado o mês inteiro) — `terraform destroy`
quando não estiver em uso, mesma recomendação dada para os outros recursos
deste projeto.

## Atualização 3 — B1 também bloqueado; resolvido com FC1 (Flex Consumption)

O `terraform apply` com `sku_name = "B1"` falhou com o **mesmo padrão de
erro** da tentativa com `Y1` — só trocando "Y1 VMs" por "B1 VMs" na
mensagem (`401 — Current Limit (B1 VMs): 0`). Isso reformulou o
diagnóstico: a assinatura não tem cota zero só pra "Dynamic" (Y1) — tem
cota zero pra **qualquer família clássica de App Service Plan**
(`Microsoft.Web/serverfarms` compute), independente do SKU. AKS não sofre
disso porque usa uma família de cota de VM totalmente diferente
(`Microsoft.Compute`, não `Microsoft.Web`).

Criar o Function App **manualmente pelo Portal Azure** (mesmo Resource
Group, mesma assinatura) funcionou de primeira, usando o SKU **`FC1`
(Flex Consumption)** — um plano mais novo do Azure Functions, com uma
família de cota própria (`FC`), diferente das famílias `Y1`/`Dynamic` e
`B1`/`Basic` que estavam zeradas. A assinatura tinha cota disponível
especificamente para essa família.

**Decisão final**: usar `FC1` (Flex Consumption) como plano de hospedagem.
Reabre a vantagem original desta ADR (paga por execução, sem custo de
infraestrutura ociosa) — Flex Consumption é, na prática, a evolução do
Consumption Plan clássico.

**Situação atual (débito técnico registrado)**: o Function App
(`oficina-lambda-auth-cpf`) está publicado e funcionando em produção, com
variáveis de ambiente configuradas e deploy automático via CI/CD
(`Azure/functions-action@v1` no repositório `oficina-lambda-auth-cpf`) —
mas foi **criado manualmente**, não pelo `terraform apply`. O
`infra/function.tf` ainda declara os recursos com SKU `B1` e o nome
`oficina-auth-cpf` (diferente do nome real, `oficina-lambda-auth-cpf`).
Terraform não gerencia esse recurso hoje. Próximo passo: reescrever
`function.tf` usando o recurso `azurerm_function_app_flex_consumption`
(SKU `FC1`, disponível em versões mais recentes do provider `azurerm`) com
os nomes corretos, e rodar `terraform import` nos recursos já existentes
para que o Terraform passe a gerenciá-los sem recriar do zero.
