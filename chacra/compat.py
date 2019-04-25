import sys

PY3 = sys.version_info[0] == 3

if PY3:
    def b_(s):
        return s.encode("utf-8")

else:
    def b_(s):
        return s

