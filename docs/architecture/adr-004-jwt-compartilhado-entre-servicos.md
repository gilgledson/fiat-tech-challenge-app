# ADR-004 — Chave de assinatura JWT compartilhada entre a API e a Function

- **Status**: Aceito

## Contexto

Ver [RFC-003](rfc-003-estrategia-de-autenticacao.md) para a análise completa
das alternativas. Esta ADR registra formalmente, como decisão arquitetural
permanente (não só o resultado de uma RFC pontual), o mecanismo escolhido:
**a Function `oficina-auth-cpf` assina tokens com a mesma chave privada RSA
e o mesmo `issuer` que a API Quarkus usa para validar.**

## Decisão

- A chave privada (`src/main/resources/privateKey.pem`, RS256) é a **fonte
  única de verdade** de assinatura para todo o sistema — tanto o login por
  e-mail/senha (`EfetuarLoginUseCaseImpl`, dentro do monólito) quanto o
  login por CPF (Function, fora do monólito) assinam com ela.
- O `issuer` (`oficina-api-interna`) também é compartilhado — a API valida
  esse issuer via `smallrye.jwt.verify.issuer`, sem distinguir "de onde"
  veio o token.
- A claim `groups` (usada pelo `@RolesAllowed`) é o único contrato real
  entre emissor e validador: qualquer token com `groups: ["CLIENTE"]`,
  assinado com a chave certa, é aceito nas rotas de cliente — a API não
  sabe nem precisa saber que esse token específico veio de uma Function.

## Consequências

- **Positivo**: acoplamento **zero** de código entre API e Function — a
  API nunca foi modificada para "aprender" sobre a Function. Validado
  concretamente: os endpoints `@RolesAllowed({"CLIENTE"})` já existentes
  (criados antes da Function existir) aceitaram os tokens dela sem
  nenhuma alteração.
- **Positivo**: qualquer novo emissor de token no futuro (ex.: uma segunda
  Function, um app mobile com seu próprio backend-for-frontend) pode
  reusar a mesma chave sem exigir mudança na API.
- **Negativo, aceito conscientemente**: a chave privada precisa ser
  distribuída para múltiplos ambientes de execução (K8s Secret da API,
  App Setting da Function). Cada novo lugar que guarda a chave é uma nova
  superfície de vazamento — mitigado por nunca commitá-la (apesar de,
  historicamente, o arquivo `privateKey.pem` já estar versionado no
  próprio repositório Git da aplicação desde a Fase 2, o que é uma prática
  de risco pré-existente, fora do escopo desta ADR corrigir, mas registrada
  aqui para visibilidade).
- **Negativo**: rotação de chave é uma operação coordenada — trocar a chave
  em só um lugar quebra a validação nos outros. Não há hoje um processo
  automatizado de rotação; é manual e precisa tocar pelo menos dois
  sistemas (API e Function) ao mesmo tempo.
- **Alternativa preservada para o futuro**: se um dia for necessário isolar
  os dois emissores (ex.: por auditoria, "quero saber se o token veio do
  login interno ou do CPF"), a claim customizada `cliente_id` (presente só
  nos tokens da Function) já permite essa distinção sem precisar de chaves
  separadas — não seria necessário reverter esta decisão, só adicionar uma
  checagem opcional.
