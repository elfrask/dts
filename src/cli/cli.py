import logging
import sys
from pathlib import Path

import click

from src.config.defaults import (
    DEFAULT_PROMPT,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_APP_CONFIG_FILE,
)
from src.config.settings import (
    load_app_settings,
    save_app_settings,
    load_project,
    save_project,
)
from src.io.file_loader import (
    load_strings,
    load_translation_dict,
    load_json,
    ensure_json,
)
from src.io.file_writer import (
    write_strings,
    write_translation_dict,
    write_json,
)
from src.io.formats import ProjectConfig, AppConfig, Project, ProviderType, ProviderKeys
from src.processors.matcher import (
    generate_input,
    apply_strings,
    merge_dicts,
    manual_generate,
    manual_apply,
)
from src.processors.normalizer import clean_normalice_new, clean_normalice
from src.processors.cleaner import clean_values, clean_void
from src.core.provider import create_provider
from src.core.translator import use_translate

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--project-dir", "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Project directory (default: current directory)",
)
@click.pass_context
def cli(ctx: click.Context, project_dir: str) -> None:
    ctx.ensure_object(dict)
    app_config = load_app_settings()
    project = load_project(Path(project_dir))
    ctx.obj["app_config"] = app_config
    ctx.obj["project"] = project


@cli.command("input-generate")
@click.pass_context
def cmd_input_generate(ctx: click.Context) -> None:
    project: Project = ctx.obj["project"]

    strings = load_strings(project.strings_file_path)
    result = generate_input(strings)
    write_translation_dict(project.input_file_path, result)
    click.echo(f"Input file generated: {project.input_file_path}")


@cli.command("run")
@click.option("--chunk-size", type=int, default=None, help="Chunk size override")
@click.pass_context
def cmd_run(ctx: click.Context, chunk_size: int | None) -> None:
    project: Project = ctx.obj["project"]
    app_config: AppConfig = ctx.obj["app_config"]

    provider = create_provider(app_config, project.config)

    if not provider.is_available():
        click.echo("Provider is not available. Check configuration.", err=True)
        sys.exit(1)

    if chunk_size:
        project.config.chunk_size = chunk_size

    ensure_json(project.output_file_path)

    use_translate(
        provider=provider,
        config=project.config,
        input_path=project.input_file_path,
        output_path=project.output_file_path,
    )

    click.echo(f"Translation saved to: {project.output_file_path}")


@cli.command("apply")
@click.pass_context
def cmd_apply(ctx: click.Context) -> None:
    project: Project = ctx.obj["project"]

    strings = load_strings(project.strings_file_path)
    translations = load_translation_dict(project.normalize_file_path)
    result = apply_strings(strings, translations)

    write_strings(project.result_file_path, result)
    click.echo(f"Applied to: {project.result_file_path}")


@cli.command("fix")
@click.pass_context
def cmd_fix(ctx: click.Context) -> None:
    project: Project = ctx.obj["project"]

    strings = load_strings(project.result_file_path)
    translations = load_translation_dict(project.normalize_file_path)
    result = apply_strings(strings, translations, fix_mode=True)

    write_strings(project.result_file_path, result)
    click.echo(f"Fixed: {project.result_file_path}")


@cli.command("normalice")
@click.option("--secure", is_flag=True, help="Remove accents and special chars")
@click.option("--old", is_flag=True, help="Use deprecated normalizer")
@click.pass_context
def cmd_normalice(ctx: click.Context, secure: bool, old: bool) -> None:
    project: Project = ctx.obj["project"]

    ensure_json(project.output_file_path)
    data = load_json(project.output_file_path)

    if old:
        result = clean_normalice(data)
    else:
        result = clean_normalice_new(data, secure=secure)

    write_json(project.normalize_file_path, result)
    click.echo(f"Normalized: {project.normalize_file_path}")


@cli.command("normalice-old")
@click.pass_context
def cmd_normalice_old(ctx: click.Context) -> None:
    ctx.invoke(cmd_normalice, secure=False, old=True)


@cli.command("voids")
@click.pass_context
def cmd_voids(ctx: click.Context) -> None:
    project: Project = ctx.obj["project"]

    ensure_json(project.output_file_path)
    data = load_json(project.output_file_path)
    original = load_json(project.input_file_path)

    result = clean_void(data, original)
    write_json(project.output_file_path, result)
    click.echo("Voids cleaned")


@cli.command("clean")
@click.pass_context
def cmd_clean(ctx: click.Context) -> None:
    project: Project = ctx.obj["project"]

    ensure_json(project.output_file_path)
    data = load_json(project.output_file_path)

    result = clean_values(data)
    write_json(project.output_file_path, result)
    click.echo("Keys cleaned")


@cli.command("merge")
@click.pass_context
def cmd_merge(ctx: click.Context) -> None:
    project: Project = ctx.obj["project"]

    original = load_json(project.input_file_path)
    overlay = load_json(project.output_file_path)

    result = merge_dicts(original, overlay)
    write_json(project.output_file_path, result)
    click.echo("Merged")


@cli.command("pull-manual")
@click.pass_context
def cmd_pull_manual(ctx: click.Context) -> None:
    project: Project = ctx.obj["project"]

    original = load_translation_dict(project.input_file_path)
    ensure_json(project.output_file_path)
    translated = load_translation_dict(project.output_file_path)

    result = manual_generate(original, translated)
    write_translation_dict(project.manual_file_path, result)
    click.echo(f"Manual edit file: {project.manual_file_path}")


@cli.command("apply-manual")
@click.pass_context
def cmd_apply_manual(ctx: click.Context) -> None:
    project: Project = ctx.obj["project"]

    ensure_json(project.output_file_path)
    current = load_translation_dict(project.output_file_path)
    manual = load_translation_dict(project.manual_file_path)

    result = manual_apply(current, manual)
    write_translation_dict(project.output_file_path, result)
    click.echo("Manual edits applied")


@cli.command("view")
@click.pass_context
def cmd_view(ctx: click.Context) -> None:
    project: Project = ctx.obj["project"]

    try:
        original = load_json(project.input_file_path)
    except FileNotFoundError:
        click.echo("No input file found")
        return

    try:
        translated = load_json(project.output_file_path)
    except FileNotFoundError:
        translated = {}

    total = len(original)
    done = len(translated)
    missing = total - done

    click.echo(f"Total dialogs: {total}")
    click.echo(f"Translated:  {done}")
    click.echo(f"Remaining:   {missing}")


@cli.command("settings")
@click.option("--provider", type=click.Choice(["gemini", "ollama"]), help="Set provider")
@click.option("--model", type=str, help="Set model name")
@click.option("--chunk-size", type=int, help="Set chunk size")
@click.option("--show", is_flag=True, help="Show current settings")
@click.pass_context
def cmd_settings(
    ctx: click.Context,
    provider: str | None,
    model: str | None,
    chunk_size: int | None,
    show: bool,
) -> None:
    project: Project = ctx.obj["project"]
    app_config: AppConfig = ctx.obj["app_config"]

    if show:
        click.echo(f"Provider:     {project.config.provider.value}")
        click.echo(f"Model:        {project.config.model}")
        click.echo(f"Chunk size:   {project.config.chunk_size}")
        click.echo(f"Project dir:  {project.directory}")
        gemini_keys = app_config.get_active_keys("gemini")
        click.echo(f"API keys:     {len(gemini_keys)} configured")
        return

    changed = False
    if provider:
        project.config.provider = ProviderType(provider)
        changed = True
    if model:
        project.config.model = model
        changed = True
    if chunk_size:
        project.config.chunk_size = chunk_size
        changed = True

    if changed:
        save_project(project)
        click.echo("Settings saved")


@cli.command("config")
@click.option("--add-key", type=str, help="Add a Gemini API key")
@click.option("--ollama-host", type=str, help="Set Ollama host")
@click.option("--ollama-timeout", type=int, help="Set Ollama timeout")
@click.option("--show", is_flag=True, help="Show app config")
@click.pass_context
def cmd_config(
    ctx: click.Context,
    add_key: str | None,
    ollama_host: str | None,
    ollama_timeout: int | None,
    show: bool,
) -> None:
    app_config: AppConfig = ctx.obj["app_config"]

    if show:
        for pname, pkeys in app_config.providers.items():
            enabled = sum(1 for k in pkeys.keys if k.enabled)
            total = len(pkeys.keys)
            click.echo(f"{pname}: {enabled}/{total} keys active")
        click.echo(f"Ollama host:    {app_config.ollama.host}:{app_config.ollama.port}")
        click.echo(f"Ollama timeout: {app_config.ollama.timeout}")
        click.echo(f"UMT CLI:        {app_config.umt.cli_path or '(not set)'}")
        return

    changed = False
    if add_key:
        gemini = app_config.providers.setdefault("gemini", ProviderKeys())
        from src.io.formats import ApiKeyEntry
        gemini.keys.append(ApiKeyEntry(name=f"key{len(gemini.keys)+1}", key=add_key, enabled=True))
        changed = True
        click.echo(f"API key added ({len(gemini.keys)} total for gemini)")
    if ollama_host:
        app_config.ollama.host = ollama_host
        changed = True
    if ollama_timeout:
        app_config.ollama.timeout = ollama_timeout
        changed = True

    if changed:
        save_app_settings(app_config)
        click.echo("App config saved")


@cli.command("help")
def cmd_help() -> None:
    click.echo("""
Commands:
  input-generate   Generate lang_input.json from strings.json
  run              Translate using the configured provider
  apply            Apply normalized translations to strings_es.json
  fix              Re-apply translations to existing strings_es.json
  normalice        Normalize lang_es_out.json → lang_es_normalize.json
  voids            Remove empty translations
  clean            Clean key prefixes
  merge            Merge input + output files
  pull-manual      Generate file with untranslated dialogs
  apply-manual     Apply manual edits
  view             Show translation progress
  settings         View/change project settings
  config           View/change app configuration
""")


def cli_main() -> None:
    cli()
