# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
import requests
import hashlib
import binascii
from lxml import etree
from .patch import has_patch
from collections import deque
from urllib.parse import urlparse
from .assinatura import Assinatura
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.utils import gerar_chave, ChaveNFe
from pytrustnfe.Servidores import localizar_url, localizar_qrcode
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Zeep
from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from zeep import Plugin

_logger = logging.getLogger(__name__)

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
        try:
            NFe = envelope[0][0][0][2]
            if NFe:
                NFe.set('xmlns','http://www.portalfiscal.inf.br/nfe')
        except:
            pass
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

def _generate_nfe_id(**kwargs):
    for item in kwargs['NFes']:
        vals = {
            'cnpj': item['infNFe']['emit']['cnpj_cpf'],
            'estado': item['infNFe']['ide']['cUF'],
            'emissao': '%s%s' % (item['infNFe']['ide']['dhEmi'][2:4],
                                 item['infNFe']['ide']['dhEmi'][5:7]),
            'modelo': item['infNFe']['ide']['mod'],
            'serie': item['infNFe']['ide']['serie'],
            'numero': item['infNFe']['ide']['nNF'],
            'tipo': item['infNFe']['ide']['tpEmis'],
            'codigo': item['infNFe']['ide']['cNF'],
        }
        chave_nfe = ChaveNFe(**vals)
        chave_nfe = gerar_chave(chave_nfe, 'NFe')
        item['infNFe']['Id'] = chave_nfe
        item['infNFe']['ide']['cDV'] = chave_nfe[len(chave_nfe) - 1:]

def _add_qrCode(xml, **kwargs):
    xml = etree.fromstring(xml)
    infnfesupl = etree.Element('infNFeSupl')
    qrcode = etree.Element('qrCode')
    urlChave = etree.Element('urlChave')
    qrcode_version = '2'
    inf_nfe = kwargs['NFes'][0]['infNFe']
    nfe = xml.find(".//{http://www.portalfiscal.inf.br/nfe}NFe")
    csc = inf_nfe['codigo_seguranca']['csc']
    chave_nfe = inf_nfe['Id'][3:]
    ambiente = kwargs['ambiente']
    qr_code_url = False
    if inf_nfe['ide']['tpEmis'] == 1:
        qr_code_url = '{ch}|{vr}|{amb}|1'.format(
            ch = chave_nfe, 
            vr = qrcode_version,
            amb = ambiente
        )
    else:
        dig_val = binascii.hexlify(xml.find(
            ".//{http://www.w3.org/2000/09/xmldsig#}DigestValue").text.encode()).decode().upper()
        diaEmis = str(inf_nfe['ide']['dhEmi'])[8:10] 
        totalNF = str(inf_nfe['total']['vNF'])
        qr_code_url = '{ch}|{vr}|{amb}|{dia}|{total}|{digest}|1'.format(
            ch = chave_nfe, 
            vr = qrcode_version,
            amb = ambiente,
            dia = diaEmis,
            total = totalNF,
            digest = dig_val,
        )
        
    qr_code_url_csc = qr_code_url + csc
    qr_code_c_hash = hashlib.sha1(qr_code_url_csc.encode()).hexdigest().upper()
    qr_code_server = localizar_qrcode(kwargs['estado'], ambiente)
    QR_code_url = "{server}?p={url}|{hash}".format(
        server = qr_code_server,
        url = qr_code_url,
        hash = qr_code_c_hash
    )
    parsed_uri = urlparse(qr_code_server)
    url_consulta_chave = '{uri.scheme}://{uri.netloc}/nfce/consulta'.format(uri=parsed_uri)
    urlChave.text = url_consulta_chave
    qrcode.text = QR_code_url
    
    infnfesupl.append(qrcode)
    infnfesupl.append(urlChave)
    nfe.insert(1, infnfesupl)
    return etree.tostring(xml, encoding=str)

def _render(certificado, method, sign, **kwargs):
    path = os.path.join(os.path.dirname(__file__), 'templates')
    xmlElem_send = render_xml(path, '%s.xml' % method, True, **kwargs)

    modelo = xmlElem_send.find(".//{http://www.portalfiscal.inf.br/nfe}mod")
    modelo = modelo.text if modelo is not None else '55'

    if sign:
        signer = Assinatura(certificado.pfx, certificado.password)
        if method == 'NfeInutilizacao':
            xml_send = signer.assina_xml(xmlElem_send, kwargs['obj']['id'])
        if method == 'NfeAutorizacao':
            xml_send = signer.assina_xml(xmlElem_send, kwargs['NFes'][0]['infNFe']['Id'])
            if modelo == '65':
                xml_send = _add_qrCode(xml_send, **kwargs)
        elif method == 'RecepcaoEvento':
            xml_send = signer.assina_xml(
                xmlElem_send, kwargs['eventos'][0]['Id'])
        elif method == 'RecepcaoEventoManifesto':
            xml_send = signer.assina_xml(
                xmlElem_send, kwargs['manifesto']['identificador'])
    else:
        xml_send = etree.tostring(xmlElem_send, encoding=str)
    return xml_send

def _get_session(certificado):
    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    session = Session()
    session.cert = (cert, key)
    session.verify = False
    return session

def _get_client(base_url, transport):
    history = MyLoggingPlugin()
    client = Client(base_url, transport=transport, plugins=[history])
    port = next(iter(client.wsdl.port_types))
    first_operation = [x for x in iter(client.wsdl.port_types[port].operations) if "zip" not in x.lower()][0]
    return first_operation, client

def _send(certificado, method, **kwargs):
    xml_send = kwargs["xml"]
    base_url = localizar_url(
        method,  kwargs['estado'], kwargs['modelo'], kwargs['ambiente'])

    session = _get_session(certificado)
    patch = has_patch(kwargs['estado'], method)
    if patch:
        return patch(session, xml_send, kwargs['ambiente'])
    transport = Transport(session=session)
    try:
        first_op, client = _get_client(base_url, transport)
    except Exception as e:
        return {
            'sent_xml': xml_send,
            'sent_raw_xml': False,
            'received_xml': str(e),
            'object': None,
        }
    return _send_zeep(first_op, client, xml_send)
    
def _send_zeep(first_operation, client, xml_send):
    parser = etree.XMLParser(strip_cdata=False)
    xml = etree.fromstring(xml_send, parser=parser)

    namespaceNFe = xml.find(".//{http://www.portalfiscal.inf.br/nfe}NFe")
    if namespaceNFe is not None:
        namespaceNFe.set('xmlns', 'http://www.portalfiscal.inf.br/nfe')

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    with client.settings(raw_response=True):
        response = client.service[first_operation](xml)
        response, obj = sanitize_response(response.text)
        return {
            'sent_xml': xml_send,
            'received_xml': response,
            'object': obj.Body.getchildren()[0]
        }

def xml_autorizar_nfe(certificado, **kwargs):
    _generate_nfe_id(**kwargs)
    return _render(certificado, 'NfeAutorizacao', True, **kwargs)

def autorizar_nfe(certificado, **kwargs):  # Assinar
    if "xml" not in kwargs:
        kwargs['xml'] = xml_autorizar_nfe(certificado, **kwargs)
    if "err108" in kwargs:
        xml = """<env:Envelope xmlns:env='http://www.w3.org/2003/05/soap-envelope'><env:Body xmlns:env='http://www.w3.org/2003/05/soap-envelope'><nfeResultMsg xmlns='http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4'><retEnviNFe versao='4.00' xmlns='http://www.portalfiscal.inf.br/nfe'><tpAmb>1</tpAmb><verAplic>PR-v4_1_9</verAplic><cStat>108</cStat><xMotivo>Servico Paralisado Momentaneamente (curto prazo)</xMotivo><cUF>41</cUF><dhRecbto>2018-10-13T11:19:00-03:00</dhRecbto></retEnviNFe></nfeResultMsg></env:Body></env:Envelope>"""       
        response, obj = sanitize_response(xml)
        return {
            'sent_xml': kwargs['xml'],
            'sent_raw_xml': False,
            'received_xml': response,
            'object': obj.Body.getchildren()[0]
        }
    else:
        return _send(certificado, 'NfeAutorizacao', **kwargs)

def xml_retorno_autorizar_nfe(certificado, **kwargs):
    return _render(certificado, 'NfeRetAutorizacao', False, **kwargs)

def retorno_autorizar_nfe(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_retorno_autorizar_nfe(certificado, **kwargs)
    return _send(certificado, 'NfeRetAutorizacao', **kwargs)

def xml_recepcao_evento_cancelamento(certificado, **kwargs):  # Assinar
    return _render(certificado, 'RecepcaoEvento', True, **kwargs)

def recepcao_evento_cancelamento(certificado, **kwargs):  # Assinar
    if "xml" not in kwargs:
        kwargs['xml'] = xml_recepcao_evento_cancelamento(certificado, **kwargs)
    return _send(certificado, 'RecepcaoEvento', **kwargs)

def xml_inutilizar_nfe(certificado, **kwargs):
    return _render(certificado, 'NfeInutilizacao', True, **kwargs)

def inutilizar_nfe(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_inutilizar_nfe(certificado, **kwargs)
    return _send(certificado, 'NfeInutilizacao', **kwargs)

def xml_consultar_protocolo_nfe(certificado, **kwargs):
    return _render(certificado, 'NfeConsultaProtocolo', False, **kwargs)

def consultar_protocolo_nfe(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_consultar_protocolo_nfe(certificado, **kwargs)
    return _send(certificado, 'NfeConsultaProtocolo', **kwargs)

def xml_nfe_status_servico(certificado, **kwargs):
    return _render(certificado, 'NfeStatusServico', False, **kwargs)

def nfe_status_servico(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_nfe_status_servico(certificado, **kwargs)
    return _send(certificado, 'NfeStatusServico', **kwargs)

def xml_consulta_cadastro(certificado, **kwargs):
    return _render(certificado, 'NfeConsultaCadastro', False, **kwargs)

def consulta_cadastro(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_consulta_cadastro(certificado, **kwargs)
        kwargs['modelo'] = '55'
    return _send(certificado, 'NfeConsultaCadastro', **kwargs)

def xml_recepcao_evento_carta_correcao(certificado, **kwargs):  # Assinar
    return _render(certificado, 'RecepcaoEvento', True, **kwargs)

def recepcao_evento_carta_correcao(certificado, **kwargs):  # Assinar
    if "xml" not in kwargs:
        kwargs['xml'] = xml_recepcao_evento_carta_correcao(
            certificado, **kwargs)
    return _send(certificado, 'RecepcaoEvento', **kwargs)

def xml_recepcao_evento_manifesto(certificado, **kwargs):  # Assinar
    return _render(certificado, 'RecepcaoEvento', True, **kwargs)

def recepcao_evento_manifesto(certificado, **kwargs):  # Assinar
    if "xml" not in kwargs:
        kwargs['xml'] = xml_recepcao_evento_manifesto(certificado, **kwargs)
    return _send(certificado, 'RecepcaoEvento', **kwargs)

def xml_consulta_distribuicao_nfe(certificado, **kwargs):  # Assinar
    return _render(certificado, 'NFeDistribuicaoDFe', False, **kwargs)

def consulta_distribuicao_nfe(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_consulta_distribuicao_nfe(certificado, **kwargs)
    return _send_v310(certificado, **kwargs)

def xml_download_nfe(certificado, **kwargs):  # Assinar
    return _render(certificado, 'NFeDistribuicaoDFe', False, **kwargs)

def download_nfe(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs['xml'] = xml_download_nfe(certificado, **kwargs)
    return _send_v310(certificado, **kwargs)

def _send_v310(certificado, **kwargs):
    xml_send = kwargs["xml"]
    base_url = localizar_url(
        'NFeDistribuicaoDFe',  kwargs['estado'], kwargs['modelo'],
        kwargs['ambiente'])

    cert, key = extract_cert_and_key_from_pfx(
        certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    xml = etree.fromstring(xml_send)
    xml_um = etree.fromstring('<nfeCabecMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/"><cUF>%s</cUF><versaoDados>1.00</versaoDados></nfeCabecMsg>' % kwargs['estado'])
    history = MyLoggingPlugin()
    client = Client(base_url, transport=transport, plugins=[history])

    port = next(iter(client.wsdl.port_types))
    first_operation = next(iter(client.wsdl.port_types[port].operations))
    with client.settings(raw_response=True):
        response = client.service[first_operation](nfeDadosMsg=xml, _soapheaders=[xml_um])
        response, obj = sanitize_response(response.text)
        return {
            'sent_xml': xml_send,
            'received_xml': response,
            'object': obj.Body.nfeDistDFeInteresseResponse.nfeDistDFeInteresseResult
        }