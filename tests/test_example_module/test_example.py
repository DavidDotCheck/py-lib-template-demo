# tests/test_example_module/test_example.py
# Author: {{project.author}} <{{project.email}}>

import sys
import pytest
from {{project.package_name}}.example_module import Example

def capture_print( function, *args):
    from io import StringIO
    capture = StringIO()
    sys.stdout = capture
    function( *args )
    sys.stdout = sys.__stdout__
    return capture
    

def test_example():
    example = Example()
    capture = capture_print( example.print_name )
    assert capture.getvalue() == "Example\n"

def test_example_name():
    example = Example("Test")
    assert example.name == "Test"

    
if __name__ == "__main__":
    pytest.main()
