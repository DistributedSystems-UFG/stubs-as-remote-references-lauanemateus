# Respostas (campo de texto da tarefa)

## (a) Mecanismo demonstrado e generalização

Rodei o exemplo da Fig. 4.20 em uma única máquina, com os três processos (servidor,
client1 e client2) iniciados localmente. O resultado reproduz o cenário esperado: o
client2 imprime `['Client 1', 'Client 2']`.

O servidor guarda um conjunto de listas em `setOfLists`, cada uma com um identificador
inteiro (`listID`). Quem usa essas listas nunca conversa com elas diretamente: usa um
*stub*, que é o objeto `DBClient`. Esse stub carrega duas coisas — o endereço do servidor
(host e porta) e o `listID` da lista a que ele se refere — e implementa os métodos
`create`, `appendData` e `getValue`. Cada método só faz empacotar a requisição com
`pickle`, abrir um socket para o servidor, enviar, receber a resposta e desempacotar. Ou
seja, o stub é um procurador (proxy) local de um objeto que mora no espaço de endereçamento
do servidor.

A parte interessante está na Fig. 4.20(d). O client1 cria o stub, cria uma lista (recebe
`listID = 1`) e acrescenta `'Client 1'`. Em seguida ele serializa o stub inteiro com
`pickle` e o envia por socket para o client2. O client2 desserializa e fica com uma cópia
fiel do stub: mesmo host, mesma porta, mesmo `listID`. Quando o client2 chama
`appendData('Client 2')` e `getValue()` nessa cópia, as chamadas vão para o mesmo servidor
e mexem na mesma lista. Por isso a leitura final traz os dois elementos.

O que o exemplo mostra é o ponto da Nota 4.5/Fig. 4.10: passar uma referência para um objeto
remoto como parâmetro. Como em uma linguagem interpretada e portável (Python, Java) o stub
do cliente *é* a referência, copiar o stub para outro processo equivale a passar a referência
por valor — e, na prática, os dois lados passam a compartilhar o mesmo objeto remoto. Não há
um passo separado de *binding*: basta copiar o stub para o destinatário para que ele consiga
invocar o objeto do lado servidor. O stub age como uma referência global, porque leva consigo
tudo o que é preciso para alcançar o objeto: o endpoint e o identificador.

Sobre a generalização: qualquer objeto remoto pode ser exposto assim. O servidor mantém uma
tabela de objetos (aqui, `setOfLists` indexado por `listID`); o stub junta o endpoint, o
identificador do objeto e a lógica de *marshalling*; e distribuir a referência é apenas
copiar o stub. Esse é o alicerce dos sistemas de objetos distribuídos e de RMI (Java RMI,
CORBA): uma referência remota nada mais é que um stub que carrega o endereço do servidor mais
uma chave do objeto. Como o código do stub é portável, ele pode inclusive ser enviado para uma
máquina que nunca viu aquela classe e ser executado lá, sem registro prévio da interface — é a
observação do livro sobre copiar o código do stub no lugar de exigir binding explícito. O
mecanismo também escala para vários detentores: dá para entregar o stub a N processos, e todos
passam a operar sobre o mesmo objeto no servidor (o que, num sistema real, traz junto o problema
de contagem distribuída de referências para liberar o objeto). Os limites a observar são os de
sempre: ambos os lados precisam interpretar o formato serializado (protocolo de `pickle`,
layout compatível), desserializar objetos arbitrários é um risco de segurança, e o endereço
embutido no stub precisa continuar válido e alcançável onde quer que o stub vá parar.

## (c) Mudanças para as três máquinas e semântica das chamadas

As mudanças em relação ao código do livro foram concentradas em endereçamento e orquestração,
sem tocar na lógica do stub:

- Os endereços, que no livro são fixos (`'localhost'`, `''` e portas constantes), passaram a
  ser lidos de variáveis de ambiente em `constRPC.py`. Assim cada máquina recebe os IPs e
  portas reais sem precisar editar código. Os defaults continuam sendo `127.0.0.1`, então a
  versão local roda sem nenhuma configuração.
- O `Client` passou a fazer *bind* em `0.0.0.0` (todas as interfaces) em vez de `localhost`,
  para aceitar conexões vindas de outra máquina; o servidor já escuta numa interface
  configurável.
- A orquestração em processo único (`multiprocessing`) deu lugar a um seletor `--role`
  em `run.py`, de modo que o mesmo código roda como `server`, `client1` ou `client2` em três
  hosts separados. O modo local foi mantido.
- No ambiente AWS: três instâncias EC2 na mesma VPC/sub-rede, *security group* liberando as
  portas TCP usadas (50004, 50053, 50054) entre as instâncias, e os IPs privados das máquinas.
  A ordem de subida é servidor, depois client2 (que fica bloqueado escutando) e por fim client1.

Quanto à semântica, é preciso separar dois níveis.

No nível lógico, **não há diferença**. O mecanismo do stub é transparente: o client2 continua
recebendo uma cópia do stub e suas chamadas continuam caindo na mesma lista do servidor. A
saída é idêntica à do caso local (`['Client 1', 'Client 2']`). É exatamente a transparência de
distribuição de que o livro fala — o mesmo código serve tanto para processos na mesma máquina
quanto espalhados, porque o stub leva consigo o endpoint do servidor.

No nível de entrega e de falhas, porém, aparecem diferenças que ficavam escondidas no caso
local:

1. O endereço embutido no stub precisa ser **globalmente válido**. Localmente, todo endpoint é
   `127.0.0.1`, que vale em qualquer processo. Quando o stub viaja entre máquinas, o host que
   ele carrega (o endereço do servidor, definido pelo client1) tem de ser alcançável também a
   partir do client2. Se o client1 tivesse usado `localhost`, a cópia do stub apontaria o
   client2 para o *próprio* loopback dele, e não para o servidor — a referência quebraria. Por
   isso usamos o IP privado do servidor na VPC, que é válido nas três máquinas. Uma referência
   só é de fato "global" se o endpoint que ela carrega for alcançável de onde o stub parar.
2. A semântica de falhas do RPC passa a ser observável. No loopback, as chamadas praticamente
   nunca falham. Pela rede, podem se perder, duplicar, atrasar ou completar pela metade; um
   `connect` pode ser recusado ou estourar timeout; uma máquina pode cair no meio da chamada. O
   código do exemplo assume que um único `recv(1024)` traz a mensagem inteira e que a conexão
   sempre dá certo — suposições que valem no loopback, mas não numa rede sob carga. Ou seja, as
   garantias do tipo "no máximo uma vez" só ficam visíveis no caso distribuído.
3. Latência, ordenação e custo de *marshalling* são desprezíveis localmente e reais entre
   máquinas, e a hipótese de representações compatíveis (protocolo de `pickle`, layout) só
   importa quando as máquinas podem diferir.

Resumindo: do ponto de vista do programador as chamadas são as mesmas e a aplicação é
transparente; o que muda é que a versão distribuída expõe as questões de endereçamento e de
falha parcial que a versão local mantinha ocultas. É justamente o alerta do livro: referências
locais e remotas parecem iguais, mas a semântica subjacente não é, e esconder essa diferença
pode ser perigoso.
