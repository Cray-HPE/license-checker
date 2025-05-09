#!/usr/bin/env python3
#
# MIT License
#
# (C) Copyright 2021-2025 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
import argparse
import re
import yaml
import sys
import os
import fnmatch
import logging
import datetime

class LicenseCheck(object):

    class LicenseCheckResult(object):
        def __init__(self, code, message, matcher=None):
            self.code = code
            self.message = message
            self.matcher = matcher
            if code > 0:
                logging.warning(message)
            else:
                logging.info(message)

        def __repr__(self):
            return "[%d, %s]" % (self.code, self.message)

    def deep_merge(self, dict1, dict2):
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def __init__(self, **kwargs):
        self.config = self.read_config(sys.path[0] + os.path.sep + 'license_check.yaml')
        config_override = kwargs.get("config_override")
        if not config_override:
            config_override = os.getcwd() + os.path.sep + ".license_check.yaml"
        if os.path.exists(config_override):
            self.config = self.deep_merge(self.config, self.read_config(config_override))
        else:
            logging.info("Skipping non-existent configuration file %s" % config_override)
        self.config.update(kwargs)
        if self.config["add_exclude"]:
            self.config["exclude"].extend(self.config["add_exclude"])
        if kwargs.get("add_exclude_cli"):
            self.config["exclude"].extend(kwargs["add_exclude_cli"].split(","))
        # start_year and end_year may be come as None from argparse
        current_year = datetime.datetime.now().year
        self.config["start_year"] = self.config["start_year"] if self.config.get("start_year") else current_year
        self.config["end_year"] = self.config["end_year"] if self.config.get("end_year") else current_year
        self.config["ignore_year"] = self.config["ignore_year"] if self.config.get("ignore_year") else False
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug("Effective configuration:\n" + yaml.safe_dump(self.config))
        # Build dict {type_name: (main_pattern, [additional_patterns])}
        self.license_pattern_by_type = {}
        for type_name in self.config["comment_types"]:
            type_def = self.config["comment_types"][type_name]
            self.license_pattern_by_type[type_name] = (
                self.template_to_pattern(self.config["license_template"], type_def),
                list(map(lambda x: self.template_to_pattern(x, type_def), self.config["additional_templates"]))
            )
        # Cache exclusion computations
        self.exclusion_cache = {}

    def read_config(self, config_file):
        logging.info("Parsing config file %s ..." % os.path.realpath(config_file))
        with open(config_file) as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
        if "file_types" in config and isinstance(config["file_types"], list):
            logging.warning("Detected v1 list style config for file_types, converting to dict")
            config["file_types"] = dict({f["pattern"] : {k: v for k, v in f.items() if k != "pattern"} for f in config["file_types"]})
        return config

    """
    Converts template (a string with [year] and [owner] placeholders) to regex pattern, specific to a file type
    (i.e. taking into account shebang line, comment start/end, line prefixes, etc).
    """
    def template_to_pattern(self, template, type_def):
        license_pattern = re.escape(template.strip()) \
            .replace(r'\[year\]', r'\[?(?P<start_year>[0-9\- ,]*)(?P<end_year>[0-9]{4})\]?') \
            .replace(r'\[owner\]', r'(?P<owner>[a-zA-Z0-9 \-,/]+)') \
            .split("\n")
        line_prefix = re.sub(r'(\\ )+', r'\ *', re.escape(type_def["line_prefix"]))
        return \
            "^(?P<shebang>" + type_def["shebang_pattern"] + ")?" + \
            "(?P<license>\n*" + \
            (type_def["insert_before_pattern"] if "insert_before_pattern" in type_def else re.escape(type_def["insert_before"])) + \
            "(" + line_prefix + "\n)*" + \
            "\n*".join(map(lambda x:  (("(" + line_prefix + ")?") if x == "\\" else line_prefix) + x + " *", license_pattern)) + "\n*" + \
            "(" + line_prefix + "\n)*" + \
            (type_def["insert_after_pattern"] if "insert_after_pattern" in type_def else re.escape(type_def["insert_after"])) + \
            ")?"

    """
    Checks if given path matches exclusion configuration. Matching performed for nested paths, starting from original path
    and up to root folder. It is needed to exclude files, explciitly provided in command line, not matching exclusion pattern,
    but belonging to excluded folder.
    """
    def matches_exclude(self, path):
        relpath = os.path.relpath(path)
        logging.debug("Checking \"%s\" for exclusion" % (relpath))
        while relpath:
            if self.matches_exclude_path(relpath):
                logging.debug("Final result of exclusion check for \"%s\" is True" % (path))
                return True
            else:
                relpath = relpath.rpartition("/")[0]
        logging.debug("Final result of exclusion check for \"%s\" is False" % (path))
        return False

    def matches_exclude_path(self, path):
        if path in self.exclusion_cache:
            logging.debug("Found exclusion check result for \"%s\" in cache as %s" % (path, str(self.exclusion_cache[path])))
            return self.exclusion_cache[path]
        for p in self.config["exclude"]:
            if fnmatch.fnmatch(path, p):
                logging.debug("Matching \"%s\" against \"%s\" .... matched!" % (path, p))
                self.exclusion_cache[path] = True
                return True
            else:
                logging.debug("Matching \"%s\" against \"%s\" .... no match!" % (path, p))
        self.exclusion_cache[path] = False
        return False

    """
    Main working method
    """
    def check(self, scan_targets, fix=False):
        result = []
        if isinstance(scan_targets, str):
            scan_targets = [scan_targets]
        for scan_target in scan_targets:
            if self.matches_exclude(scan_target):
                logging.info("Excluding file or directory %s as it matches excludes pattern" % scan_target)
            elif os.path.isdir(scan_target):
                logging.info("Scanning directory %s" % scan_target)
                for dirname, subdirs, filenames in os.walk(scan_target):
                    for subdir in subdirs.copy():
                        if self.matches_exclude(dirname + os.path.sep + subdir):
                            logging.info("Excluding directory %s/%s as it matches excludes pattern" % (dirname, subdir))
                            subdirs.remove(subdir)
                    for filename in filenames:
                        filename = dirname + os.path.sep + filename
                        if os.path.islink(filename):
                            logging.info("Excluding file %s as it is a link" % filename)
                        elif self.matches_exclude(filename):
                            logging.info("Excluding file %s as it matches excludes pattern" % filename)
                        else:
                            result.append(self.check_file(filename, fix))
            elif os.path.isfile(scan_target):
                logging.info("Scanning file %s" % scan_target)
                result.append(self.check_file(scan_target, fix))
            else:
                logging.warning("Can't scan %s - not regular file or directory" % scan_target)
        return result

    """
    Evaluate license template (replace [year] and [owner] placeholders, add comment start/end and line prefixes)
    """
    def license_template(self, file_type, matcher=None):
        start_year = self.config.get("start_year")
        end_year = self.config.get("end_year")
        if matcher and matcher.groupdict().get("end_year"):
            start_year_current = matcher.groupdict().get("start_year")
            end_year_current = int(matcher.groupdict().get("end_year"))
            group_current = "%s%d" % (start_year_current, end_year_current)
            if end_year_current == end_year - 1:
                # End year is 1 year behind
                if start_year_current.endswith("-"):
                    # "2016, 2019-2021" > "2016, 2019-2022"
                    year_replace = "%s%d" % (start_year_current, end_year)
                else:
                    # "2016, 2021" > "2016, 2021-2022"; "2021" > "2021-2022"
                    year_replace = "%s-%d" % (group_current, end_year)
            elif end_year_current < end_year - 1:
                # End year is more then 1 year behind - add new end year separated with comma
                # "2016, 2018-2020" > "2016, 2018-2020, 2022"
                year_replace = "%s, %d" % (group_current, end_year)
            else:
                # End year is already up to date or in the future, replacing it with end_year
                year_replace = "%s%d" % (start_year_current, end_year)
        else:
            # No year matching group - new header being added
            if start_year < end_year:
                # Add year range, in case if back-dated fix requested by providing start_year in the past
                year_replace = "%d-%d" % (start_year, end_year)
            else:
                # Add single year as part of new license header
                year_replace = str(end_year)
        type_def = self.config["comment_types"][file_type]
        license_text = self.config["license_template"].strip()
        if type_def["line_prefix"]:
            license_text = "\n" + license_text + "\n"
            license_text = "\n".join(map(lambda x: (type_def["line_prefix"] + x).rstrip(), license_text.split("\n")))
        return type_def["insert_before"] + \
            license_text.replace("[owner]", self.config["owner"]).replace("[year]", year_replace) + "\n" + \
            type_def["insert_after"]

    def fix_or_report(self, code, message, file_type, matcher, fix, filename, outfile):
        if not fix:
            return self.LicenseCheckResult(code, message, matcher)
        if code == 0:
            logging.info(message)
        else:
            if outfile is None:
                logging.warning("Fixing file %s in place ..." % filename)
            else:
                logging.warning("Fixing file %s, writing result to %s ..." % (filename, outfile))
            new_content = ""
            pos = 0
            if matcher and matcher.groupdict().get("shebang"):
                new_content += matcher.group("shebang")
                pos += len(matcher.group("shebang"))
            if matcher and matcher.groupdict().get("license"):
                new_content += self.license_template(file_type, matcher)
                pos += len(matcher.group("license"))
            else:
                new_content += self.license_template(file_type)
            with open(filename) as f:
                content = f.read()
            with open(outfile if outfile is not None else filename, "w") as f:
                f.write(new_content + content[pos:])
        return None

    def check_file(self, filename, fix=False, outfile=None):
        file_type_def = None
        for file_pattern in self.config["file_types"]:
            if fnmatch.fnmatch(os.path.relpath(filename), file_pattern):
                file_type_def = self.config["file_types"][file_pattern]
                logging.debug("Matching %s against %s to determine file type .... matched!" % (os.path.relpath(filename), file_pattern))
                break
            else:
                logging.debug("Matching %s against %s to determine file type .... no match!" % (os.path.relpath(filename), file_pattern))
        if not file_type_def:
            return self.LicenseCheckResult(0, "Filename pattern not recognized: %s" % filename)
        file_type = file_type_def["type"]
        with open(filename) as f:
            content = f.read(4092)
        if not content:
            return self.LicenseCheckResult(0, "File %s is empty" % filename)
        logging.debug("Trying main file comment type for %s as %s" % (filename, file_type))
        pattern = self.license_pattern_by_type[file_type][0]
        logging.debug("Applying pattern:\n%s\nagainst content\n%s" % (pattern, content))
        result = re.search(pattern, content)
        if not result or not result.groupdict().get("license") and "alternative_type" in file_type_def:
            logging.debug("Trying alternate file comment type for %s as %s" % (filename, file_type_def["alternative_type"]))
            pattern = self.license_pattern_by_type[file_type_def["alternative_type"]][0]
            logging.debug("Applying pattern:\n%s\nagainst content\n%s" % (pattern, content))
            result = re.search(pattern, content)
        if result and result.groupdict().get("license"):
            logging.debug("Discovered groups: %s" % str(result.groupdict()))
            if result.groupdict().get("end_year") and result.group("end_year") != str(self.config["end_year"]) and not self.config["ignore_year"]:
                return self.fix_or_report(1, "License is detected, but copyright year is not up to date: %s" % filename, file_type, result, fix, filename, outfile)
            if result.groupdict().get("owner") and result.group("owner") != self.config["owner"]:
                return self.fix_or_report(1, "License is detected, but copyright owner is not current: %s" % filename, file_type, result, fix, filename, outfile)
            return self.fix_or_report(0, "License is up to date: %s" % filename, file_type, result, fix, filename, outfile)
        else:
            logging.debug("Main pattern did not match, trying additional patterns")
            for pattern in self.license_pattern_by_type[file_type][1]:
                logging.debug("Applying pattern:\n%s\nagainst content\n%s" % (pattern, content))
                result = re.search(pattern, content)
                if result and result.groupdict().get("license"):
                    return self.fix_or_report(1, "License is detected, but wording is wrong: %s" % filename, file_type, result, fix, filename, outfile)
                logging.debug("Additional pattern did not match")
            return self.fix_or_report(1, "License is not detected: %s" % filename, file_type, result, fix, filename, outfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check or fix license header in source files, with year range support')
    parser.add_argument('--fix', action='store_true', help='fix headers in source files in target directory')
    parser.add_argument('--config', metavar='config_file', help='optional config file, defaults to <scan_directory>/.license_check.yaml')
    parser.add_argument('--log-level', choices=["debug", "info", "warn"], help='log level, defaults to "info"')
    parser.add_argument('--add-exclude', metavar='add_exclude', help='additional filename exclusion patterns, comma-separated')
    parser.add_argument('--start-year', metavar='start_year', type=int, help='start year to use when new header is added (defaults to current year)')
    parser.add_argument('--end-year', metavar='end_year', type=int, help='end year to use (defaults to current year)')
    parser.add_argument('--ignore-year', action='store_true', help='ignore existing copyright year(s), only validate/fix license header wording')
    parser.add_argument('scan_target', nargs='*', default=os.path.curdir, help='directories and individual files to scan (defaults to current directory)')
    args = parser.parse_args()
    if args.log_level == "warn":
        log_level = logging.WARNING
    elif args.log_level == "debug":
        log_level = logging.DEBUG
    elif args.log_level is None and os.environ.get("RUNNER_DEBUG") == "1":
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=log_level)
    license_check = LicenseCheck(config_override=args.config, add_exclude_cli=args.add_exclude,
        start_year=args.start_year, end_year=args.end_year, ignore_year=args.ignore_year)
    result = license_check.check(args.scan_target, fix=args.fix)
    if not args.fix:
        success = len(list(filter(lambda x: x.code == 0, result)))
        total = len(result)
        if total > 0:
            logging.info("License headers score: %d%%" % (100.0 * success / total))
        else:
            logging.info("No files were scanned")
        if success < total:
            logging.info("Not all files have proper license headers. You may fix them by running:")
            logging.info("")
            logging.info("    docker run -it --rm -v $(pwd):/github/workspace /us-docker.pkg.dev/csm-release/csm-docker/stable/license-checker --fix %s" % " ".join(args.scan_target))
            logging.info("")
            logging.info("Please refer to https://github.com/Cray-HPE/license-checker for more details.")
        sys.exit(1 if success < total else 0)
