"""
Basic sanity tests for lxml package.
Tests C-backed (libxml2/libxslt) functionality without extra dependencies.
"""

from lxml import etree
from io import BytesIO


def test_version():
    """Test version is accessible."""
    assert hasattr(etree, 'LXML_VERSION')
    assert etree.LXML_VERSION is not None


def test_parse_string():
    """Test XML parsing from string (C-backed libxml2)."""
    xml_string = b"<root><child>text</child></root>"
    root = etree.fromstring(xml_string)
    
    assert root.tag == 'root'
    assert root[0].tag == 'child'
    assert root[0].text == 'text'


def test_create_element():
    """Test element creation (C-backed)."""
    root = etree.Element('root')
    child = etree.SubElement(root, 'child')
    child.text = 'Hello'
    
    assert root.tag == 'root'
    assert len(root) == 1
    assert root[0].text == 'Hello'


def test_element_attributes():
    """Test element attributes (C-backed)."""
    root = etree.Element('root', attrib={'id': '1', 'name': 'test'})
    
    assert root.get('id') == '1'
    assert root.get('name') == 'test'
    
    root.set('new_attr', 'value')
    assert root.get('new_attr') == 'value'


def test_xpath():
    """Test XPath queries (C-backed libxml2)."""
    xml = b"""
    <root>
        <item id="1">First</item>
        <item id="2">Second</item>
        <item id="3">Third</item>
    </root>
    """
    root = etree.fromstring(xml)
    
    # Find all items
    items = root.xpath('//item')
    assert len(items) == 3
    
    # Find by attribute
    item = root.xpath('//item[@id="2"]')
    assert len(item) == 1
    assert item[0].text == 'Second'


def test_tree_iteration():
    """Test tree iteration (C-backed)."""
    xml = b"<root><a><b/><c/></a><d/></root>"
    root = etree.fromstring(xml)
    
    # Iterate all elements
    tags = [elem.tag for elem in root.iter()]
    assert 'root' in tags
    assert 'a' in tags
    assert 'b' in tags


def test_serialize():
    """Test XML serialization (C-backed)."""
    root = etree.Element('root')
    child = etree.SubElement(root, 'child')
    child.text = 'content'
    
    xml_bytes = etree.tostring(root)
    assert b'<root>' in xml_bytes
    assert b'<child>content</child>' in xml_bytes


def test_pretty_print():
    """Test pretty printing (C-backed)."""
    root = etree.Element('root')
    etree.SubElement(root, 'child')
    
    pretty = etree.tostring(root, pretty_print=True)
    assert b'\n' in pretty


def test_html_parsing():
    """Test HTML parsing (C-backed libxml2)."""
    html = b"<html><body><p>Hello</p></body></html>"
    root = etree.HTML(html)
    
    assert root is not None
    paragraphs = root.xpath('//p')
    assert len(paragraphs) == 1


def test_namespace():
    """Test XML namespaces (C-backed)."""
    nsmap = {'ns': 'http://example.com/ns'}
    root = etree.Element('{http://example.com/ns}root', nsmap=nsmap)
    
    assert root.tag == '{http://example.com/ns}root'


def test_cdata():
    """Test CDATA sections (C-backed)."""
    root = etree.Element('root')
    root.text = etree.CDATA('Some <special> content')
    
    xml = etree.tostring(root)
    assert b'CDATA' in xml


def test_comments():
    """Test XML comments (C-backed)."""
    root = etree.Element('root')
    comment = etree.Comment('This is a comment')
    root.append(comment)
    
    xml = etree.tostring(root)
    assert b'<!--' in xml


def test_validation_wellformed():
    """Test well-formedness checking (C-backed)."""
    # Valid XML
    valid_xml = b"<root><child/></root>"
    root = etree.fromstring(valid_xml)
    assert root is not None
    
    # Invalid XML should raise
    invalid_xml = b"<root><child></root>"
    try:
        etree.fromstring(invalid_xml)
        assert False, "Should have raised"
    except etree.XMLSyntaxError:
        pass


def test_element_tree():
    """Test ElementTree operations (C-backed)."""
    root = etree.Element('root')
    tree = etree.ElementTree(root)
    
    assert tree.getroot() is root
    
    # Write to BytesIO
    buffer = BytesIO()
    tree.write(buffer)
    buffer.seek(0)
    assert b'<root' in buffer.read()


if __name__ == "__main__":
    test_version()
    test_parse_string()
    test_create_element()
    test_element_attributes()
    test_xpath()
    test_tree_iteration()
    test_serialize()
    test_pretty_print()
    test_html_parsing()
    test_namespace()
    test_cdata()
    test_comments()
    test_validation_wellformed()
    test_element_tree()
    print("All lxml tests passed!")

