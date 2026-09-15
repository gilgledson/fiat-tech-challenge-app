variable "newrelic_account_id" {
  description = "ID da conta New Relic (Account Settings > Account ID em one.newrelic.com)."
  type        = string
}

variable "newrelic_api_key" {
  description = "User API Key do New Relic (começa com 'NRAK-') — usada pelo provider Terraform pra criar dashboards e alertas via NerdGraph. NÃO é a license key do agent (essa vai só no k8s Secret). Nunca definir um valor aqui — fornecer via TF_VAR_newrelic_api_key ou um arquivo *.tfvars (gitignored)."
  type        = string
  sensitive   = true
}

variable "newrelic_app_name" {
  description = "Nome da aplicação como reportado ao New Relic pelo Java Agent — precisa bater com NEW_RELIC_APP_NAME em k8s/app/configMap.yaml, senão as queries do dashboard/alertas não encontram dado nenhum."
  type        = string
  default     = "Oficina API (AKS)"
}

variable "alert_notification_email" {
  description = "E-mail que recebe os alertas de falha da Oficina API. Deixe vazio para não criar canal de notificação (só a policy/condition ficam provisionadas, sem ninguém sendo avisado)."
  type        = string
  default     = ""
}
