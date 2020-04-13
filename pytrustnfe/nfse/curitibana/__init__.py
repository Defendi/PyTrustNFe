# © 2020 Alexandre Defendi
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import suds
from pytrustnfe.client import get_authenticated_client
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.nfe.assinatura import Assinatura


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    xml_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    reference = ""
    if method == "CancelarNfse":
        reference = "Cancelamento_NF%s" % kwargs["cancelamento"]["numero_nfse"]

    signer = Assinatura(certificado.pfx, certificado.password)
    xml_send = signer.assina_xml(xml_send, reference)
    return xml_send.encode("utf-8")

def _send(certificado, method, **kwargs):
    base_url = ""
    if kwargs["ambiente"] == "producao":
        base_url = "https://isscuritiba.curitiba.pr.gov.br/Iss.NfseWebService/nfsews.asmx?wsdl"
    else:
        base_url = "https://piloto-iss.curitiba.pr.gov.br/nfse_ws/nfsews.asmx?wsdl"  # noqa

    xml_send = kwargs["xml"].decode("utf-8")
    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    try:
        client = get_authenticated_client(base_url, cert, key)
        response = getattr(client.service, method)(xml_send)
    except suds.WebFault as e:
        return {
            "sent_xml": str(xml_send),
            "received_xml": str(e.fault.faultstring),
            "object": None,
        }
    except Exception as e:
        return {
            "sent_xml": str(xml_send),
            "received_xml": str(e),
            "object": None,
        }

    response, obj = sanitize_response(response)
    return {"sent_xml": str(xml_send), "received_xml": str(response), "object": obj}


def xml_gerar_rps(certificado, **kwargs):
    return _render(certificado, "Rps", **kwargs)

def xml_gerar_lote(certificado, **kwargs):
    if "lote" in kwargs:
        if "lista_rps" not in kwargs["lote"] or len(kwargs["lote"]["lista_rps"]) == 0:
            kwargs["lista_rps"] = [xml_gerar_rps(certificado, **kwargs)]
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

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)


def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "CancelarNfse", **kwargs)
