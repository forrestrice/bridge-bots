# Bridgebots Core
This package contains the core components of the bridgebots library. The main focus is representing Contract Bridge concepts such as suits, ranks, cards, deals, bids, alerts, and scores. Data processing utilities such as a PBN parser are also included.

### Installation
`pip install bridgebots`

### Requirements
This package will attempt to maintain an extremely minimal set of external dependencies. As of this writing there are zero.


## Building, Testing, and Contributing
Bridgebots uses [Poetry](https://python-poetry.org/) to manage building, testing, and publishing.

### Build
`poetry install` to install dependencies.

`poetry build` to build a wheel file.

### Test
`poetry run pytest` to run all unit tests.

### Contribute
Feel free to create issues or fork the repository and submit a pull-request. This is a hobby project, so they may not be addressed immediately.

### Style
Format all Python code using [Black](https://github.com/psf/black) with `--line-length 120`.

Use type-hints wherever possible.

Any added functionality should include unit tests.

## Examples
TODO
