# ADR-003 — Plano de hospedagem da Function Serverless (Consumption Plan)

- **Status**: Aceito e resolvido (ver "Atualização" no final)

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
