@pytest.mark.parametrize('input', testFiles)

def test_validation_outcome(input):
    """
    Tests validation outcome against known validity (JP2)
    """
    fName = os.path.basename(input)
    outIsolyzer = checkOneFile(input, 'jp2')
    if fName in validityLookupJP2.keys():
        isValid = validityLookupJP2[fName]
        assert outIsolyzer.findtext('./isValid') == isValid

def test_xml_is_valid(capsys):
    """
    Run checkfiles function on all files in test corpus and
    verify resulting XML output validates against XSD schema
    """
    config.VALIDATION_FORMAT = "jp2"
    checkFiles(config.INPUT_RECURSIVE_FLAG, True, testFiles)
    
    # Capture output from stdout
    captured = capsys.readouterr()
    xmlOut = captured.out
    # Parse XSD schema
    xmlschema_doc = etree.parse(xsdFile)
    xmlschema = etree.XMLSchema(xmlschema_doc)
    # Parse XML
    xml_doc = etree.fromstring(xmlOut.encode())
    assert xmlschema.validate(xml_doc)

