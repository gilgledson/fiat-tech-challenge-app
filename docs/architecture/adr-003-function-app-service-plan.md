# ADR-003 — Plano de hospedagem da Function Serverless (Consumption Plan)

- **Status**: Aceito, com pendência operacional conhecida

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
- **Caminhos de resolução, para quando a cota for tratada**:
  1. Solicitar aumento de cota via Azure Portal (Help + Support → Service
     and subscription limits (quotas) → App Service → Consumption Y1 VMs)
     — pode não ser imediato em assinaturas de estudante/trial.
  2. Tentar provisionar em outra região com cota disponível (cota de
     Consumption Plan é por região/assinatura).
  3. Como último recurso, trocar para um **App Service Plan Basic (B1)**
     dedicado só para a Function — sai da definição estrita de
     "serverless paga por execução", mas desbloqueia o deploy sem depender
     de aprovação de cota; essa troca ficaria registrada como revisão desta
     ADR se adotada.
