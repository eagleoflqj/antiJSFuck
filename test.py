import re
import unittest

import execjs
import requests
from parameterized import parameterized

from antijsfuck import fight

jsfuck_source = 'https://raw.githubusercontent.com/aemkei/jsfuck/master/jsfuck.js'
jsfuck_test_source = 'https://raw.githubusercontent.com/aemkei/jsfuck/master/test/jsfuck_test.js'

jsfuck = requests.get(jsfuck_source).text
jsfuck = re.sub(r'^[\s\S]*?\(', 'jsfuck=(', jsfuck, 1)
jsfuck = re.sub(r'replaceStrings\(\);[\s\S]*$',
                'replaceStrings();return encode;})()', jsfuck, 1)
context = execjs.get().compile(jsfuck)
jsfuck_test = requests.get(jsfuck_test_source).text
cases = re.findall(r"createTest\(('.*')\);", jsfuck_test) + \
    [repr(chr(c)) for c in range(32, 127)]


class Test(unittest.TestCase):

    @parameterized.expand(cases)
    def test(self, raw_string):
        string = eval(raw_string)
        fucked = context.call('jsfuck', string, 1, 1)
        self.assertEqual(string, fight(fucked).code, raw_string)


if __name__ == '__main__':
    unittest.main()
