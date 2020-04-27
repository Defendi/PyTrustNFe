import logging
import os
import re
from lxml import etree

import suds
from requests.packages.urllib3 import disable_warnings

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura
from pytrustnfe.client import get_authenticated_client

_logger = logging.getLogger(__name__)

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    xml_send = render_xml(path, "%s.xml" % method, True, **kwargs)
#     xml_send = etree.tostring(xml_send,encoding='unicode')
    reference = ""
    signer = Assinatura(certificado.pfx, certificado.password)
    xml_send = signer.assina_xml(xml_send, reference)
    return xml_send

def _send(certificado, method, **kwargs):
    base_url = ""
    if kwargs["ambiente"] == "producao":
        base_url = "https://isscuritiba.curitiba.pr.gov.br/Iss.NfseWebService/nfsews.asmx?wsdl"
    else:
        base_url = "https://piloto-iss.curitiba.pr.gov.br/nfse_ws/nfsews.asmx?WSDL"  # noqa

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    try:
        client = get_authenticated_client(base_url, cert, key)
    except Exception as e: 
        return {
            'sent_xml': kwargs.get('xml', False),
            'received_xml': str(e),
            'object': None
        }
    #_logger.info(str(client))
    try:
        xml_send = kwargs['xml']
#         header = '<cabecalho xmlns="http://www.betha.com.br/e-nota-contribuinte-ws" versao="2.02"><versaoDados>2.02</versaoDados></cabecalho>' #noqa
        response = getattr(client.service, method)(xml=xml_send)
    except:
        return {
            'sent_xml': xml_send,
            'received_xml': e.fault.faultstring,
            'object': None
        }
    print(str(response))
    
    return False
    
    response, obj = sanitize_response(response)
    return {
        'sent_xml': xml_send,
        'received_xml': response,
        'object': obj
    }


def xml_gerar_rps(certificado, **kwargs):
    return _render(certificado, "Rps", **kwargs)

def xml_gerar_lote(certificado, **kwargs):
    if "lote" in kwargs:
#         if "lista_rps" not in kwargs["lote"] or len(kwargs["lote"]["lista_rps"]) == 0:
#             kwargs["lista_rps"] = [xml_gerar_rps(certificado, **kwargs)]
        return _render(certificado, "EnviarLoteRpsEnvio", **kwargs)
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
