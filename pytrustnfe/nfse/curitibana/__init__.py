# -*- coding: utf-8 -*-

import logging
import os
import re
from lxml import etree

import suds
from OpenSSL import crypto
from base64 import b64encode
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.client import get_authenticated_client
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.assinatura import Assinatura
from pytrustnfe.xml.validate import pop_encoding

_logger = logging.getLogger(__name__)

def _validate(method, xml):
    path = os.path.join(os.path.dirname(__file__), 'templates')
    schema = os.path.join(path, '%s.xsd' % method)

    nfe = etree.fromstring(xml)
    esquema = etree.XMLSchema(etree.parse(schema))
    esquema.validate(nfe)
    erros = [x.message for x in esquema.error_log]
    return erros

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), 'templates')
    xml_send = render_xml(path, '%s.xml' % method, True, **kwargs)
    if method in ('RecepcionarLoteRps','CancelarNfse'):
        reference = ''
        if method == 'RecepcionarLoteRps':
            reference = '%s' % kwargs['nfse']['lista_rps'][0]['numero']
        signer = Assinatura(certificado.pfx, certificado.password)
        xml_send = signer.assina_xml(xml_send, reference)
#         xml_send = etree.tostring(xml_send)
        if method == 'CancelarNfse':
            xml_send = etree.fromstring(xml_send)
            Signature = xml_send.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
            Pedido = xml_send.find(".//{http://www.betha.com.br/e-nota-contribuinte-ws}Pedido")
            if Signature:
                Pedido.append(Signature)
            xml_send = etree.tostring(xml_send)
    else:
        xml_send = etree.tostring(xml_send)
    return xml_send

def _send(certificado, method, **kwargs):
    base_url = ''
    if kwargs['ambiente'] == 'producao':
        base_url = 'https://isscuritiba.curitiba.pr.gov.br/Iss.NfseWebService/nfsews.asmx'
    else:
        base_url = 'https://pilotoisscuritiba.curitiba.pr.gov.br/nfse_ws/nfsews.asmx'

    cert, key = extract_cert_and_key_from_pfx(
        certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
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
        header = '<cabecalho xmlns="http://www.betha.com.br/e-nota-contribuinte-ws" versao="2.02"><versaoDados>2.02</versaoDados></cabecalho>' #noqa
        response = getattr(client.service, method)(header, xml_send)
    except suds.WebFault, e:
        return {
            'sent_xml': xml_send,
            'received_xml': e.fault.faultstring,
            'object': None
        }
    response, obj = sanitize_response(response)
    return {
        'sent_xml': xml_send,
        'received_xml': response,
        'object': obj
    }

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, 'RecepcionarLoteRps', **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, 'RecepcionarLoteRps', **kwargs)

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, 'ConsultarLoteRps', **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, 'ConsultarLoteRps', **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, 'CancelarNfse', **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, 'CancelarNfse', **kwargs)

