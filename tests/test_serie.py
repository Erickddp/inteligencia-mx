"""serie(id, fecha): los datos automáticos se leen por fecha, igual que los parámetros."""
from decimal import Decimal as D

import pytest

from timbra_reglas.motor import SinValor, dir_series, serie


def test_inpc_por_mes_o_por_fecha():
    assert serie("INPC", "2026-01") == D("143.588")
    assert serie("INPC", "2026-01-15") == D("143.588")          # una fecha cae en su mes
    assert isinstance(serie("INPC", "2026-01"), D)               # Decimal, nunca float


def test_sin_dato_avisa_y_no_inventa():
    with pytest.raises(SinValor, match="no hay valor"):
        serie("INPC", "2019-01")
    with pytest.raises(SinValor, match="no hay archivo"):
        serie("NO_EXISTE", "2026-01")


def test_la_carpeta_se_puede_apuntar(tmp_path, monkeypatch):
    (tmp_path / "inpc.yaml").write_text('valores:\n  "2030-01": {valor: "200.5"}\n', encoding="utf-8")
    monkeypatch.setenv("TIMBRA_REGLAS_SERIES", str(tmp_path))
    assert dir_series() == tmp_path
    assert serie("INPC", "2030-01-31") == D("200.5")
