# ADR-002 — Uso de HorizontalPodAutoscaler (HPA) para a API

- **Status**: Aceito

## Contexto

O enunciado da Fase 3 exige "Cluster Kubernetes com escalabilidade". A
`oficina-api` roda como um `Deployment` único no AKS, atrás do API Gateway
(Traefik) — precisa suportar picos de carga (ex.: vários atendentes abrindo
OS ao mesmo tempo, ou uma leva de testes de carga/Newman) sem degradar
latência, e voltar a um número menor de réplicas quando a carga cai, para
não gastar recursos do cluster à toa.

## Decisão

Usar um `HorizontalPodAutoscaler` (`autoscaling/v2`) nativo do Kubernetes,
definido em [`k8s/app/hpa.yaml`](../../k8s/app/hpa.yaml):

```yaml
minReplicas: 1
maxReplicas: 8
metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Escala com base em **utilização de CPU** (não memória, nem métricas
customizadas). Alternativas descartadas:

- **KEDA / autoscaling por métrica customizada** (ex.: requisições/s via
  New Relic ou fila): mais preciso para picos de tráfego HTTP puro, mas
  adiciona um componente extra no cluster (KEDA precisa ser instalado à
  parte) só pra um ganho marginal, dado que a carga de trabalho da API é
  majoritariamente CPU-bound (validações, serialização JSON, JDBC) — CPU já
  é um proxy razoável de carga.
- **Scale manual** (ajustar `replicas` via `kubectl`/CI): descartado por
  não atender ao requisito de escalabilidade automática, e por depender de
  intervenção humana durante um pico real.

`minReplicas: 1` (não zero) porque o requisito não pede scale-to-zero, e
zero réplicas significaria indisponibilidade total até o primeiro pod
subir — inaceitável para uma API que também é usada como uptime/healthcheck
no dashboard do New Relic. `maxReplicas: 8` foi dimensionado para o node
pool atual (`Standard_D2s_v3`, 1 nó, 2 vCPU) sem esgotar CPU/memória do nó
para outros pods do cluster (Traefik, New Relic Infrastructure Agent, etc.)
— ver [`diagrama-componentes.mmd`](diagrama-componentes.mmd).

## Consequências

- **Positivo**: validado em produção durante esta fase — uma execução da
  collection Newman completa contra o cluster real fez o HPA escalar de 1
  para 8 réplicas automaticamente, e voltar a 1 depois que a carga cessou,
  sem intervenção manual.
- **Positivo**: `startupProbe`/`readinessProbe` (ver
  [ADR sobre observabilidade não numerado — ver TODO.md, seção
  Monitoramento](../../TODO.md)) garantem que uma réplica nova só recebe
  tráfego depois de estar de fato pronta (Flyway + seed concluídos),
  evitando que o HPA "esconda" um problema de inicialização lenta atrás de
  escalonamento.
- **Negativo/risco conhecido**: métrica de CPU não captura gargalos de I/O
  (ex.: banco de dados lento, mesmo com CPU da API ociosa) — nesse cenário
  o HPA não escalaria a API, porque o gargalo não é dela. Fora do escopo
  desta ADR corrigir (seria resolvido monitorando o Postgres separadamente,
  não escalando a API).
- **Negativo**: como o node pool tem apenas 1 nó, escalar até 8 réplicas de
  pod não necessariamente significa mais capacidade de CPU real disponível
  — o HPA escala pods, não nós; escalonamento de nós (Cluster Autoscaler)
  não foi configurado nesta fase por estar fora do escopo obrigatório do
  desafio.
