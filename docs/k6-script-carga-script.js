import http from "k6/http";
import { check, sleep } from "k6";

// Uso:
//   k6 run -e BASE_URL=http://<host>:8080 docs/k6-script-carga-script.js
//
// Rampa gradual em vez de VUs fixos: o boot da JVM em modo padrão do Quarkus
// leva ~2min pra um pod novo ficar Ready, então uma carga instantânea (ex.:
// --vus 50 --duration 1m) satura as poucas réplicas existentes e termina
// antes do HPA conseguir escalar — o teste vira só timeout, sem mostrar
// escalonamento nenhum. As stages abaixo dão tempo real pro HPA reagir e
// pros pods novos entrarem, então dá pra ver REPLICAS subindo ao vivo no
// `kubectl get hpa -w` enquanto o teste ainda está rodando.
const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";
const LOGIN_EMAIL = __ENV.LOGIN_EMAIL || "admin@oficina.com.br";
const LOGIN_SENHA = __ENV.LOGIN_SENHA || "admin123";

export const options = {
  stages: [
    { duration: "30s", target: 30 }, // rampa inicial: começa a pressionar CPU
    { duration: "1m30s", target: 50 }, // segue subindo enquanto o HPA reage
    { duration: "2m", target: 50 }, // platô: dá tempo dos pods novos ficarem Ready e absorverem carga
    { duration: "30s", target: 0 }, // rampa de descida
  ],
};

// setup() roda uma única vez, antes da carga começar — não por VU/iteração.
// O valor retornado é entregue (uma cópia) para cada chamada de default().
export function setup() {
  const loginRes = http.post(
    `${BASE_URL}/api/usuarios/login`,
    JSON.stringify({ email: LOGIN_EMAIL, senha: LOGIN_SENHA }),
    { headers: { "Content-Type": "application/json" } }
  );

  const loginOk = check(loginRes, {
    "login: HTTP 200": (r) => r.status === 200,
  });

  if (!loginOk) {
    throw new Error(
      `Falha no login antes de iniciar a carga - HTTP ${loginRes.status}: ${loginRes.body}`
    );
  }

  const token = loginRes.json("access_token");
  return { token };
}

// default() roda repetidamente, para cada VU/iteração, durante toda a carga.
export default function (data) {
  const res = http.get(`${BASE_URL}/api/ordens?tamanho=20`, {
    headers: { Authorization: `Bearer ${data.token}` },
  });

  check(res, {
    "listagem: HTTP 200": (r) => r.status === 200,
    "listagem: corpo tem itens": (r) => {
      try {
        return Array.isArray(r.json("itens"));
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1);
}
