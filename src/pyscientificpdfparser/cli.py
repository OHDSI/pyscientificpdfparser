# src/pyscientificpdfparser/cli.py
"""Command-Line Interface for the pyScientificPdfParser."""

from __future__ import annotations

import pathlib

import click

from pyscientificpdfparser.core import parse_pdf


@click.group()  # type: ignore[misc]
def cli() -> None:
    """A CLI tool for parsing scientific PDF documents."""
    pass


@cli.command()  # type: ignore[misc]
@click.argument(  # type: ignore[misc]
    "pdf_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
)
@click.option(  # type: ignore[misc]
    "--output-dir",
    "-o",
    default="./parsed_output",
    type=click.Path(file_okay=False, resolve_path=True),
    help="The directory where output files will be saved.",
)
@click.option(  # type: ignore[misc]
    "--llm-refine",
    is_flag=True,
    default=False,
    help="Enable optional LLM-powered refinement for higher accuracy.",
)
def process(pdf_path: str, output_dir: str, llm_refine: bool) -> None:
    """
    Process a single PDF file and save the output.
    """
    pdf_path_obj = pathlib.Path(pdf_path)
    output_dir_obj = pathlib.Path(output_dir)

    # Create the output directory if it doesn't exist
    output_dir_obj.mkdir(parents=True, exist_ok=True)

    click.echo(f"Starting to process PDF: {pdf_path_obj.name}")
    click.echo(f"Output will be saved in: {output_dir_obj}")
    if llm_refine:
        click.echo("LLM refinement is enabled.")

    # Call the core parsing function
    parse_pdf(
        pdf_path=pdf_path_obj,
        output_dir=output_dir_obj,
        llm_refine=llm_refine,
    )

    click.echo("Processing finished.")


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
