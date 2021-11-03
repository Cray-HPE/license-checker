# license-checker
Validate and fix license headers in source files. Year ranges are supported: if license header refers to copyright year as "\[2021\]",
it will be converted to "\[2021-2022\]" if run in year 2022.

Files which are in unrecognized format are reported, but do not affect final score. Files in recognized format are checked and affect final score,
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
   Patterns in inclusion list must follow [Python fnmatch module syntax](https://docs.python.org/3/library/fnmatch.html), applied against path to
   each individual file, relative to top level scan directory. I.e., use `dist/*` to cover all files in `dist/` folder. Specifying just `dist/` is not
   sufficient.
