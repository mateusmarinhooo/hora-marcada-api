import sqlite3
import unittest
from datetime import date, timedelta
from unittest.mock import patch
from uuid import UUID

from fastapi import HTTPException

import main


class TestAgenda(unittest.IsolatedAsyncioTestCase):
    async def test_reserva_duplicada_e_cancelamento(self):
        # Cada teste tem sua própria agenda, sem tocar no arquivo de quem usa a API.
        uri = f"file:teste-agenda-{id(self)}?mode=memory&cache=shared"
        conectar = sqlite3.connect
        ancora = conectar(uri, uri=True)
        self.addCleanup(ancora.close)
        with patch.object(main.sqlite3, "connect", side_effect=lambda _: conectar(uri, uri=True)):
            async with main.iniciar(main.app):
                dia = date.today() + timedelta(days=1)
                pedido = main.PedidoDeReserva(dia=dia, horario="09:00")
                self.assertIn("09:00", main.horarios_livres(dia))
                reserva = main.reservar(pedido)
                self.assertNotIn("09:00", main.horarios_livres(dia))

                with self.assertRaises(HTTPException) as conflito:
                    main.reservar(pedido)
                self.assertEqual(conflito.exception.status_code, 409)
                total = ancora.execute("SELECT count(*) FROM reservas").fetchone()[0]
                self.assertEqual(total, 1)

                resposta = main.cancelar(UUID(reserva["codigo"]))
                self.assertEqual(resposta.status_code, 204)
                self.assertIn("09:00", main.horarios_livres(dia))
                nova = main.reservar(pedido)
                self.assertNotEqual(nova["codigo"], reserva["codigo"])
