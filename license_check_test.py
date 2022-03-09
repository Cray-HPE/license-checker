#!/usr/bin/env python3
#
# MIT License
#
# (C) Copyright 2021-2022 Hewlett Packard Enterprise Development LP
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
import unittest
import license_check
import sys
import logging
import tempfile
import os

class LicenseCheckTest(unittest.TestCase):
    def testExcludeFolder(self):
        checker = license_check.LicenseCheck(exclude=["tests"], add_exclude=[])
        result = checker.check("tests")
        self.assertEqual(result, [])

    def testExcludeFile(self):
        checker = license_check.LicenseCheck(exclude=["tests/*"], add_exclude=[])
        result = checker.check("tests")
        self.assertEqual(result, [])

    def testExcludeFileInFolder(self):
        checker = license_check.LicenseCheck(exclude=["tests"], add_exclude=[])
        result = checker.check(["tests/templates/go_template_no_license.yaml", "tests/templates/go_template_one_liner.yaml"])
        self.assertEqual(result, [])

    def testValidYaml(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_year.yaml")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidYamlYearRangeList(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_year_range_list.yaml")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidYamlWithDummyLine(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_year_dummy_line.yaml")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidShell(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_year.sh")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidShellEmptyLine(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_year_empty_line.sh")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testInvalidShell(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/no_license.sh")
        self.assertEqual(result.code, 1)
        self.assertRegex(result.message, "^License is not detected:")

    def testOneLinerShell(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/one_liner.sh")
        self.assertEqual(result.code, 1)
        self.assertRegex(result.message, "^License is detected, but wording is wrong:")

    def testValidShellWithDummyLine(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_year_dummy_line_shebang.sh")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidShellWithEmptyLine(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_year_empty_line_shebang.sh")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidXml(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_year.xml")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testOneLinerXml(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/one_liner.xml")
        self.assertEqual(result.code, 1)
        self.assertRegex(result.message, "^License is detected, but wording is wrong:")

    def testValidXmlMultilineDeclaration(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_year_multiline_declaration.xml")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidJava(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_year.java")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testValidInlineGo(self):
        checker = license_check.LicenseCheck(end_year=2020)
        result = checker.check_file("tests/valid_old_range_inline.go")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    # [2020] > 2020-2021
    def testConvertSingleYearToRangeJava(self):
        checker = license_check.LicenseCheck(end_year=2021)
        tempdir = tempfile.mkdtemp()
        outfile = tempdir + "/valid_old_year.java"
        checker.check_file("tests/valid_old_year.java", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("start_year"), "2020-")
        self.assertEqual(result.matcher.group("end_year"), "2021")
        os.remove(outfile)
        os.rmdir(tempdir)

    def testAddLicenseToXml(self):
        checker = license_check.LicenseCheck(end_year=2021)
        tempdir = tempfile.mkdtemp()
        outfile = tempdir + "/no_license.xml"
        checker.check_file("tests/no_license.xml", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("start_year"), "")
        self.assertEqual(result.matcher.group("end_year"), "2021")
        os.remove(outfile)
        os.rmdir(tempdir)

    def testAddLicenseToJava(self):
        checker = license_check.LicenseCheck(end_year=2021)
        tempdir = tempfile.mkdtemp()
        outfile = tempdir + "/no_license.java"
        checker.check_file("tests/no_license.java", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("start_year"), "")
        self.assertEqual(result.matcher.group("end_year"), "2021")
        os.remove(outfile)
        os.rmdir(tempdir)

    def testFixOneLinerInXml(self):
        checker = license_check.LicenseCheck(end_year=2022)
        tempdir = tempfile.mkdtemp()
        outfile_one_liner = tempdir + "/one_liner.xml"
        outfile_valid = tempdir + "/valid.xml"
        checker.check_file("tests/one_liner.xml", fix=True, outfile=outfile_one_liner)
        checker.check_file("tests/valid_old_year.xml", fix=True, outfile=outfile_valid)
        result = checker.check_file(outfile_one_liner)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        # Unlike testAddLicenseToShell, year 2020 should be picked up from existing one-liner
        self.assertEqual(result.matcher.group("start_year"), "2020, ")
        self.assertEqual(result.matcher.group("end_year"), "2022")
        # Assert that fix removed one liner and put full license on place of it
        with open(outfile_one_liner) as f1, open(outfile_valid) as f2:
            self.assertEqual(f1.read(), f2.read())
        os.remove(outfile_one_liner)
        os.remove(outfile_valid)
        os.rmdir(tempdir)

    def testAddLicenseToShell(self):
        checker = license_check.LicenseCheck(start_year=2019, end_year=2021)
        tempdir = tempfile.mkdtemp()
        outfile = tempdir + "/no_license.sh"
        checker.check_file("tests/no_license.sh", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("start_year"), "2019-")
        self.assertEqual(result.matcher.group("end_year"), "2021")
        os.remove(outfile)
        os.rmdir(tempdir)

    def testFixOneLinerInShell(self):
        checker = license_check.LicenseCheck(end_year=2021)
        tempdir = tempfile.mkdtemp()
        outfile_one_liner = tempdir + "/one_liner.sh"
        outfile_valid = tempdir + "/valid.sh"
        checker.check_file("tests/one_liner.sh", fix=True, outfile=outfile_one_liner)
        checker.check_file("tests/valid_old_year.sh", fix=True, outfile=outfile_valid)
        result = checker.check_file(outfile_one_liner)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        # Unlike testAddLicenseToShell, year 2020 should be picked up from existing one-liner, and propagated as range
        self.assertEqual(result.matcher.group("start_year"), "2020-")
        self.assertEqual(result.matcher.group("end_year"), "2021")
        # Assert that fix removed one liner and put full license on place of it
        with open(outfile_one_liner) as f1, open(outfile_valid) as f2:
            self.assertEqual(f1.read(), f2.read())
        os.remove(outfile_one_liner)
        os.remove(outfile_valid)
        os.rmdir(tempdir)

    # Test that "2014, 2016-2020" is converted to "2014, 2016-2021" in year 2021
    def testExtendRangeGo(self):
        checker = license_check.LicenseCheck(end_year=2021)
        tempdir = tempfile.mkdtemp()
        outfile = tempdir + "/valid_old_range_inline.go"
        checker.check_file("tests/valid_old_range_inline.go", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("start_year"), "2014, 2016-")
        self.assertEqual(result.matcher.group("end_year"), "2021")
        os.remove(outfile)
        os.rmdir(tempdir)

    # Test that "2014, 2016-2020" is converted to "2014, 2016-2020, 2022" in year 2022
    def testAddToRangeGo(self):
        checker = license_check.LicenseCheck(end_year=2022)
        tempdir = tempfile.mkdtemp()
        outfile = tempdir + "/valid_old_range_inline.go"
        checker.check_file("tests/valid_old_range_inline.go", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("start_year"), "2014, 2016-2020, ")
        self.assertEqual(result.matcher.group("end_year"), "2022")
        os.remove(outfile)
        os.rmdir(tempdir)

    # Test that "2014, 2016-2020" is converted to "2014, 2016-2019" in year 2019
    def testFixFutureYearGo(self):
        checker = license_check.LicenseCheck(end_year=2019)
        tempdir = tempfile.mkdtemp()
        outfile = tempdir + "/valid_old_range_inline.go"
        checker.check_file("tests/valid_old_range_inline.go", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("start_year"), "2014, 2016-")
        self.assertEqual(result.matcher.group("end_year"), "2019")
        os.remove(outfile)
        os.rmdir(tempdir)

    def testValidGoTemplate(self):
        checker = license_check.LicenseCheck(end_year=2022)
        result = checker.check_file("tests/templates/go_template_valid.yaml")
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")

    def testAddLicenseToGoTemplate(self):
        checker = license_check.LicenseCheck(end_year=2022)
        tempdir = tempfile.mkdtemp()
        # outfile must be in templates/ folder, for yaml to be recognized as go_template    
        os.mkdir(tempdir + "/templates")
        outfile = tempdir + "/templates/go_template_no_license.yaml"
        checker.check_file("tests/templates/go_template_no_license.yaml", fix=True, outfile=outfile)
        result = checker.check_file(outfile)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        self.assertEqual(result.matcher.group("start_year"), "")
        self.assertEqual(result.matcher.group("end_year"), "2022")
        os.remove(outfile)
        os.rmdir(tempdir + "/templates")
        os.rmdir(tempdir)

    def testFixOneLinerInGoTemplate(self):
        checker = license_check.LicenseCheck(end_year=2022)
        tempdir = tempfile.mkdtemp()
        # outfile must be in templates/ folder, for yaml to be recognized as go_template    
        os.mkdir(tempdir + "/templates")
        outfile_one_liner = tempdir + "/templates/go_template_one_liner.yaml"
        outfile_valid = tempdir + "/templates/go_template_valid.yaml"
        checker.check_file("tests/templates/go_template_one_liner.yaml", fix=True, outfile=outfile_one_liner)
        checker.check_file("tests/templates/go_template_valid.yaml", fix=True, outfile=outfile_valid)
        result = checker.check_file(outfile_one_liner)
        self.assertEqual(result.code, 0)
        self.assertRegex(result.message, "^License is up to date:")
        # Unlike testAddLicenseToShell, year 2020 should be picked up from existing one-liner
        self.assertEqual(result.matcher.group("start_year"), "2020, ")
        self.assertEqual(result.matcher.group("end_year"), "2022")
        # Assert that fix removed one liner and put full license on place of it
        with open(outfile_one_liner) as f1, open(outfile_valid) as f2:
            self.assertEqual(f1.read(), f2.read())
        os.remove(outfile_one_liner)
        os.remove(outfile_valid)
        os.rmdir(tempdir + "/templates")
        os.rmdir(tempdir)

    def testConvertInlineToBlockGo(self):
        checker = license_check.LicenseCheck(end_year=2020)
        tempdir = tempfile.mkdtemp()
        outfile = tempdir + "/valid_old_range_inline.go"
        checker.check_file("tests/valid_old_range_inline.go", fix=True, outfile=outfile)
        with open(outfile) as f1, open("tests/valid_old_range_block.go") as f2:
            self.assertEqual(f1.read(), f2.read())
        os.remove(outfile)
        os.rmdir(tempdir)


logging.basicConfig(level=logging.ERROR)
os.chdir(sys.path[0])
unittest.main()