# license-checker
Validate and fix license headers in source files. Year ranges are supported: if license header refers to copyright year as `2021`,
it will be converted to `2021-2022` if run with `--fix` option in year 2022. If license header is completely missed from the file, it will be
added with copyright year `2022`. Use `--start-year 2021` option to override this behaivor and use copyright year range `2021-2022` for files, which
had completely missed license header before.

Files which are in unrecognized format are reported, but this does not affect final score. Files in recognized format are checked and this affects final score,
printed as last line (if run without `--fix` option).

## Quick Start

Run this to verify license headers in all recognized files in current directory:
```
$ docker run -it --rm -v $(pwd):/github/workspace artifactory.algol60.net/csm-docker/stable/license-checker
```

Run this to fix license headers in all recognized files in current directory:
```
$ docker run -it --rm -v $(pwd):/github/workspace artifactory.algol60.net/csm-docker/stable/license-checker --fix
```

Run this to fix license headers in all recognized files in current directory, pushing start of copyright year range back to year 2021:
```
$ docker run -it --rm -v $(pwd):/github/workspace artifactory.algol60.net/csm-docker/stable/license-checker --fix --start-year 2021
```

Run this to fix license headers in specific files, pushing start of copyright year range back to year 2021:
```
$ docker run -it --rm -v $(pwd):/github/workspace artifactory.algol60.net/csm-docker/stable/license-checker --fix --start-year 2021 path/to/file1 path/to/file2
```

Alternatively, if you don't want to run docker, you can run license-checker Python script. You will need standard Python3 distro, plus PyYAML module installed. Clone license-checker repo. If run without parameters, license-checker script will perform read-only checking in current directory.
```
$ git clone https://github.com/Cray-HPE/license-checker.git
$ cd /path/to/my-repo
$ /path/to/license_check.py
...
$ /path/to/license_check.py --fix
...
```

## Customizations
Customizations are available through `.license_check.yaml` file, placed into top level scan directory (which defaults to current directory).
For full list and explanation of all customizable fields, please refer to [main configuration file](https://github.com/Cray-HPE/license-checker/blob/main/license_check.yaml).
Settings, defined in `.license_check.yaml`, are merged on top of defaults: dicts are updated, lists are getting overwritten.

Most notable settings, which may require customization, are:

1. `file_types`. This section sets relationship between filename pattern and content type. This section is defined as dict, so if you need
    to ovewrite existing definition, or add new one, just add it to `.license_check.yaml`:
    ```
    file_types:
        "*.htm": html
    ```
2. `add_exclude`. Use this section in `.license_check.yaml` to *add* new entries to exclusion list (preserving default entries):
   ```
   add_exclude:
       - "ignore_this.*"
   ```
   Patterns in exclusion list must follow [Python fnmatch module syntax](https://docs.python.org/3/library/fnmatch.html). File and directory names are
   normalized relative to top level scan directory (i.e. `./dist/` becomes `dist`), and then matched against exclusion pattern. Directories, matching
   exclusion pattern, are not descended into. I.e., use `dist` to exclude `dist` folder, located in scan root. Use another entry `*/dist` to exclude
   all folders, named `dist`, located deeper in file tree.

## Integration with GitHub Workflows
If docker image is available for anonymous read at public docker registry, add the following to a file named `.github/workflows/license-check.yaml`:
```
name: license-check

on:
  push:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: License Check
        uses: docker://<your_public_registry>/license-checker:latest
```
Alternatively, if image is only available from private registry, create secrets holding private registry username and password, and 
use containerized job, which does support private registries:
```
name: license-check

on:
  push:
  workflow_dispatch:

jobs:
  license-check:
    runs-on: ubuntu-latest

    container:
      image: <your_private_registry>/license-checker:latest
      credentials:
          username: ${{ secrets.<your_private_registry_username_secret> }}
          password: ${{ secrets.<your_private_registry_password_secret> }}

    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: License Check
        run: /usr/local/bin/python3 /license_check/license_check.py
```