"""Hora Marcada: uma agenda para um profissional, no horário local.

Para abrir a agenda, execute na pasta do projeto:
    python -m pip install fastapi uvicorn
    python -m uvicorn main:app --reload
Abra http://127.0.0.1:8000/docs para experimentar.
"""
from contextlib import asynccontextmanager, closing
from datetime import date, datetime, time
from pathlib import Path
import sqlite3
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

BANCO = Path(__file__).with_name("agenda.sqlite3")
HORARIOS_DE_ATENDIMENTO = [f"{hora:02d}:00" for hora in range(9, 18)]


@asynccontextmanager
async def iniciar(app: FastAPI):
    with closing(sqlite3.connect(BANCO)) as banco, banco:
        banco.execute("""
            CREATE TABLE IF NOT EXISTS reservas (
                codigo TEXT PRIMARY KEY,
                dia TEXT NOT NULL,
                horario TEXT NOT NULL,
                UNIQUE (dia, horario)
            )
        """)
    yield


app = FastAPI(title="Hora Marcada", lifespan=iniciar,
              description="Agenda de demonstração para um profissional. Sessões de uma hora, das 9h às 18h, no horário local.")


class PedidoDeReserva(BaseModel):
    dia: date
    horario: str


def horario_ainda_nao_passou(dia: date, horario: str) -> bool:
    inicio_do_atendimento = datetime.combine(dia, time.fromisoformat(horario))
    return inicio_do_atendimento > datetime.now()


@app.get("/horarios", summary="Ver horários livres em uma data")
def horarios_livres(dia: date):
    """Escolha uma data. Se a lista vier vazia, tente outro dia."""
    with closing(sqlite3.connect(BANCO)) as banco:
        linhas = banco.execute("SELECT horario FROM reservas WHERE dia = ?", (dia.isoformat(),))
        horarios_ocupados = {horario for (horario,) in linhas}
    
    return [
        horario for horario in HORARIOS_DE_ATENDIMENTO
        if horario not in horarios_ocupados and horario_ainda_nao_passou(dia, horario)
    ]


@app.post("/reservas", status_code=201, summary="Reservar um horário")
def reservar(pedido: PedidoDeReserva):
    if pedido.horario not in HORARIOS_DE_ATENDIMENTO:
        raise HTTPException(422, "Os atendimentos começam de hora em hora, das 09:00 às 17:00. Escolha um desses horários.")
    if not horario_ainda_nao_passou(pedido.dia, pedido.horario):
        raise HTTPException(422, "Esse horário já passou. Consulte a agenda e escolha um horário futuro.")
    codigo = str(uuid4())
    with closing(sqlite3.connect(BANCO)) as banco, banco:
        # Duas pessoas podem ver a mesma vaga. O banco confirma só a primeira reserva.
        registro = banco.execute("""
            INSERT INTO reservas (codigo, dia, horario) VALUES (?, ?, ?)
            ON CONFLICT (dia, horario) DO NOTHING
        """, (codigo, pedido.dia.isoformat(), pedido.horario))
        if registro.rowcount == 0:
            raise HTTPException(
                409,
                f"O horário das {pedido.horario} de {pedido.dia:%d/%m} já foi reservado. "
                "Consulte a agenda para escolher outro."
            )
    return {
        "dia": pedido.dia,
        "horario": pedido.horario,
        "codigo": codigo,
        "mensagem": (
            f"Reserva confirmada para {pedido.dia:%d/%m/%Y} às {pedido.horario}. "
            "Guarde este código para cancelar se seus planos mudarem."
        ),
    }


@app.delete("/reservas/{codigo}", status_code=204, summary="Cancelar com o código da reserva")
def cancelar(codigo: UUID):
    with closing(sqlite3.connect(BANCO)) as banco, banco:
        registro = banco.execute("DELETE FROM reservas WHERE codigo = ?", (str(codigo),))
        if registro.rowcount == 0:
            raise HTTPException(404, "Não encontrei essa reserva. Confira o código informado.")
    return Response(status_code=204)
