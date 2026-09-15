# ADR-001 — Padrão de comunicação: REST síncrono + Event Bus interno assíncrono

- **Status**: Aceito

## Contexto

O sistema tem dois tipos de comunicação bem distintos:

1. **Cliente ↔ API**: toda a interação externa (Postman, front-end, a
   Function de autenticação indiretamente via JWT) é requisição/resposta
   clássica.
2. **Dentro do monólito, entre módulos**: por exemplo, ao abrir uma Ordem de
   Serviço (`AbrirOrdemDeServicoUseCaseImpl`), o módulo `operacional`
   precisa avisar o módulo `notificacao` para notificar o cliente — sem
   que a resposta HTTP do `POST /api/ordens` fique esperando o envio da
   notificação terminar.

## Decisão

- **Comunicação externa**: **REST sobre HTTP/JSON**, síncrona, exposta via
  o API Gateway (Traefik). Sem GraphQL nem gRPC — o domínio é
  CRUD-orientado com poucas relações profundas por requisição, e REST é
  suficiente e mais simples de documentar (OpenAPI/Swagger já gerado pelo
  Quarkus) e testar (a collection Postman/Newman já cobre esse contrato).
- **Comunicação interna entre módulos**: **Event Bus do Vert.x**
  (`io.vertx.core.eventbus.EventBus`), assíncrono, dentro do mesmo processo
  JVM. Exemplo real: `AbrirOrdemDeServicoUseCaseImpl` publica o evento
  `OrdemServicoAberta` depois de persistir a OS; o módulo de notificação
  consome esse evento de forma desacoplada (ver
  [`diagrama-sequencia-abertura-os.mmd`](diagrama-sequencia-abertura-os.mmd)).
  Não é fila persistente nem sistema de mensageria externo (Kafka/RabbitMQ)
  — é *in-process*, então não sobrevive a um restart do pod nem escala
  entre réplicas; isso é aceitável porque o consumidor (notificação) é
  best-effort e não faz parte da transação de negócio principal.
- **Comunicação entre a Function de CPF e a API principal**: **nenhuma
  chamada direta** — a Function consulta o mesmo banco e emite um JWT que a
  API valida de forma independente (ver
  [RFC-003](rfc-003-estrategia-de-autenticacao.md)). Não há acoplamento de
  rede entre os dois serviços.

## Consequências

- **Positivo**: desacoplamento leve entre "salvar a OS" e "notificar o
  cliente" sem precisar de infraestrutura de mensageria externa — reduz
  custo e complexidade operacional para o volume atual do domínio.
- **Positivo**: REST + OpenAPI mantém a barreira de entrada baixa para
  consumidores externos (Postman, Swagger UI, front-end futuro).
- **Negativo/limite conhecido**: o Event Bus in-process **não escala
  horizontalmente** — se o Deployment tiver múltiplas réplicas (via HPA), o
  evento só é visto pela réplica que processou a requisição original, o que
  é suficiente hoje porque o consumidor está no mesmo pod, mas impede, por
  exemplo, que um worker dedicado e separado processe notificações no
  futuro sem mudar essa decisão.
- **Negativo/limite conhecido**: eventos publicados não são persistidos —
  se o pod cair entre a publicação do evento e o consumidor processá-lo, a
  notificação é perdida silenciosamente. Aceitável para notificação (não
  crítica), não seria para eventos que afetam o estado transacional do
  negócio.
