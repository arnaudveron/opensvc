import re
from functools import total_ordering

_semver_re = re.compile(
    r"""
    ^
    (?P<major>0|[1-9]\d*)\.
    (?P<minor>0|[1-9]\d*)\.
    (?P<patch>0|[1-9]\d*)
    (?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?
    (?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?
    $""",
    re.VERBOSE,
)

@total_ordering
class Semver(object):
    """
    Represents a semantic version as defined by the Semantic Versioning 2.0.0 standard.

    This class provides functionalities to create, parse, and compare semantic version strings.
    Semantic versioning is a versioning scheme intended for managing dependencies in software projects.
    It follows the format `MAJOR.MINOR.PATCH` where changes to each segment indicate specific types of updates.
    Additionally, the class supports optional prerelease and build metadata fields that allow to specify
    more detailed versioning information.

    :ivar major: The major version number. Incremented for incompatible changes.
    :type major: int
    :ivar minor: The minor version number. Incremented for backward-compatible functionality.
    :type minor: int
    :ivar patch: The patch version number. Incremented for backward-compatible bug fixes.
    :type patch: int
    :ivar prerelease: An optional prerelease identifier string (e.g., alpha, beta).
    :type prerelease: str
    :ivar build: An optional build metadata string (e.g., build identifiers for internal use).
    :type build: str
    """
    def __init__(self, major=0, minor=0, patch=0, prerelease=None, build=None):
        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)
        self.prerelease = prerelease or None
        self.build = build or None

    def __str__(self):
        s = "%d.%d.%d" % (self.major, self.minor, self.patch)
        if self.prerelease:
            s += "-%s" % self.prerelease
        if self.build:
            s += "+%s" % self.build
        return s

    @classmethod
    def parse(cls, s):
        if not isinstance(s, str):
            return cls()
        m = re.match(_semver_re, s)
        if not m:
            raise ValueError("Invalid semver")
        return cls(
            major=int(m.group("major")),
            minor=int(m.group("minor")),
            patch=int(m.group("patch")),
            prerelease=m.group("prerelease"),
            build=m.group("buildmetadata"))

    def __eq__(self, other):
        if not isinstance(other, Semver):
            return False
        if (self.major, self.minor, self.patch, self.prerelease) == (other.major, other.minor, other.patch, other.prerelease):
            return True
        return False

    def __lt__(self, other):
        if not isinstance(other, Semver):
            return NotImplemented
        if self.major < other.major:
            return True
        elif self.major == other.major:
            if self.minor < other.minor:
                return True
            elif self.minor == other.minor:
                if self.patch < other.patch:
                    return True
                elif self.patch == other.patch:
                    return self._parse_prerelease() < other._parse_prerelease()

        return False

    def _parse_prerelease(self):
        """
        Parses the prerelease component of a version string into a tuple
        that can be used for comparing versions by precedence according to
        the https://semver.org rules.

        The method differentiates between numeric and alphanumeric
        identifiers in the prerelease string, and constructs a precedence
        tuple accordingly.

        :return: A tuple representing the parsed prerelease component
                 with numeric and alphanumeric identifiers.
        :rtype: tuple
        """
        if not self.prerelease:
            return (1,)  # no prerelease = highest precedence

        parts = []
        for p in self.prerelease.split("."):
            if p.isdigit():
                parts.append((0, int(p)))  # numeric identifiers
            else:
                parts.append((1, p))  # alphanumeric identifiers
        return (0, parts)

    def __hash__(self):
        return hash((self.major, self.minor, self.patch, self.prerelease))

def as_semver(s):
    """
    Do our best to convert a string to a semver object from calendar versioning.
    Remove removing leading zeros from major, minor, patch version components
    before the first "-", or "+", if present.
    Docker example: 17.05.0-ce -> 17.5.0-ce.
    """
    has_release = False
    has_build = False
    suffix = ""
    if '-' in s:
        has_release = True
        base, suffix = s.split('-', 1)
    elif '+' in s:
        has_build = True
        base, suffix = s.split('+', 1)
    else:
        base = s
    clean_base = re.sub(r'(^|\.)0+(?=\d)', r'\1', base)
    if has_release:
        clean_v = "%s-%s" % (clean_base, suffix)
    elif has_build:
        clean_v = "%s+%s" % (clean_base, suffix)
    else:
        clean_v = clean_base
    return Semver.parse(clean_v)
