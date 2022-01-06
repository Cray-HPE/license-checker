#!/usr/bin/python3
#
# MIT License
#
# (C) Copyright [2021-2022] Hewlett Packard Enterprise Development LP
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
import datetime
import unittest
import license_check
import sys
import logging
import tempfile
import os

class LicenseCheckTest(unittest.TestCase):
    def testExcludeFolder(self):
        checker = license_check.LicenseCheck(rootdir="tests", exclude=["tests/*"])
        result = checker.check("tests")
        self.assertEqual(result, [])

    def testExcludeFile(self):
        checker = license_check.LicenseCheck(rootdir="tests/exclude", exclude=["*/exclude.*"])
        result = checker.check()
        self.assertEqual(result, [])

    def testValidYaml(self):
        checker = license_check.LicenseCheck(rootdir="tests", config_override="tests/config_no_year.yaml")
        result = checker.check_file("tests/valid_old_year.yaml")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidYamlWithDummyLine(self):
        checker = license_check.LicenseCheck(rootdir="tests", config_override="tests/config_no_year.yaml")
        result = checker.check_file("tests/valid_old_year_dummy_line.yaml")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidShell(self):
        checker = license_check.LicenseCheck(rootdir="tests", config_override="tests/config_no_year.yaml")
        result = checker.check_file("tests/valid_old_year.sh")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidShellWithDummyLine(self):
        checker = license_check.LicenseCheck(rootdir="tests", config_override="tests/config_no_year.yaml")
        result = checker.check_file("tests/valid_old_year_dummy_line_shebang.sh")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidShellWithEmptyLine(self):
        checker = license_check.LicenseCheck(rootdir="tests", config_override="tests/config_no_year.yaml")
        result = checker.check_file("tests/valid_old_year_empty_line_shebang.sh")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidXml(self):
        checker = license_check.LicenseCheck(rootdir="tests", config_override="tests/config_no_year.yaml")
        result = checker.check_file("tests/valid_old_year.xml")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidXmlMultilineDeclaration(self):
        checker = license_check.LicenseCheck(rootdir="tests", config_override="tests/config_no_year.yaml")
        result = checker.check_file("tests/valid_old_year_multiline_declaration.xml")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidJava(self):
        checker = license_check.LicenseCheck(rootdir="tests", config_override="tests/config_no_year.yaml")
        result = checker.check_file("tests/valid_old_year.java")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testConvertSingleYearToRangeJava(self):
        checker = license_check.LicenseCheck(rootdir="tests")
        outfile = tempfile.gettempdir() + "/valid_old_year.java"
        checker.check_file("tests/valid_old_year.java", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("year"), "2020-%d" % datetime.datetime.now().year)
        os.remove(outfile)

    def testAddLicenseToXml(self):
        checker = license_check.LicenseCheck(rootdir="tests")
        outfile = tempfile.gettempdir() + "/no_license.xml"
        checker.check_file("tests/no_license.xml", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("year"), "%d" % datetime.datetime.now().year)
        os.remove(outfile)

    def testAddLicenseToShell(self):
        checker = license_check.LicenseCheck()
        outfile = tempfile.gettempdir() + "/no_license.sh"
        checker.check_file("tests/no_license.sh", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("year"), "%d" % datetime.datetime.now().year)
        os.remove(outfile)

    def testExtendRangeGo(self):
        checker = license_check.LicenseCheck()
        outfile = tempfile.gettempdir() + "/valid_old_range.go"
        checker.check_file("tests/valid_old_range.go", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("year"), "2016-%d" % datetime.datetime.now().year)
        os.remove(outfile)

logging.basicConfig(level=logging.WARNING)
os.chdir(sys.path[0])
unittest.main()