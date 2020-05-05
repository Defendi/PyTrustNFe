import os
import operator
from OpenSSL import crypto
from base64 import b64encode
from suds.sax.text import Raw

from requests import Session
from requests.auth import HTTPBasicAuth

from zeep import Client
from zeep.transports import Transport
from zeep.wsse.signature import Signature
from requests.packages.urllib3 import disable_warnings

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura
from lxml import etree

def _set_lote_xml(lote,rps_list):
    rps = ''
    for item in rps_list:
        rps += item
    str_to_sch = "<ListaRps>loterps</ListaRps>"
    inicio = str(lote).find(str_to_sch)
    tamanho = len(str_to_sch)
    fim = inicio + tamanho
    if inicio > 0:
        res = lote[:inicio] + "<ListaRps>{}</ListaRps>".format(rps) + lote[fim:]
    else:
        res = False
    return res


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    xml_send = render_xml(path, "%s.xml" % method, True, **kwargs)
#     xml_send = etree.tostring(xml_send,encoding='unicode')
    reference = ""
    signer = Assinatura(certificado.pfx, certificado.password)
    if method == "Rps":
        xml_send = signer.assina_xml(xml_send, reference)
    elif method == "EnviarLoteRpsEnvio":
        xml_send = etree.tostring(xml_send,encoding='unicode')
        lista_rps = kwargs['lote']['lista_rps']
        xml_send = _set_lote_xml(xml_send,lista_rps)
        xml_send = etree.fromstring(xml_send)
        xml_send = signer.assina_xml(xml_send, "")
    else:
        xml_send = etree.tostring(xml_send,encoding='unicode')
    return xml_send

# def _send(certificado, method, **kwargs):
#     base_url = ""
#     if kwargs["ambiente"] == "producao":
#         base_url = "https://isscuritiba.curitiba.pr.gov.br/Iss.NfseWebService/nfsews.asmx?wsdl"
#     else:
#         base_url = "https://piloto-iss.curitiba.pr.gov.br/nfse_ws/nfsews.asmx?wsdl"  # noqa
# 
#     cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
#     cert, key = save_cert_key(cert, key)
#     
#     xml_send = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><RecepcionarLoteRps xmlns="http://www.e-governeapps2.com.br/">%s</RecepcionarLoteRps></soap:Body></soap:Envelope>""" % kwargs['xml']
#     xml_send = xml_send.encode()
#     buffer = io.BytesIO()
#     c = pycurl.Curl()
# 
#     c.setopt(c.URL, base_url)
#     c.setopt(pycurl.HTTPHEADER, [
#        'POST /nfse_ws/nfsews.asmx HTTP/1.1',
#        'Host: piloto-iss.curitiba.pr.gov.br',
#        'Content-Type: text/xml; charset=utf-8',
#        'Content-Length:%s' % len(xml_send),
#        'SOAPAction: "http://www.e-governeapps2.com.br/RecepcionarLoteRps"',
#     ])
#     c.setopt(c.POST, True)
#     c.setopt(c.SSLKEY,key)
#     c.setopt(c.SSLCERT,cert)
#     c.setopt(c.SSLCERTPASSWD,'1234')
#     c.setopt(c.POSTFIELDS, xml_send)
#     #c.setopt(c.RETURNTRANSFER, True)
#     c.setopt(c.SSL_VERIFYHOST, 2)
#     c.setopt(c.SSL_VERIFYPEER, False)
#     c.setopt(c.VERBOSE, True)
#     c.setopt(c.WRITEDATA, buffer)
#     c.perform()
# 
#     print('\n\nStatus: %d' % c.getinfo(c.RESPONSE_CODE))
#     print('TOTAL_TIME: %f' % c.getinfo(c.TOTAL_TIME))
#     c.close()
#     body = buffer.getvalue()
#     print(body.decode())
#     
#     return ''

# def _send(certificado, method, **kwargs):
#     base_url = ""
#     if kwargs["ambiente"] == "producao":
#         base_url = "https://isscuritiba.curitiba.pr.gov.br/Iss.NfseWebService/nfsews.asmx?wsdl"
#     else:
#         base_url = "https://piloto-iss.curitiba.pr.gov.br/nfse_ws/nfsews.asmx?WSDL"  # noqa
#  
#     cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
#     cert, key = save_cert_key(cert, key)
#  
#     #disable_warnings()
#     try:
#         client = get_authenticated_client(base_url, cert, key)
#         print(client)
#     except Exception as e: 
#         return str(e)
#     #_logger.info(str(client))
#     try:
#         xml_send = Raw(kwargs['xml'])
# #         header = '<cabecalho xmlns="http://www.betha.com.br/e-nota-contribuinte-ws" versao="2.02"><versaoDados>2.02</versaoDados></cabecalho>' #noqa
#         response = getattr(client.service, method)(xml=xml_send)
#     except Exception as e: 
#         return str(e)
#     
#     print(str(response))
#      
#     return False
#      
#     response, obj = sanitize_response(response)
#     return {
#         'sent_xml': xml_send,
#         'received_xml': response,
#         'object': obj
#     }

# def _send(certificado, method, **kwargs):
#     base_url = ""
#     if kwargs["ambiente"] == "producao":
#         base_url = "https://isscuritiba.curitiba.pr.gov.br/Iss.NfseWebService/nfsews.asmx?wsdl"
#     else:
#         base_url = "https://piloto-iss.curitiba.pr.gov.br/nfse_ws/nfsews.asmx?WSDL"  # noqa
# 
#     cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
#     cert, key = save_cert_key(cert, key)
# #     try:
#     client = get_authenticated_client(base_url, cert, key)
#     print(client)
# #     except Exception as e: 
# #         return {
# #             'sent_xml': kwargs.get('xml', False),
# #             'received_xml': str(e),
# #             'object': None
# #         }
# #     return ''
#     #_logger.info(str(client))
#     try:
#         xml_send = kwargs['xml']
#         #header = '<cabecalho xmlns="http://www.betha.com.br/e-nota-contribuinte-ws" versao="2.02"><versaoDados>2.02</versaoDados></cabecalho>' #noqa
#         response = getattr(client.service, method)(xml_send)
#     except Exception as e: 
#         return str(e)
#     return response

def _send(certificado, method, **kwargs):
    base_url = ""
    if kwargs["ambiente"] == "producao":
        base_url = "https://isscuritiba.curitiba.pr.gov.br/Iss.NfseWebService/nfsews.asmx?WSDL"
    else:
        base_url = "https://piloto-iss.curitiba.pr.gov.br/nfse_ws/nfsews.asmx?WSDL"  # noqa
 
    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    client = Client(wsdl=base_url, transport=transport, wsse=Signature(key, cert))
    
    for service in client.wsdl.services.values():
        for port in service.ports.values():
            operations = sorted(port.binding._operations.values(),key=operator.attrgetter('name'))

        for operation in operations:
            print("method :", operation.name)
            print("  input :", operation.input.signature())
            print()    

    xml_send = Raw(kwargs['xml'])
    
    response = client.service['RecepcionarXml'](metodo=method,xml=xml_send)
    return False


def xml_gerar_rps(certificado, **kwargs):
    return _render(certificado, "Rps", **kwargs)

def xml_gerar_lote(certificado, **kwargs):
    if "lote" in kwargs:
#         if "lista_rps" not in kwargs["lote"] or len(kwargs["lote"]["lista_rps"]) == 0:
#             kwargs["lista_rps"] = [xml_gerar_rps(certificado, **kwargs)]
        return _render(certificado, "EnviarLoteRpsEnvio", **kwargs)
    else:
        return False

def xml_gerar_lote_cancel(certificado, **kwargs):
    if "lote" in kwargs:
        return _render(certificado, "CancelarLoteNfseEnvio", **kwargs)
    else:
        return False


def send_lote(certificado, **kwargs):
    if "xml" in kwargs:
        return _send(certificado, "RecepcionarLoteRps", **kwargs)
    else:
        return {
            "sent_xml": False,
            "received_xml": 'XML não enviado',
            "object": None,
        }

def valid_xml(certificado, **kwargs):
    if "xml" in kwargs:
        return _send(certificado, "ValidarXml", **kwargs)
    else:
        return {
            "sent_xml": False,
            "received_xml": 'XML não enviado',
            "object": None,
        }

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "CancelarNfse", **kwargs)
