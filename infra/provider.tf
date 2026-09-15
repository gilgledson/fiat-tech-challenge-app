terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    newrelic = {
      source  = "newrelic/newrelic"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

provider "newrelic" {
  account_id = var.newrelic_account_id
  api_key    = var.newrelic_api_key
  region     = "US"
}

# O Resource Group é provisionado pelo repositório oficina-infra-kubernetes
# — aqui só lemos o recurso já existente, nunca o criamos nem duplicamos.
data "azurerm_resource_group" "oficina_rg" {
  name = "oficina-resources"
}
