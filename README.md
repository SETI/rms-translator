[![GitHub release; latest by date](https://img.shields.io/github/v/release/SETI/rms-translator)](https://github.com/SETI/rms-translator/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/SETI/rms-translator)](https://github.com/SETI/rms-translator/releases)
[![Test Status](https://img.shields.io/github/actions/workflow/status/SETI/rms-translator/run-tests.yml?branch=main)](https://github.com/SETI/rms-translator/actions)
[![Documentation Status](https://readthedocs.org/projects/rms-translator/badge/?version=latest)](https://rms-translator.readthedocs.io/en/latest/?badge=latest)
[![Code coverage](https://img.shields.io/codecov/c/github/SETI/rms-translator/main?logo=codecov)](https://codecov.io/gh/SETI/rms-translator)
<br />
[![PyPI - Version](https://img.shields.io/pypi/v/rms-translator)](https://pypi.org/project/rms-translator)
[![PyPI - Format](https://img.shields.io/pypi/format/rms-translator)](https://pypi.org/project/rms-translator)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/rms-translator)](https://pypi.org/project/rms-translator)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rms-translator)](https://pypi.org/project/rms-translator)
<br />
[![GitHub commits since latest release](https://img.shields.io/github/commits-since/SETI/rms-translator/latest)](https://github.com/SETI/rms-translator/commits/main/)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/SETI/rms-translator)](https://github.com/SETI/rms-translator/commits/main/)
[![GitHub last commit](https://img.shields.io/github/last-commit/SETI/rms-translator)](https://github.com/SETI/rms-translator/commits/main/)
<br />
[![Number of GitHub open issues](https://img.shields.io/github/issues-raw/SETI/rms-translator)](https://github.com/SETI/rms-translator/issues)
[![Number of GitHub closed issues](https://img.shields.io/github/issues-closed-raw/SETI/rms-translator)](https://github.com/SETI/rms-translator/issues)
[![Number of GitHub open pull requests](https://img.shields.io/github/issues-pr-raw/SETI/rms-translator)](https://github.com/SETI/rms-translator/pulls)
[![Number of GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed-raw/SETI/rms-translator)](https://github.com/SETI/rms-translator/pulls)
<br />
![GitHub License](https://img.shields.io/github/license/SETI/rms-translator)
[![Number of GitHub stars](https://img.shields.io/github/stars/SETI/rms-translator)](https://github.com/SETI/rms-translator/stargazers)
![GitHub forks](https://img.shields.io/github/forks/SETI/rms-translator)

# Introduction

`translator` is a module that provides abstract classes and implementations for mapping strings (such as file paths) to other information. It supports several translation mechanisms including Python dictionaries, regular expression patterns, and sequences of translators.

`translator` is a product of the [PDS Ring-Moon Systems Node](https://pds-rings.seti.org).

# Installation

The `translator` module is available via the `rms-translator` package on PyPI and can be installed with:

```sh
pip install rms-translator
```

# Getting Started

The `translator` module provides several translator classes:

- **`Translator`** - Abstract base class defining the translator interface
- **`TranslatorByDict`** - Fast dictionary-based translation
- **`TranslatorByRegex`** - Flexible regex pattern-based translation with substitution
- **`TranslatorBySequence`** - Combines multiple translators in sequence
- **`NullTranslator`** - Returns nothing (useful as a placeholder)
- **`SelfTranslator`** - Returns the input unchanged

All translator subclasses implement two key methods:
- `all(strings, strings_first=False)` - Returns all matching translations
- `first(strings, strings_first=False)` - Returns the first matching translation

Details of each class are available in the [module documentation](https://rms-translator.readthedocs.io/en/latest/module.html).

## Example: Dictionary Translator

```python
from translator import TranslatorByDict

# Create a simple dictionary translator
trans = TranslatorByDict({
    'apple': 'fruit',
    'carrot': 'vegetable',
    'chicken': 'meat'
})

print(trans.first('apple'))    # Output: 'fruit'
print(trans.all(['apple', 'carrot']))  # Output: ['fruit', 'vegetable']
```

## Example: Regex Translator

```python
from translator import TranslatorByRegex
import re

# Create a regex translator for file paths
trans = TranslatorByRegex([
    (r'data/(\w+)/(\w+)\.txt', r'processed/\1/\2.dat'),
    (r'images/(\w+)\.jpg', r'thumbnails/\1_thumb.jpg')
])

print(trans.first('data/2024/observations.txt'))
# Output: 'processed/2024/observations.dat'

print(trans.first('images/saturn.jpg'))
# Output: 'thumbnails/saturn_thumb.jpg'
```

## Example: Sequence of Translators

```python
from translator import TranslatorByDict, TranslatorByRegex, TranslatorBySequence

# Combine multiple translators
dict_trans = TranslatorByDict({'special': 'handled'})
regex_trans = TranslatorByRegex([(r'(\w+)', r'default_\1')])

seq_trans = TranslatorBySequence([dict_trans, regex_trans])

print(seq_trans.first('special'))  # Output: 'handled' (from dictionary)
print(seq_trans.first('other'))    # Output: 'default_other' (from regex)
```

# Contributing

Information on contributing to this package can be found in the
[Contributing Guide](https://github.com/SETI/rms-translator/blob/main/CONTRIBUTING.md).

# Links

- [Documentation](https://rms-translator.readthedocs.io)
- [Repository](https://github.com/SETI/rms-translator)
- [Issue tracker](https://github.com/SETI/rms-translator/issues)
- [PyPI](https://pypi.org/project/rms-translator)

# Licensing

This code is licensed under the [Apache License v2.0](https://github.com/SETI/rms-translator/blob/main/LICENSE).
