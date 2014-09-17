from pyblish.vendor import click


@click.group()
@click.option("--verbose", default=False)
@click.pass_context
def main(ctx, verbose):
    if not ctx.obj:
        ctx.obj = dict()

    ctx.obj['verbose'] = verbose
    verbose = verbose


@click.command()
@click.argument("path")
@click.option("-a", "--all", default=None)
@click.option("-i", "--instance", default=None)
@click.pass_context
def publish(ctx, path, all=None, instance=None):
    """Publish instances of `path`

    \b
    Usage:
        $ pyblish publish my_file.txt --instance=Message01
        $ pyblish publish my_file.txt --all

    """

    print path
