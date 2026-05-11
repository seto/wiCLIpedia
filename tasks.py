# Copyright (C) 2026  Roberto Matarazzo
#
# This file is part of WiCLIpedia.
#
# WiCLIpedia is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# WiCLIpedia is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WiCLIpedia.  If not, see <https://www.gnu.org/licenses/>.

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
    ctx.run("rm -rf dist/ build/ *.egg-info")
    ctx.run('find . -name "__pycache__" -type d -exec rm -r {} +')
    print("Done!")


@task(pre=[clean])
def build(ctx):
    ctx.run("python -m build")


@task(pre=[build])
def publish(ctx):
    ctx.run("twine upload dist/*")
