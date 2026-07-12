import logging
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

EXPORT_SCRIPT_REL = "Scripts/Resource Exporters/ExportAllStringsJSON.csx"
IMPORT_SCRIPT_REL = "Scripts/Resource Importers/ImportAllStringsJSON.csx"


def _find_cli(directory: str) -> Optional[Path]:
    """Return the path to the UMT CLI executable inside the directory."""
    d = Path(directory)
    if not d.is_dir():
        return None
    exe_name = "UndertaleModCli.exe" if platform.system().lower() == "windows" else "UndertaleModCli"
    candidate = d / exe_name
    return candidate if candidate.exists() and candidate.is_file() else None


def _find_export_script(directory: str) -> Optional[Path]:
    """Return the path to ExportAllStringsJSON.csx inside the directory."""
    d = Path(directory)
    if not d.is_dir():
        return None
    candidate = d / EXPORT_SCRIPT_REL
    return candidate if candidate.exists() and candidate.is_file() else None


def _find_import_script(directory: str) -> Optional[Path]:
    """Return the path to ImportAllStringsJSON.csx inside the directory."""
    d = Path(directory)
    if not d.is_dir():
        return None
    candidate = d / IMPORT_SCRIPT_REL
    return candidate if candidate.exists() and candidate.is_file() else None


def _run_umt_script(
    cli: Path,
    data_win: Path,
    script: Path,
    output_win: Path,
    stdin_input: str,
    timeout: int,
) -> tuple[bool, str, Optional[str]]:
    """
    Execute UMT CLI with a script, sending input via stdin.

    Returns (success, message, stdout_text).
    """
    cmd = [
        str(cli),
        "load",
        str(data_win),
        "--scripts",
        str(script),
        "--output",
        str(output_win),
    ]
    logger.info("UMT cmd: %s", " ".join(cmd))
    logger.info("UMT stdin: %s", repr(stdin_input.rstrip("\n")))

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = proc.communicate(input=stdin_input, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return False, "El proceso UMT tardó demasiado y fue terminado.", None
    except Exception as e:
        logger.exception("Error al ejecutar UMT")
        return False, f"Error inesperado: {e}", None

    if proc.returncode != 0:
        err = (stderr or stdout or f"Código de salida: {proc.returncode}").strip()
        logger.warning("UMT falló (rc=%s): %s", proc.returncode, err)
        return False, f"UMT CLI falló:\n{err}", stdout

    return True, "OK", stdout


def is_umt_configured(directory: str) -> bool:
    """Check if a UMT directory contains the CLI executable and export script."""
    if not directory:
        return False
    return _find_cli(directory) is not None and _find_export_script(directory) is not None


def umt_status(directory: str) -> tuple[bool, bool, str]:
    """Return (cli_ok, script_ok, extra_info) for the settings UI."""
    if not directory:
        return False, False, "No hay ruta configurada"
    d = Path(directory)
    if not d.exists():
        return False, False, "La carpeta no existe"
    if not d.is_dir():
        return False, False, "La ruta no es una carpeta"

    cli = _find_cli(directory)
    export = _find_export_script(directory)
    import_ = _find_import_script(directory)

    parts = []
    parts.append(f"CLI: {'✓' if cli else '✗'}")
    parts.append(f"Exportar: {'✓' if export else '✗'}")
    parts.append(f"Importar: {'✓' if import_ else '✗'}")
    return cli is not None, export is not None, " | ".join(parts)


def verify_umt(directory: str) -> tuple[bool, str]:
    """Run `--version` on UMT CLI to verify it's a valid executable."""
    cli = _find_cli(directory)
    if not cli:
        return False, "No se encontró UndertaleModCli en la carpeta"
    try:
        result = subprocess.run(
            [str(cli), "--version"],
            capture_output=True, text=True, timeout=15,
        )
        version = (result.stdout or result.stderr).strip()
        if version:
            return True, version
        return True, "Versión desconocida"
    except subprocess.TimeoutExpired:
        return False, "El comando tardó demasiado"
    except PermissionError:
        return False, "Permiso denegado"
    except Exception as e:
        return False, f"Error: {e}"


def extract_strings(
    directory: str,
    data_win_path: str,
    output_path: str,
    timeout: int = 120,
) -> tuple[bool, str]:
    """
    Extract strings from data.win using UMT CLI with ExportAllStringsJSON.csx.

    The CLI loads the data.win, executes the export script, and the script
    expects the output JSON path via stdin. We send it automatically.

    Returns (success, message).
    """
    cli = _find_cli(directory)
    if not cli:
        return False, "No se encontró UndertaleModCli en la carpeta configurada"

    script = _find_export_script(directory)
    if not script:
        return False, (
            f"No se encontró el script de exportación:\n"
            f"{EXPORT_SCRIPT_REL}\n\n"
            f"Asegúrate de que la carpeta contiene la instalación completa de UMT."
        )

    dw = Path(data_win_path)
    if not dw.exists():
        return False, f"data.win no encontrado: {data_win_path}"

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # El script espera la ruta del JSON por stdin
    stdin_input = f"{output_path}\n"

    success, msg, stdout = _run_umt_script(
        cli=cli,
        data_win=dw,
        script=script,
        output_win=out.parent / "__dts_temp_umt_output.win",
        stdin_input=stdin_input,
        timeout=timeout,
    )

    if success:
        if out.exists() and out.stat().st_size > 0:
            logger.info("Extracción exitosa: %s", output_path)
            _cleanup_temp_win(out.parent)
            return True, f"Strings extraídos ({out.stat().st_size} bytes)"
        else:
            _cleanup_temp_win(out.parent)
            return False, (
                f"UMT terminó sin error pero no se encontró el archivo de salida.\n"
                f"Verifica que la ruta del script sea correcta.\n"
                f"stdout: {(stdout or '').strip()}"
            )

    _cleanup_temp_win(out.parent)
    return False, msg


def replace_strings(
    directory: str,
    data_win_path: str,
    strings_json_path: str,
    output_win_path: str,
    timeout: int = 120,
) -> tuple[bool, str]:
    """
    Replace strings in data.win using UMT CLI with ImportAllStringsJSON.csx.

    Falls back to --replace-strings flag if the import script is not found.

    Returns (success, message).
    """
    cli = _find_cli(directory)
    if not cli:
        return False, "No se encontró UndertaleModCli en la carpeta configurada"

    dw = Path(data_win_path)
    if not dw.exists():
        return False, f"data.win no encontrado: {data_win_path}"

    sj = Path(strings_json_path)
    if not sj.exists():
        return False, f"strings.json no encontrado: {strings_json_path}"

    out = Path(output_win_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Try import script first
    import_script = _find_import_script(directory)
    if import_script:
        stdin_input = f"{strings_json_path}\n"
        success, msg, _ = _run_umt_script(
            cli=cli,
            data_win=dw,
            script=import_script,
            output_win=out,
            stdin_input=stdin_input,
            timeout=timeout,
        )
        if success:
            if out.exists() and out.stat().st_size > 0:
                logger.info("Reemplazo exitoso con script: %s", output_win_path)
                return True, f"Strings reemplazados ({out.stat().st_size} bytes)"
            else:
                return False, "UMT terminó sin error pero no generó el archivo de salida"
        return False, msg

    # Fallback: --replace-strings flag
    logger.info("Import script no encontrado, usando --replace-strings")
    try:
        result = subprocess.run(
            [str(cli), "--replace-strings", str(dw), str(sj), str(out)],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0:
            if out.exists() and out.stat().st_size > 0:
                return True, f"Strings reemplazados ({out.stat().st_size} bytes)"
            else:
                return False, "UMT terminó sin error pero no generó el archivo de salida"
        else:
            err = (result.stderr or result.stdout or f"Código: {result.returncode}").strip()
            return False, f"UMT CLI falló:\n{err}"
    except subprocess.TimeoutExpired:
        return False, "El reemplazo tardó demasiado."
    except Exception as e:
        logger.exception("Error inesperado al ejecutar UMT")
        return False, f"Error inesperado: {e}"


def import_strings(
    directory: str,
    data_win_path: str,
    strings_json_path: str,
    output_win_path: str,
    timeout: int = 120,
) -> tuple[bool, str]:
    """
    Import translated strings into a data.win using UMT CLI with ImportAllStringsJSON.csx.

    The CLI loads the data.win, runs the import script, and the script expects
    the path to the translated JSON via stdin. We send it automatically.

    Returns (success, message).
    """
    return replace_strings(
        directory=directory,
        data_win_path=data_win_path,
        strings_json_path=strings_json_path,
        output_win_path=output_win_path,
        timeout=timeout,
    )


def _cleanup_temp_win(directory: Path) -> None:
    """Remove temp .win files created during script execution."""
    for f in directory.glob("__dts_temp_umt_*.win"):
        try:
            f.unlink()
        except OSError:
            logger.warning("No se pudo eliminar temp: %s", f)
