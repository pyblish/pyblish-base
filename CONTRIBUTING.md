### Contributing to this project

To contribute, fork this project and submit a pull-request.

Your code will be reviewed and merged once it:

1. Does something useful
1. Is up to par with surrounding code

Development for this project takes place in individual forks. The parent project ever only contains a single branch, a branch containing the latest working version of the project.

Bugreports must include:

1. Description
2. Expected results
3. Short reproducible
 
Feature requests must include:

1. Goal (what the feature aims to solve)
2. Motivation (why *you* think this is necessary)
3. Suggested implementation (psuedocode)

Questions may also be submitted as issues.

### Releasing

Releases to [PyPI](https://pypi.org/project/pyblish-base/) are made by the "Release" GitHub Actions workflow, which anyone with write access can run.

1. Bump the version in `pyblish/version.py` via a pull-request and merge it into `master`.
1. Go to Actions -> Release -> Run workflow, select the `master` branch and a target:
    - `dry-run` builds, tests and checks the package without uploading anything.
    - `testpypi` additionally uploads it to [TestPyPI](https://test.pypi.org/project/pyblish-base/) as `<version>.dev<run>`.
    - `pypi` additionally uploads it to PyPI, then creates the git tag and GitHub release for that version.

The workflow refuses to release a version that is already tagged or already on PyPI.
