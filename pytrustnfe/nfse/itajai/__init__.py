# -*- coding: utf-8 -*-
# © 2019 Alexandre Defendi
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import suds
import logging
import logging.config
from collections import deque
from lxml import etree
from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from zeep import Plugin

from OpenSSL import crypto

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.nfe.assinatura import Assinatura
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.client import get_authenticated_client

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

# logging.config.dictConfig({
#     'version': 1,
#     'formatters': {
#         'verbose': {
#             'format': '%(name)s: %(message)s'
#         }
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'zeep.transports': {
#             'level': 'DEBUG',
#             'propagate': True,
#             'handlers': ['console'],
#         },
#     }
# })

# Plugin do Zeep para incluir o namespace e gerar o log do envio
class MyLoggingPlugin(Plugin):

    def __init__(self, maxlen=1):
        self._buffer = deque([], maxlen)

    @property
    def last_sent(self):
        last_tx = self._buffer[-1]
        if last_tx:
            return last_tx['sent']

    @property
    def last_received(self):
        last_tx = self._buffer[-1]
        if last_tx:
            return last_tx['received']

    def ingress(self, envelope, http_headers, operation):
        last_tx = self._buffer[-1]
        last_tx['received'] = {
            'envelope': envelope,
            'http_headers': http_headers,
            'operation': operation,
        }
        _logger.info(etree.tostring(envelope, pretty_print=True))
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
#         try:
#             NFe = envelope[0][0][0][2]
#             if NFe:
#                 NFe.set('xmlns','http://www.portalfiscal.inf.br/nfe')
#         except:
#             pass
        self._buffer.append({
            'received': None,
            'sent': {
                'envelope': envelope,
                'http_headers': http_headers,
                'operation': operation,
            },
        })
        _logger.info(etree.tostring(envelope, pretty_print=True))
        return envelope, http_headers

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), 'templates')
    xml_send = render_xml(path, '%s.xml' % method, True, **kwargs)
    reference = ''
#     if method == 'RecepcionarLoteRps':
#         reference = 'lote%s' % kwargs['nfse']['numero_lote']
#         signer = Assinatura(certificado.pfx, certificado.password)
#         xml_send = signer.assina_xml(xml_send, reference)
# #         if method == 'CancelarNfse':
# #             xml_send = etree.fromstring(xml_send)
# #             Signature = xml_send.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
# #             Pedido = xml_send.find(".//{http://www.betha.com.br/e-nota-contribuinte-ws}Pedido")
# #             if Signature:
# #                 Pedido.append(Signature)
# #             xml_send = etree.tostring(xml_send)
#     else:
#         xml_send = etree.tostring(xml_send)
    xml_send = '<?xml version="1.0" encoding="utf-8"?>'+etree.tostring(xml_send)
    return xml_send

def _send(certificado, method, **kwargs):
    base_url = ''
    if kwargs['ambiente'] == 'producao':
        base_url = 'https://nfse.itajai.sc.gov.br/nfse_integracao/Services?wsdl'
    else:
        base_url = 'http://nfse-teste.publica.inf.br/nfse_integracao/Services?wsdl'

    xml_send = '<![CDATA['+kwargs['xml'].decode("utf-8")+']]>'

    cert, key = extract_cert_and_key_from_pfx(
        certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    history = MyLoggingPlugin()
    
    client = Client(base_url, transport=transport, plugins=[history])

    print(client)

    response = client.service[method](xml_send)

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

