"""El gobierno del repo es parte del producto: licencias, aviso, dueños, plantillas y changelog."""
import importlib.util
import shutil

import yaml

from conftest import BASE, RAIZ


def release():
    spec = importlib.util.spec_from_file_location("release", RAIZ / "scripts" / "release.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_archivos_de_gobierno_existen():
    for f in ("LICENSE", "LICENSE-DATOS", "LICENCIAS.md", "AVISO.md", "README.md", "CONTRIBUTING.md", "CHANGELOG.md",
              ".github/CODEOWNERS", ".github/PULL_REQUEST_TEMPLATE.md", ".github/ISSUE_TEMPLATE/cambio_de_ley.yml",
              ".github/ISSUE_TEMPLATE/error_en_calculo.yml", ".github/workflows/dco.yml", "docs/ficha_regla.md"):
        assert (RAIZ / f).is_file(), f


def test_licencias():
    assert "Apache License" in (RAIZ / "LICENSE").read_text(encoding="utf-8")
    assert "Attribution 4.0 International" in (RAIZ / "LICENSE-DATOS").read_text(encoding="utf-8")


def test_aviso_en_readme():
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert "no asesoría fiscal" in readme and "AVISO.md" in readme
    assert "no es asesoría fiscal" in (RAIZ / "AVISO.md").read_text(encoding="utf-8").lower() or "No es asesoría fiscal" in (RAIZ / "AVISO.md").read_text(encoding="utf-8")


def test_codeowners_cubre_base_motor_scripts_y_workflows():
    reglas = {}
    for linea in (RAIZ / ".github" / "CODEOWNERS").read_text(encoding="utf-8").splitlines():
        if linea.strip() and not linea.startswith("#"):
            ruta, *duenos = linea.split()
            reglas[ruta] = duenos
    for ruta in ("/base/", "/timbra_reglas/", "/scripts/", "/.github/", "/.claude/"):
        assert reglas.get(ruta) == ["@Erickddp"], ruta


def test_plantillas_son_yaml_validos_y_piden_lo_esencial():
    cambio = yaml.safe_load((RAIZ / ".github/ISSUE_TEMPLATE/cambio_de_ley.yml").read_text(encoding="utf-8"))
    error = yaml.safe_load((RAIZ / ".github/ISSUE_TEMPLATE/error_en_calculo.yml").read_text(encoding="utf-8"))
    assert {"publicacion", "fecha", "enlace", "parametros"} <= {b["id"] for b in cambio["body"] if "id" in b}
    assert {"caso", "esperado", "obtenido", "fuente"} <= {b["id"] for b in error["body"] if "id" in b}
    pr = (RAIZ / ".github/PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    for clave in ("Fuente primaria", "Casos agregados", "**A**", "**B**", "Firmas que se caen"):
        assert clave in pr


def test_contributing_menciona_dco_y_fuentes():
    c = (RAIZ / "CONTRIBUTING.md").read_text(encoding="utf-8")
    for clave in ("Signed-off-by", "git commit -s", "DOF", "CONASAMI", "ficha_regla"):
        assert clave in c


def test_changelog_se_genera_y_reemplaza(tmp_path):
    rel = release()
    shutil.copy(RAIZ / "CHANGELOG.md", tmp_path / "CHANGELOG.md")
    dif = {k: [] for k in ("param_nuevos", "param_quitados", "valor_cambiado", "estado_cambiado", "vigencia_cambiada",
                           "tramos_nuevos", "reglas_nuevas", "reglas_quitadas", "regla_estado")}
    dif["valor_cambiado"] = ["UMA_DIARIA desde 2026-02-01"]
    dif["tramos_nuevos"] = ["UMA_DIARIA desde 2027-02-01 (vigente)"]
    rel.escribe_changelog(tmp_path, rel.entrada_changelog("0.5.0", dif, "90 pasan", "2026-12-01"), "0.5.0")
    t = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert t.index("## [v0.5.0]") < t.index("## [v0.4.1]")
    assert "UMA_DIARIA desde 2026-02-01" in t and "firmas que se caen" in t
    rel.escribe_changelog(tmp_path, rel.entrada_changelog("0.5.0", dif, "91 pasan", "2026-12-02"), "0.5.0")
    t2 = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert t2.count("## [v0.5.0]") == 1 and "91 pasan" in t2 and "## [v0.4.1]" in t2


def test_tag_exige_entrada_de_changelog(tmp_path):
    spec = importlib.util.spec_from_file_location("verificar_tag", RAIZ / "scripts" / "verificar_tag.py")
    vt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vt)
    (tmp_path / "base").mkdir()
    (tmp_path / "timbra_reglas").mkdir()
    for f in ("parametros.yaml", "reglas.yaml"):
        shutil.copy(BASE / f, tmp_path / "base" / f)
    shutil.copy(RAIZ / "timbra_reglas" / "motor.py", tmp_path / "timbra_reglas" / "motor.py")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    tag_actual = f"v{vt.versiones(tmp_path)['motor.py']}"
    assert any("CHANGELOG" in e for e in vt.verifica(tag_actual, tmp_path))
    (tmp_path / "CHANGELOG.md").write_text(f"# Changelog\n\n## [{tag_actual}] - x\n", encoding="utf-8")
    assert vt.verifica(tag_actual, tmp_path) == []


def test_skill_aportar_regla_es_valida_y_solo_cita_lo_que_existe():
    import re
    texto = (RAIZ / ".claude" / "skills" / "aportar-inteligencia-mx" / "SKILL.md").read_text(encoding="utf-8")
    cab = yaml.safe_load(texto.split("---")[1])
    assert cab["name"] == "aportar-inteligencia-mx" and len(cab["description"]) > 60
    for s in set(re.findall(r"scripts/(\w+\.py)", texto)):
        assert (RAIZ / "scripts" / s).is_file(), s
    for f in set(re.findall(r"`(docs/[\w_]+\.md|CONTRIBUTING\.md|AVISO\.md)`", texto)):
        assert (RAIZ / f).is_file(), f
