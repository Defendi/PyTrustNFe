# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os, re

from lxml import etree

PATH = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(PATH, 'schemas/enviNFe_v4.00.xsd')

def valida_nfe(xml_nfe):
    nfe = etree.fromstring(xml_nfe)
    esquema = etree.XMLSchema(etree.parse(SCHEMA))
    esquema.validate(nfe)
    erros = [x.message for x in esquema.error_log]
    error_msg = '{field} inválido: {valor}.'
    unexpected = '{unexpected} não é esperado. O valor esperado é {expected}'
    namespace = '{http://www.portalfiscal.inf.br/nfe}'
    mensagens = []
    for erro in erros:
        campo = re.findall(r"'([^']*)'", erro)[0]
        nome = campo[campo.find('}') + 1:]
        valor = nfe.find('.//' + campo).text
        if 'Expected is' in erro:
            expected_name = re.findall('\(.*?\)', erro)
            valor = unexpected.format(unexpected=nome, expected=expected_name)
        mensagem = error_msg.format(field=campo.replace(namespace, ''),
                                    valor=valor)
        mensagens.append(mensagem)
    return "\n".join(mensagens)
