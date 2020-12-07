import tempfile
import os.path
import unittest
from lxml import etree
from pytrustnfe.nfe.danfe_simplificado import danfe_simplificado
from pytrustnfe.nfe.danfe import danfe
from reportlab.lib.pagesizes import A4,A5,A6

file_name = next(tempfile._get_candidate_names()) + '.pdf'
file_path = tempfile.gettempdir()+'/'+ file_name

print(file_name)

path_xml = '/home/defendi/Downloads'
xml_string = open(os.path.join(path_xml, 'NFe00022545.xml'), "r").read()

xml_element = etree.fromstring(xml_string)
# oDanfe = danfe_simplificado(list_xml=[xml_element],sizepage=A6,rascunho=False)
oDanfe = danfe(list_xml=[xml_element],sizepage=A6,rascunho=False)

f = open(file_path,'wb')
oDanfe.writeto_pdf(f)
