# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.35.1",
# ]
# ///

import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import polars as pl
    return (pl,)


@app.cell
def _(pl):
    pl.__file__
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
