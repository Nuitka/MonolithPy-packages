"""
Basic sanity tests for regex package.
Tests C-backed functionality without extra dependencies.
"""

import regex


def test_version():
    """Test version is accessible."""
    assert hasattr(regex, '__version__')
    assert regex.__version__ is not None


def test_basic_match():
    """Test basic pattern matching (C-backed)."""
    pattern = regex.compile(r'\d+')
    
    match = pattern.match('123abc')
    assert match is not None
    assert match.group() == '123'
    
    no_match = pattern.match('abc123')
    assert no_match is None


def test_search():
    """Test search functionality (C-backed)."""
    pattern = regex.compile(r'\d+')
    
    match = pattern.search('abc123def')
    assert match is not None
    assert match.group() == '123'


def test_findall():
    """Test findall functionality (C-backed)."""
    pattern = regex.compile(r'\d+')
    
    matches = pattern.findall('a1b2c3d4')
    assert matches == ['1', '2', '3', '4']


def test_finditer():
    """Test finditer functionality (C-backed)."""
    pattern = regex.compile(r'\d+')
    
    matches = list(pattern.finditer('a1b22c333'))
    assert len(matches) == 3
    assert matches[0].group() == '1'
    assert matches[1].group() == '22'
    assert matches[2].group() == '333'


def test_sub():
    """Test substitution (C-backed)."""
    pattern = regex.compile(r'\d+')
    
    result = pattern.sub('X', 'a1b2c3')
    assert result == 'aXbXcX'


def test_split():
    """Test split functionality (C-backed)."""
    pattern = regex.compile(r'\s+')
    
    result = pattern.split('hello   world  test')
    assert result == ['hello', 'world', 'test']


def test_groups():
    """Test capture groups (C-backed)."""
    pattern = regex.compile(r'(\w+)@(\w+)\.(\w+)')
    
    match = pattern.match('user@example.com')
    assert match is not None
    assert match.group(1) == 'user'
    assert match.group(2) == 'example'
    assert match.group(3) == 'com'
    assert match.groups() == ('user', 'example', 'com')


def test_named_groups():
    """Test named capture groups (C-backed)."""
    pattern = regex.compile(r'(?P<user>\w+)@(?P<domain>\w+)')
    
    match = pattern.match('john@example')
    assert match is not None
    assert match.group('user') == 'john'
    assert match.group('domain') == 'example'


def test_unicode():
    """Test Unicode support (C-backed)."""
    pattern = regex.compile(r'\p{L}+')  # Unicode letter category
    
    matches = pattern.findall('Hello Мир 世界')
    assert 'Hello' in matches
    assert 'Мир' in matches
    assert '世界' in matches


def test_fuzzy_matching():
    """Test fuzzy matching (regex-specific feature)."""
    # Allow up to 1 error
    pattern = regex.compile(r'(?:hello){e<=1}')
    
    assert pattern.match('hello') is not None
    assert pattern.match('hallo') is not None  # 1 substitution
    assert pattern.match('helo') is not None   # 1 deletion


def test_overlapping():
    """Test overlapping matches (regex-specific feature)."""
    pattern = regex.compile(r'\d{2}')
    
    # Non-overlapping
    matches = pattern.findall('12345')
    assert matches == ['12', '34']
    
    # Overlapping
    matches = pattern.findall('12345', overlapped=True)
    assert matches == ['12', '23', '34', '45']


def test_flags():
    """Test regex flags (C-backed)."""
    # Case insensitive
    pattern = regex.compile(r'hello', regex.IGNORECASE)
    assert pattern.match('HELLO') is not None
    
    # Multiline
    pattern = regex.compile(r'^line', regex.MULTILINE)
    matches = pattern.findall('line1\nline2\nline3')
    assert len(matches) == 3


def test_lookahead():
    """Test lookahead assertions (C-backed)."""
    # Positive lookahead
    pattern = regex.compile(r'\w+(?=@)')
    match = pattern.search('user@example.com')
    assert match.group() == 'user'
    
    # Negative lookahead
    pattern = regex.compile(r'\d+(?!\.)')
    matches = pattern.findall('1.5 2 3.14 4')
    assert '2' in matches
    assert '4' in matches


def test_lookbehind():
    """Test lookbehind assertions (C-backed)."""
    # Positive lookbehind
    pattern = regex.compile(r'(?<=\$)\d+')
    match = pattern.search('Price: $100')
    assert match.group() == '100'


if __name__ == "__main__":
    test_version()
    test_basic_match()
    test_search()
    test_findall()
    test_finditer()
    test_sub()
    test_split()
    test_groups()
    test_named_groups()
    test_unicode()
    test_fuzzy_matching()
    test_overlapping()
    test_flags()
    test_lookahead()
    test_lookbehind()
    print("All regex tests passed!")

