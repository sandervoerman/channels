from contextlib import redirect_stdout
from io import StringIO
from importlib import import_module
from unittest import TestCase, main
import mypy.api


class TestChannels(TestCase):
    def test_typing(self) -> None:
        args = ['--namespace-packages', '-c', 'import sav.channels']
        out, err, code = mypy.api.run(args)
        self.assertEqual(code, 0, msg=out+err)

    def test_examples(self) -> None:
        for i in range(1, 4):
            with self.subTest(example=i):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    import_module(f'docs.example{i}')
                with open(f'docs/example{i}.txt') as expected:
                    self.assertEqual(stdout.getvalue(), expected.read())


if __name__ == '__main__':
    main(verbosity=2)
