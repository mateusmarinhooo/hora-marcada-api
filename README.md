# Hora Marcada

Duas pessoas consultam a agenda e escolhem as 9h. Quem confirma primeiro fica com a vaga. Esta API cuida da consulta, da reserva e do cancelamento de atendimentos de uma hora para um profissional. Cada reserva recebe um código para cancelamento.

## Rodar no Windows

Com Python 3.13 instalado, baixe ou clone este repositório. Abra o PowerShell na pasta que contém `main.py` e execute:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn main:app --reload
~~~

Abra [a documentação interativa](http://127.0.0.1:8000/docs). O SQLite cria o arquivo da agenda na primeira execução.

## Experimente a regra de reserva

1. Em **GET /horarios**, selecione **Try it out**, informe uma data futura no formato AAAA-MM-DD e copie um horário livre.
2. Em **POST /reservas**, envie os campos `dia` e `horario` com os valores escolhidos. A resposta **201** traz o código da reserva.
3. Envie o mesmo pedido novamente. A resposta **409** informa que o horário já está ocupado.
4. Em **DELETE /reservas/{codigo}**, informe o código da primeira resposta. O retorno é **204**. Consulte a data outra vez para ver a vaga livre.

## Por que a vaga não duplica?

A consulta mostra a disponibilidade naquele instante. Entre consultar e confirmar, outra pessoa pode reservar. Por isso, a tabela tem uma restrição `UNIQUE (dia, horario)`. O próprio banco decide se a gravação pode acontecer. Quando o horário já existe, a API devolve o conflito para quem fez a segunda tentativa.

## Executar o teste

~~~powershell
.\.venv\Scripts\python -m unittest -v test_agenda
~~~

O teste usa um banco SQLite em memória. Ele verifica a disponibilidade, a recusa da segunda reserva, a contagem de registros e a liberação do horário após o cancelamento. Os atendimentos vão das 9h às 18h, com última entrada às 17h, no horário local do servidor.
