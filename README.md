# pynetevents

[![CI](https://github.com/Dr0f0x/pynetevents/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Dr0f0x/pynetevents/actions/workflows/python-ci.yml)
[![Publish](https://github.com/Dr0f0x/pynetevents/actions/workflows/publish.yml/badge.svg)](https://github.com/Dr0f0x/pynetevents/actions/workflows/publish.yml)

python implementation of c# style events

for build and publish

python -m build
twine upload --repository testpypi dist/\*

sphinx setup

spinx-quickstart docs

in docs folder .\make html

python -m pip install -e . for editable install