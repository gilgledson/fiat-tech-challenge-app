# Armazenamento das assinaturas de aceite de orçamento. Antes ficavam no disco
# local do pod (efêmero: some a cada restart/redeploy e não é compartilhado
# entre réplicas do HPA) — agora vão pro Azure Blob Storage.

# Nome de Storage Account precisa ser globalmente único em todo o Azure — foi
# gerado uma vez com sufixo aleatório e fixado aqui (não usamos mais
# `random_string` pra isso: um recurso "random" não tem objeto real na nuvem
# pra conferir num `terraform import`, então ele sempre assume os parâmetros
# padrão do provider e força recriação da Storage Account real no primeiro
# `apply` pós-import — arriscado, já que ela guarda os arquivos de assinatura
# dos orçamentos).
resource "azurerm_storage_account" "oficina_storage" {
  name                     = "oficinasign0pqr9z"
  resource_group_name      = data.azurerm_resource_group.oficina_rg.name
  location                 = data.azurerm_resource_group.oficina_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
}

resource "azurerm_storage_container" "assinaturas" {
  name                  = "assinaturas"
  storage_account_name  = azurerm_storage_account.oficina_storage.name
  container_access_type = "private"
}
