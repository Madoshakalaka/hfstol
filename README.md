# hfstol
![travis-badge](https://travis-ci.org/Madoshakalaka/hfstol.svg?branch=master)
![code-cov](https://codecov.io/gh/Madoshakalaka/hfstol/branch/master/graphs/badge.svg)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/hfstol.svg)](https://pypi.python.org/pypi/hfstol/)

hfst-optimized-lookup in python


`pip install hfstol`

All below examples are based on two `.hfstol` files

respectively: [crk-descriptive-analyzer.hfstol crk-normative-generator.hfstol](https://github.com/UAlbertaALTLab/plains-cree-fsts/releases)


# Use

example with `crk-descriptive-analyzer.hfstol` :

```python
from hfstol import HFSTOL

hfst = HFSTOL.from_file('crk-descriptive-analyzer.hfstol')

hfst.feed('niska')
# returns: 
# (('niska', '+N', '+A', '+Sg'), ('niska', '+N', '+A', '+Obv'))

hfst.feed_in_bulk(['niska', 'kinipânânaw'])
# returns: 
# {'niska': {('niska', '+N', '+A', '+Obv'), ('niska', '+N', '+A', '+Sg')}, 'kinipânânaw': {('nipâw', '+V', '+AI', '+Ind', '+Prs', '+12Pl')}}

hfst.feed_in_bulk_fast(['niska', 'kinipânânaw'])
# returns:
# {'niska': {'niska+N+A+Obv', 'niska+N+A+Sg'}, 'kinipânânaw': {'nipâw+V+AI+Ind+Prs+12Pl'}}

```

example with `crk-normative-generator.hfstol` :

```python
from hfstol import HFSTOL

hfst = HFSTOL.from_file('crk-normative-generator.hfstol')

hfst.feed('niska+N+A+Pl')
# returns: 
# (('niskak',),)

hfst.feed_in_bulk(["niska+N+A+Pl", 'nipâw+V+AI+Ind+Prs+12Pl'])
# returns: 
# {'niska+N+A+Pl': {('niskak',)}, 'nipâw+V+AI+Ind+Prs+12Pl': {('kinipânânaw',), ('kinipânaw',)}}

hfst.feed_in_bulk_fast(["niska+N+A+Pl", 'nipâw+V+AI+Ind+Prs+12Pl'], multi_process=4)
# returns:
# {'niska+N+A+Pl': {'niskak'}, 'nipâw+V+AI+Ind+Prs+12Pl': {'kinipânânaw', 'kinipânaw'}}
```

to see a comprehensive API behaviour including edge cases, see [this test file](https://github.com/Madoshakalaka/hfstol/blob/master/tests/test_apply.py) (what if I `feed('absolute garbage')`)

# API signatures


```python

# HFSTOL.from_file

@classmethod
def from_file(cls, filename: Union[str, pathlib.Path]): 
    """
    :param filename: the `.hfstol` file
    :return: an `HFSTOL` instance, which you can use to convert surface forms to deep forms
    """
    pass


# HFSTOL.feed

def feed(self, surface_form: str, concat: bool = True) -> Tuple[Tuple[str, ...], ...]:
    """
    feed surface form to hfst

    :param surface_form: the surface form
    :param concat: whether to concatenate single characters

        example output for `surface_form` = 'niskak', with `crk-descriptive-analyzer.hfstol`
        - True: (('niska', '+N', '+A', '+Pl'), ('nîskâw', '+V', '+II', '+II', '+Cnj', '+Prs', '+3Sg'))
        - False: (('n', 'i', 's', 'k', 'a', '+N', '+A', '+Pl'), ('n', 'î', 's', 'k', 'â', 'w', '+V', '+II', '+II', '+Cnj', '+Prs', '+3Sg'))

        example output for `surface_form` = 'niska+N+A+Pl' with `crk-normative-generator.hfstol`
        - True: (('niskak',),)
        - False: (('n', 'i', 's', 'k', 'a', 'k'),)

        example output for `surface_form` = 'niska+N+A+Pl' with `crk-normative-generator.hfstol` (an inflection that has two spellings)
        - True: (('kinipânaw',), ('kinipânânaw',))
        -False: (('k', 'i', 'n', 'i', 'p', 'â', 'n', 'a', 'w'), ('k', 'i', 'n', 'i', 'p', 'â', 'n', 'â', 'n', 'a', 'w'))
    """
    pass
    
# HFSTOL.feed_in_bulk   

def feed_in_bulk(self, surface_forms: List[str], concat=True) -> Dict[str, Set[Tuple[str, ...]]]:
    """
    feed a multiple of surface forms to hfst at once

    :param surface_forms:
    :return: a dictionary with keys being each surface form fed in, values being their corresponding deep forms
    """
    pass

# HFSTOL.feed_in_bulk_fast

def feed_in_bulk_fast(self, strings: Iterable[str], multi_process: int = 1) -> Dict[str, Set[str]]:
    """
    calls `hfstol-optimized-lookup`. Evaluation is magnitudes faster. Note the generated symbols will all be all concatenated.
    e.g. instead of ['n', 'i', 's', 'k', 'a', '+N', '+A', '+Pl'] it returns ['niska+N+A+Pl']

    :keyword multi_process: Defaults to 1. Specify how many parallel processes you want to speed up computation. A rule is to have processes at most your machine core count.
    """

```


# To Use `feed_in_bulk_fast`

`feed_in_bulk_fast` calls compiled C code, which can be 100 times faster than `feed_in_bulk`. 

It requires `hfst-optimized-lookup` installed. Version 1.2 is tested to work. For linux system, installing can be as easy as `sudo apt install hfst`. For other systems see [installation guide](https://github.com/hfst/hfst#installation)

If `hfst-optimized-lookup` is not found, calling `feed_in_bulk_fast` throws `ImportError`
