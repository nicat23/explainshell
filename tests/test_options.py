import unittest

from explainshell import options, store, errors


class test_options(unittest.TestCase):
    def test_simple(self):
        s = "\t-a description"
        self.assertEqual(options.extract_option(s), (["-a"], []))

        s = "\t-a, description"
        self.assertEqual(options.extract_option(s), (["-a"], []))

        r = (["-a", "-b"], [])
        s = "\t-a, -b description"
        self.assertEqual(options.extract_option(s), r)

        s = "\t-a/-b description"
        self.assertEqual(options.extract_option(s), r)

        s = "\t-a -b description"
        self.assertEqual(options.extract_option(s), r)

        s = "\t-a     -b,-c,           -d description"
        self.assertEqual(options.extract_option(s), (["-a", "-b", "-c", "-d"], []))

        s = "\t--a, -b, --c-d description"
        self.assertEqual(options.extract_option(s), (["-b"], ["--a", "--c-d"]))

        s = "---c-d "
        self.assertEqual(options.extract_option(s), ([], []))

        s = "-c- "
        self.assertEqual(options.extract_option(s), ([], []))

    def test_option_arg(self):
        s = "\t-a FOO, -b=BAR, description"
        self.assertEqual(
            options.extract_option(s), ([("-a", "FOO"), ("-b", "BAR")], [])
        )

        s = "\t-a [FOO], -b[=BAR], description"
        self.assertEqual(
            options.extract_option(s), ([("-a", "FOO"), ("-b", "BAR")], [])
        )

        s = "\t-a<n>, -b=<BAR>, -C <ah>"
        self.assertEqual(
            options.extract_option(s), ([("-a", "n"), ("-b", "BAR"), ("-C", "ah")], [])
        )

        s = "\t--aa    FOO, --bb=BAR, description"
        self.assertEqual(
            options.extract_option(s), ([], [("--aa", "FOO"), ("--bb", "BAR")])
        )

        s = "-a or -b"
        self.assertEqual(options.extract_option(s), (["-a", "-b"], []))

    def test_pipe_separator(self):
        s = "-a|b"
        self.assertEqual(options.extract_option(s), (["-a", "b"], []))

        s = "-a|-b|--c|d"
        self.assertEqual(options.extract_option(s), (["-a", "-b", "d"], ["--c"]))

    def test_multiline_options(self):
        s = "\t-a, -b, \n-c, --ddd description"
        self.assertEqual(options.extract_option(s), (["-a", "-b", "-c"], ["--ddd"]))

    def test_multiline_desc(self):
        s = "\t-a, -b description\n\tmultiline\n  another line"
        self.assertEqual(options.extract_option(s), (["-a", "-b"], []))

    def test_not_an_option(self):
        self.assertEqual(options.extract_option("foobar"), ([], []))

    def test_no_hyphen(self):
        s = "\ta=b description"
        self.assertEqual(options.extract_option(s), ([], [("a", "b")]))

    def test_hyphen_in_arg(self):
        s = "-a=FOO-BAR, --aa=FOO-BAR"
        self.assertEqual(
            options.extract_option(s), ([("-a", "FOO-BAR")], [("--aa", "FOO-BAR")])
        )

        # s = '-a FOO-BAR, --aa FOO-BAR'
        # self.assertEqual(options.extract_option(s),
        #                  ([('-a', 'FOO-BAR')], [('--aa', 'FOO-BAR')]))

    def test_extract(self):
        p1 = store.paragraph(0, "<b>--test</b>=<u>arg</u>\ndesc", "", True)
        p2 = store.paragraph(1, "no options here", "", True)
        p3 = store.paragraph(2, "--foo-bar=&lt;arg&gt;\ndesc", "", True)

        m = store.manpage("", "", "", [p1, p2, p3], [])
        options.extract(m)
        r = m.options
        self.assertEqual(len(r), 2)
        self._extracted_from_test_extract_10(r, 0, p1, "--test")
        self._extracted_from_test_extract_10(r, 1, p3, "--foo-bar")

    # TODO Rename this here and in `test_extract`
    def _extracted_from_test_extract_10(self, r, arg1, arg2, arg3):
        self.assertEqual(r[arg1].text, arg2.text)
        self.assertEqual(r[arg1].short, [])
        self.assertEqual(r[arg1].long, [arg3])
        self.assertEqual(r[arg1].expectsarg, True)

    def test_help(self):
        s = "\t-?, --help description"
        self.assertEqual(options.extract_option(s), (["-?"], ["--help"]))

    def test_error_conditions(self):
        # Test invalid input types
        with self.assertRaises((TypeError, AttributeError)):
            options.extract_option(None)
        
        # Test empty string
        self.assertEqual(options.extract_option(""), ([], []))
        
        # Test malformed options
        self.assertEqual(options.extract_option("---invalid"), ([], []))
        self.assertEqual(options.extract_option("-"), ([], []))
