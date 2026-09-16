# RFC-003 — Estratégia de autenticação (dois modos de login + JWT compartilhado)

- **Status**: Aceito
- **Data**: 2026-09 (Fase 3)
- **Autores**: Equipe Oficina API

## Contexto

Até a Fase 2, a API tinha um único modo de autenticação: login por
e-mail/senha (`POST /api/usuarios/login`), usado pela equipe interna
(`ADMIN`, `ATENDENTE`, `MECANICO`) e, tecnicamente, também disponível para
clientes que tivessem um `Usuario` vinculado. A Fase 3 exige:

- Uma **Function Serverless** que valide o CPF do cliente, consulte sua
  existência/status no banco e emita um JWT.
- Um **API Gateway** protegendo rotas sensíveis.

A pergunta central desta RFC: como fazer o login por CPF (emitido por um
processo separado, fora do monólito) resultar em um token que a API
principal aceita **sem** duplicar lógica de autenticação nem exigir que o
cliente tenha uma conta `Usuario` completa?

## Alternativas consideradas

### A) Function chama a API para pedir um token
A Function receberia o CPF, chamaria um endpoint interno da API
(`POST /api/interno/emitir-token`), que geraria o JWT com sua própria
lógica já existente.

- Prós: um único ponto de emissão de token; API mantém controle total.
- Contras: exige expor um novo endpoint interno "de confiança" (mais
  superfície de ataque), acopla a Function a estar sempre disponível
  *e* à API estar de pé — perde parte do valor de ser "serverless
  independente"; adiciona uma chamada de rede a mais em cada login.

### B) Function assina o próprio JWT com uma chave independente
A Function teria seu próprio par de chaves RSA, e a API precisaria
confiar em **dois issuers/chaves** diferentes.

- Prós: isolamento total entre Function e API.
- Contras: complexidade de configuração (a API teria que aceitar múltiplas
  chaves de verificação), duas chaves para rotacionar e proteger em vez de
  uma, sem ganho real de segurança para este caso de uso (ambas residem no
  mesmo provedor de nuvem, mesma responsabilidade de proteção de segredo).

### C) Function assina o JWT com a mesma chave privada e issuer que a API já usa (escolhida)
A Function recebe uma cópia da mesma chave privada RSA
(`src/main/resources/privateKey.pem`) e do mesmo `issuer`
(`oficina-api-interna`) via variável de ambiente/App Setting, e monta um
token com `groups: ["CLIENTE"]`.

- Prós: **zero mudança de código ou configuração no lado Java** — o
  `smallrye.jwt.verify.*` já existente valida o token normalmente, porque
  a validação de assinatura/issuer é agnóstica a *quem* gerou o token.
  Nenhuma chamada de rede extra: a Function consulta o Postgres
  diretamente e responde em uma única ida e volta.
- Contras: a chave privada precisa ser distribuída com segurança para um
  segundo ambiente de execução (Function App), aumentando a superfície de
  onde ela pode vazar (mitigado: nunca commitada, só via App Setting/GitHub
  Secret — mesmo tratamento dado às demais credenciais do projeto).

## Decisão

Adotar a **Alternativa C**. A Function `oficina-auth-cpf`
(repositório [`oficina-lambda-auth-cpf`](https://github.com/gilgledson/fiat-tech-challenge-lambda-auth-cpf)):

1. Valida o formato do CPF (dígito verificador) localmente, sem chamar a
   API.
2. Consulta a tabela `cliente` diretamente no mesmo Postgres da aplicação
   (`SELECT id, nome, email, deletado_em FROM cliente WHERE cpf_cnpj = ?`),
   verificando existência e status ativo (`deletado_em IS NULL`).
3. Assina um JWT RS256 com a claim `groups: ["CLIENTE"]`, o mesmo `iss` e a
   mesma chave privada que a API já usa para validar (ver
   [ADR-004](adr-004-jwt-compartilhado-entre-servicos.md) para o registro
   formal dessa decisão como permanente).

O login por e-mail/senha (`EfetuarLoginUseCaseImpl`) continua existindo,
inalterado, para a equipe interna — os dois modos de login coexistem e são
independentes; a única coisa que compartilham é o **formato e a chave** do
token final, não o fluxo de autenticação em si.

Ver diagrama de sequência completo em
[`diagrama-sequencia-autenticacao-cpf.mmd`](diagrama-sequencia-autenticacao-cpf.mmd).

## Consequências

- **Positivo**: nenhuma mudança em `application.yml`, controllers ou
  `@RolesAllowed` da API — os endpoints já preparados para `CLIENTE`
  (`GET /api/ordens/{id}`, `POST /api/ordens/{id}/aprovar`, etc.) passaram
  a aceitar tokens da Function imediatamente.
- **Positivo**: a Function funciona de forma independente da API estar no
  ar (só depende do Postgres) — alinhado com a proposta de "serverless" do
  desafio.
- **Risco identificado e documentado, não corrigido nesta fase**: nenhuma
  rota valida que o `CLIENTE` autenticado é o **dono** da OS que está
  acessando — qualquer JWT válido com `groups=CLIENTE` pode consultar ou
  aprovar a OS de **qualquer** cliente pelo ID. Esse gap de autorização já
  existia antes da Function (login por e-mail/senha de um `Usuario`
  vinculado a `Cliente` tinha o mesmo problema), mas ficou mais exposto
  agora que qualquer pessoa com um CPF cadastrado pode se autenticar sem
  precisar de conta prévia. Fica registrado como débito técnico para uma
  próxima iteração (checar `ordemDeServico.clienteId == jwt.claim("cliente_id")`
  nos endpoints acessíveis por `CLIENTE`).
- **Negativo operacional**: a chave privada agora precisa estar sincronizada
  em dois lugares (K8s Secret da API e App Setting da Function) — se for
  rotacionada, precisa ser atualizada nos dois, ou tokens emitidos por um
  lado param de ser aceitos pelo outro.
