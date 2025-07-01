import sys
import json
from pathlib import Path
import click
import yaml
from src.model import RefrigerantOptimizer

def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise click.BadParameter("YAML must map keys to values")
    return data

@click.group(context_settings={"help_option_names": ["-h", "--help"]}, help="Refrigerant optimisation commands")
def main():
    pass

@main.command()
@click.option("--mix", type=click.Path(exists=True, dir_okay=False), required=True,
              help="YAML file mapping each element to its current mass (kg)")
@click.option("--target", type=float, default=None, help="Target total weight after refuel (kg)")
def refuel(mix: str, target: float):
    comp = _load_yaml(Path(mix))
    opt = RefrigerantOptimizer("refuel", initial_composition=comp, target_weight=target)
    click.echo(json.dumps(opt.optimize(), indent=2))

@main.command("new-blend")
@click.option("--weight", type=float, required=True, help="Desired weight of the new blend (kg)")
def new_blend(weight: float):
    opt = RefrigerantOptimizer("new_blend", target_weight=weight)
    click.echo(json.dumps(opt.optimize(), indent=2))

@main.command("optimise")
@click.option(
    "--mix",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="YAML file mapping each element to its current mass (kg)",
)
@click.option(
    "--target",
    type=float,
    required=True,
    help="Desired total weight after optimisation (kg)",
)
def optimise_mix(mix: str, target: float):
    """Solve the combined optimisation model (Scenario 3)."""
    comp = _load_yaml(Path(mix))
    opt = RefrigerantOptimizer(
        "optimise_mixture", initial_composition=comp, target_weight=target
    )
    click.echo(json.dumps(opt.optimize(), indent=2))

@main.command("auto")
@click.option(
    "--mix",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="YAML file mapping each element to its current mass (kg)",
)
@click.option(
    "--target",
    type=float,
    required=True,
    help="Desired total weight after optimisation (kg)",
)
def auto_mix(mix: str, target: float):
    """Run the optimiser in *auto* mode (currently an alias of optimise_mixture)."""
    comp = _load_yaml(Path(mix))
    opt = RefrigerantOptimizer("auto", initial_composition=comp, target_weight=target)
    click.echo(json.dumps(opt.optimize(), indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)