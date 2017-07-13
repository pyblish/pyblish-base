[![Build Status][travis-image]][travis-link]
[![Build status][appveyor-image]](https://ci.appveyor.com/project/mottosso/pyblish)
[![Coverage Status][cover-image]][cover-link]
[![PyPI version][pypi-image]][pypi-link]
[![Code Health][landscape-image]][landscape-repo]
[![Gitter][gitter-image]](https://gitter.im/pyblish/pyblish?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![image](https://cloud.githubusercontent.com/assets/2152766/12704326/b6ff015c-c850-11e5-91be-68d824526f13.png)](https://www.youtube.com/watch?v=j5uUTW702-U)

Test-driven content creation for collaborative, creative projects.

- [Wiki](../../wiki)
- [Learn by Example](http://learn.pyblish.com)

<br>
<br>
<br>

### Introduction

Pyblish is a modular framework, consisting of many sub-projects. This project contains the primary API upon which all other projects build.

You may use this project as-is, or in conjunction with surrounding projects - such as [pyblish-maya][] for integration with Autodesk Maya, [pyblish-qml][] for a visual front-end and [pyblish-starter][] for a starting point your publishing pipeline.

[pyblish-maya]: https://github.com/pyblish/pyblish-maya
[pyblish-qml]: https://github.com/pyblish/pyblish-qml
[pyblish-starter]: http://pyblish.com/pyblish-starter

- [Browse All Projects](https://github.com/pyblish)

<br>
<br>
<br>

### Installation

pyblish-base is avaialble on PyPI.

```bash
$ pip install pyblish-base
```

Like all other Pyblish projects, it may also be cloned as-is via Git and added to your PYTHONPATH.

```bash
$ git clone https://github.com/pyblish/pyblish-base.git
$ # Windows
$ set PYTHONPATH=%cd%\pyblish-base
$ # Unix
$ export PYTHONPATH=$(pwd)/pyblish-base
```

<br>
<br>
<br>

### Usage

Refer to the [getting started guide](http://learn.pyblish.com) for a gentle introduction to the framework and [the forums](http://forums.pyblish.com) for tips and tricks.

- [Learn Pyblish By Example](http://learn.pyblish.com)
- [Pyblish Starter - an example pipeline](http://pyblish.com/pyblish-starter)
- [Forums](http://forums.pyblish.com)

[travis-image]: https://travis-ci.org/pyblish/pyblish-base.svg?branch=master
[travis-link]: https://travis-ci.org/pyblish/pyblish-base

[appveyor-image]: https://ci.appveyor.com/api/projects/status/github/pyblish/pyblish-base?svg=true

[cover-image]: https://coveralls.io/repos/pyblish/pyblish-base/badge.svg
[cover-link]: https://coveralls.io/r/pyblish/pyblish-base
[pypi-image]: https://badge.fury.io/py/pyblish-base.svg
[pypi-link]: http://badge.fury.io/py/pyblish
[landscape-image]: https://landscape.io/github/pyblish/pyblish-base/master/landscape.png
[landscape-repo]: https://landscape.io/github/pyblish/pyblish-base/master
[gitter-image]: https://badges.gitter.im/Join%20Chat.svg
