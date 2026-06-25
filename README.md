[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/TPGyf4AW)
This is a simple example to demonstrate how stubs can be used as remote references in RPC systems. The example was extracted from (Tanenbaum and van Steen, 2025).

## Sobre o exemplo

Reproduz a Nota 4.8 (Figs. 4.20 (a)-(d)) do livro-texto. O servidor mantém um conjunto
de listas (`setOfLists`), cada uma identificada por um `listID`. O cliente nunca fala com a
lista diretamente: ele usa um *stub* (`DBClient`), que guarda o endereço do servidor e o
`listID` e, em cada método, empacota a requisição, manda pelo socket e desempacota a resposta.

O ponto demonstrado é que o stub funciona como uma **referência remota**: `client1` cria a
lista, acrescenta um dado e então envia o próprio stub (serializado com `pickle`) para
`client2`. O `client2` recebe uma cópia do stub e, ao chamar seus métodos, acaba operando na
**mesma** lista do servidor. A saída final é `['Client 1', 'Client 2']`.

## Arquivos

- `constRPC.py` — constantes do protocolo e a configuração de rede (lida de variáveis de ambiente, com defaults locais).
- `dbclient.py` — o stub `DBClient`: proxy local para uma lista que vive no servidor.
- `server.py` — o servidor que guarda as listas.
- `client.py` — processo cliente, capaz de enviar e receber objetos por socket.
- `run.py` — orquestra a execução: modo local (um processo por papel via `multiprocessing`) ou um papel por máquina via `--role`.

## Configuração (variáveis de ambiente)

| Variável | Default | Função |
|---|---|---|
| `RPC_SERVER_HOST` | `127.0.0.1` | endereço do servidor que os clientes acessam |
| `RPC_SERVER_PORT` | `50004` | porta do servidor |
| `RPC_CLIENT1_HOST` / `RPC_CLIENT1_PORT` | `127.0.0.1` / `50053` | endereço/porta do client1 |
| `RPC_CLIENT2_HOST` / `RPC_CLIENT2_PORT` | `127.0.0.1` / `50054` | endereço/porta do client2 |
| `RPC_SERVER_BIND_HOST` / `RPC_CLIENT_BIND_HOST` | `0.0.0.0` | interface em que servidor/cliente escutam |

Sem nenhuma variável definida, tudo aponta para `127.0.0.1` e o exemplo roda numa só máquina.

## Execução local (uma máquina)

```bash
python3 run.py --role local
```

Saída esperada:

```
['Client 1', 'Client 2']
```

## Execução distribuída (3 máquinas — AWS EC2)

Pré-requisitos: três instâncias EC2 na mesma VPC/sub-rede, com Python 3 instalado e o
*security group* liberando as portas TCP `50004`, `50053` e `50054` entre as instâncias.
Use os **IPs privados** das instâncias (válidos dentro da VPC); cada máquina tem um IP
diferente, e você os informa na hora de rodar, sem editar o código.

Como exemplo, suponha os IPs privados abaixo:

| Máquina | IP privado | Comando |
|---|---|---|
| servidor | `172.31.0.10` | `python3 run.py --role server` |
| client2 | `172.31.0.12` | `RPC_SERVER_HOST=172.31.0.10 python3 run.py --role client2` |
| client1 | `172.31.0.11` | `RPC_SERVER_HOST=172.31.0.10 RPC_CLIENT2_HOST=172.31.0.12 python3 run.py --role client1` |

Detalhes:

- O **servidor** não precisa saber o IP de ninguém: faz *bind* em `0.0.0.0:50004` e só escuta.
- O **client1** precisa do IP do servidor (para criar/popular a lista) e do IP do client2 (para enviar o stub).
- O **client2** precisa do IP do servidor. Note que `RPC_SERVER_HOST` é o **mesmo** nos dois
  clientes, e isso é proposital: o stub que o client1 envia carrega dentro de si o endereço do
  servidor, então esse endereço tem de ser alcançável também a partir do client2. Por isso usamos
  o IP privado do servidor na VPC, que vale nas três máquinas — se o client1 usasse `localhost`,
  o stub copiado apontaria o client2 para o loopback dele, e a referência quebraria.

Ordem de inicialização: **servidor → client2 → client1**. A saída `['Client 1', 'Client 2']`
aparece no terminal do client2.
