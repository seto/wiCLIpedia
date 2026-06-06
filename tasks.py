from invoke import task


@task
def format(ctx, targets="src tests"):
    print(f"Formatting {targets}...")
    ctx.run(f"black --quiet {targets}")
    ctx.run(f"isort --quiet {targets}")
    print("Done!")


@task
def test(ctx):
    ctx.run("pytest")


@task
def clean(ctx):
    print("Cleaning...")
    ctx.run("rm -rf dist/ build/ *.egg-info .pytest_cache")
    ctx.run('find . -name "__pycache__" -type d -exec rm -r {} +')
    print("Done!")


@task(pre=[clean])
def build(ctx):
    ctx.run("python -m build")


@task(pre=[build])
def publish(ctx):
    ctx.run("twine upload dist/*")
