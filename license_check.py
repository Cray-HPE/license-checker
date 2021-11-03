#!/usr/bin/python3
#
# MIT License
#
# (C) Copyright [2021] Hewlett Packard Enterprise Development LP
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

    def __init__(self, **kwargs):
        self.rootdir = kwargs.get("rootdir", os.path.curdir)
        logging.info("Scanning from top level directory %s" % self.rootdir)
        self.config = self.read_config(sys.path[0] + os.path.sep + 'license_check.yaml')
        config_override = kwargs.get("config_override")
        if not config_override:
            config_override = self.rootdir + os.path.sep + ".license_check.yaml"
        if os.path.exists(config_override):
            self.config.update(self.read_config(config_override))
        else:
            logging.info("Skipping non-existent configuration file %s" % config_override)
        self.config.update(kwargs)
        if self.config["add_exclude"]:
            self.config["exclude"].extend(self.config["add_exclude"])
        if kwargs.get("add_exclude_cli"):
            self.config["exclude"].extend(kwargs["add_exclude_cli"].split(","))
        license_pattern = re.escape(self.config["license_template"].strip()) \
            .replace('\\[year\\]', '(?P<year>([0-9]{4}-)?[0-9]{4})') \
            .replace('\\[owner\\]', '(?P<owner>[a-zA-Z0-9 \-,]+)') \
            .split("\n")
        self.license_pattern_by_type = {}
        for type_name in self.config["comment_types"]:
            type_def = self.config["comment_types"][type_name]
            line_prefix = re.sub("(\\\ )+", "\\ *", re.escape(type_def["line_prefix"]))
            self.license_pattern_by_type[type_name] = \
                "^(?P<shebang>" + type_def["shebang_pattern"] + ")?" + \
                "(?P<license>\n*" + \
                re.escape(type_def["insert_before"]) + \
                "(" + line_prefix + "\n)*" + \
                "\n*".join(map(lambda x: line_prefix + ("*" if line_prefix.endswith(" ") and x == "\\" else "") + x + " *", license_pattern)) + "\n*" + \
                "(" + line_prefix + "\n)*" + \
                re.escape(type_def["insert_after"]) + \
                ")?"

    def read_config(self, config_file):
        logging.info("Parsing config file %s ..." % config_file)
        with open(config_file) as f:
            return yaml.load(f, Loader=yaml.SafeLoader)

    def matches_exclude(self, path):
        for p in self.config["exclude"]:
            if fnmatch.fnmatch(os.path.relpath(path), os.path.relpath(p)):
                return True
        return False

    def check(self, fix=False):
        result = []
        for dirname, _, filenames in os.walk(self.rootdir):
            if self.matches_exclude(dirname):
                logging.debug("Excluding directory %s as it matches excludes pattern" % dirname)
            else:
                for filename in filenames:
                    filename = dirname + os.path.sep + filename
                    if os.path.islink(filename):
                        logging.debug("Excluding file %s as it is a link" % filename)
                    elif self.matches_exclude(filename):
                        logging.debug("Excluding file %s as it matches excludes pattern" % filename)
                    else:
                        result.append(self.check_file(filename, fix))
        return result

    def license_template(self, file_type, matcher=None):
        current_year = datetime.datetime.now().year
        if matcher and matcher.groupdict().get("year"):
            year_range = matcher.group("year").split("-")
            if int(year_range[0]) < current_year:
                year_replace = "%s-%d" % (year_range[0], current_year)
            else:
                year_replace = str(current_year)
        else:
            year_replace = str(current_year)
        type_def = self.config["comment_types"][file_type]
        license_text = self.config["license_template"].strip()
        if type_def["line_prefix"]:
            license_text = "\n" + license_text + "\n"
            license_text = "\n".join(map(lambda x: (type_def["line_prefix"] + x).strip(), license_text.split("\n")))
        return type_def["insert_before"] + \
            license_text.replace("[owner]", self.config["owner"]).replace("[year]", year_replace) + "\n" + \
            type_def["insert_after"]

    def fix_or_report(self, code, message, file_type, matcher, fix, filename, outfile):
        if code == 0 or not fix:
            return self.LicenseCheckResult(code, message)
        logging.info("Fixing file %s ..." % filename)
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

    def check_file(self, filename, fix=False, outfile=None):
        filename_pattern = None
        for filename_pattern_candidate in self.config["file_types"]:
            if fnmatch.fnmatch(os.path.basename(filename), filename_pattern_candidate):
                filename_pattern = filename_pattern_candidate
                break
        if not filename_pattern:
            return self.LicenseCheckResult(0, "Filename pattern not recognized: %s" % filename)
        file_type = self.config["file_types"][filename_pattern]
        logging.debug("Identified file type for %s as %s" % (filename, file_type))
        with open(filename) as f:
            content = f.read(4092)
        logging.debug("Applying pattern:\n%s\nagainst content\n%s" % (self.license_pattern_by_type[file_type], content))
        result = re.search(self.license_pattern_by_type[file_type], content)
        if result and result.groupdict().get("license"):
            logging.debug("Discovered groups: %s" % str(result.groupdict()))
            if result.groupdict().get("year") and not result.group("year").endswith(str(datetime.datetime.now().year)):
                return self.fix_or_report(1, "License is detected, but copyright year is not up to date: %s" % filename, file_type, result, fix, filename, outfile)
            if result.groupdict().get("owner") and result.group("owner") != self.config["owner"]:
                return self.fix_or_report(1, "License is detected, but copyright owner is not current: %s" % filename, file_type, result, fix, filename, outfile)
            return self.LicenseCheckResult(0, "License is up to date: %s" % filename, result)
        else:
            return self.fix_or_report(1, "License is not detected: %s" % filename, file_type, result, fix, filename, outfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check or fix license header in source files, with year range support')
    parser.add_argument('--fix', action='store_true', help='fix headers in source files in target directory')
    parser.add_argument('--config', metavar='config_file', help='optional config file, defaults to <scan_directory>/.license_check.yaml')
    parser.add_argument('--log-level', choices=["debug", "info", "warn"], help='log level, defaults to "info"')
    parser.add_argument('--add-exclude', metavar='add_exclude', help='additional filename patterns, comma-separated')
    parser.add_argument('scan_directory', nargs='?', default=os.path.curdir, help='top level directory to scan (defaults to current directory)')
    args = parser.parse_args()
    if args.log_level == "warn":
        log_level = logging.WARNING
    elif args.log_level == "debug":
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format="[%(levelname).4s] %(message)s", level=log_level)
    license_check = LicenseCheck(rootdir=args.scan_directory, config_override=args.config, add_exclude_cli=args.add_exclude)
    result = license_check.check(fix=args.fix)
    if not args.fix:
        print("License headers score: %d%%" % (100.0 * len(list(filter(lambda x: x.code == 0, result))) / len(result)))
