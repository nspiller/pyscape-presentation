from invoke import task


@task
def format(c, github=False):
    if github:
        print("Running formatter with GitHub Actions...")
        c.run("ruff format --diff .")
    else:
        print("Running formatter locally...")
        c.run("ruff format .")


@task
def lint(c, github=False):
    if github:
        print("Running linter with GitHub Actions...")
        c.run("ruff check --diff --output-format=github .")
    else:
        print("Running linter locally...")
        c.run("ruff check --fix .")


@task(pre=[format, lint])
def check(c):
    pass
