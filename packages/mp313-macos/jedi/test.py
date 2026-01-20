"""
Basic sanity tests for jedi package.
Tests code completion and analysis functionality without extra dependencies.
"""

import jedi


def test_version():
    """Test version is accessible."""
    assert hasattr(jedi, '__version__')
    assert jedi.__version__ is not None


def test_script_creation():
    """Test Script object creation."""
    source = "import os\nos.path."
    script = jedi.Script(source)
    assert script is not None


def test_completions():
    """Test code completions."""
    source = "import os\nos.path.j"
    script = jedi.Script(source)
    completions = script.complete(2, 10)
    
    assert completions is not None
    assert len(completions) > 0
    
    # Should find 'join'
    names = [c.name for c in completions]
    assert 'join' in names


def test_goto_definitions():
    """Test goto definitions."""
    source = """
def my_function():
    pass

my_function()
"""
    script = jedi.Script(source)
    definitions = script.goto(5, 5)
    
    assert definitions is not None
    assert len(definitions) > 0


def test_references():
    """Test finding references."""
    source = """
x = 1
y = x + 1
z = x * 2
"""
    script = jedi.Script(source)
    references = script.get_references(2, 1)
    
    assert references is not None
    assert len(references) >= 2  # Definition and at least one usage


def test_signatures():
    """Test function signatures."""
    source = "print("
    script = jedi.Script(source)
    signatures = script.get_signatures(1, 6)
    
    assert signatures is not None
    # print should have a signature
    if len(signatures) > 0:
        assert signatures[0].name == 'print'


def test_infer():
    """Test type inference."""
    source = """
x = [1, 2, 3]
x
"""
    script = jedi.Script(source)
    names = script.infer(3, 1)
    
    assert names is not None


def test_names():
    """Test getting all names in source."""
    source = """
def foo():
    pass

class Bar:
    def method(self):
        pass

x = 1
"""
    script = jedi.Script(source)
    names = script.get_names()
    
    assert names is not None
    name_list = [n.name for n in names]
    assert 'foo' in name_list
    assert 'Bar' in name_list


def test_completion_with_context():
    """Test completions with different contexts."""
    # String method completions
    source = '"hello".'
    script = jedi.Script(source)
    completions = script.complete(1, 9)
    
    names = [c.name for c in completions]
    assert 'upper' in names
    assert 'lower' in names


def test_builtin_completions():
    """Test completions for builtins."""
    source = "len"
    script = jedi.Script(source)
    completions = script.complete(1, 3)
    
    assert completions is not None


def test_import_completions():
    """Test import completions."""
    source = "import o"
    script = jedi.Script(source)
    completions = script.complete(1, 9)
    
    names = [c.name for c in completions]
    assert 'os' in names


def test_project():
    """Test Project creation."""
    project = jedi.Project('.')
    assert project is not None


if __name__ == "__main__":
    test_version()
    test_script_creation()
    test_completions()
    test_goto_definitions()
    test_references()
    test_signatures()
    test_infer()
    test_names()
    test_completion_with_context()
    test_builtin_completions()
    test_import_completions()
    test_project()
    print("All jedi tests passed!")

