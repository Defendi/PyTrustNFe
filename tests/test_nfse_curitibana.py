import mock
import os.path
import unittest

from pytrustnfe.nfse.curitibana import xml_gerar_rps
from pytrustnfe.nfse.curitibana import xml_gerar_lote
from pytrustnfe.nfse.curitibana import send_lote
from pytrustnfe.nfse.curitibana import valid_xml
from pytrustnfe.certificado import Certificado

class test_nfse_curitibana(unittest.TestCase):

    caminho = os.path.dirname(__file__)

    def _get_rps(self):
        rps = {
            'numero': '1',
            'serie': '1',
            'tipo_rps': '1',
            'data_emissao': '2020-04-16T21:00:53',
            'natureza_operacao': '1',
            'optante_simples': '1', # 1 - Sim, 2 - Não
            'incentivador_cultural': '2',  # 2 - Não
            'status': '1',  # 1 - Normal
            'valor_servico': '100.00',
            'valor_deducao': '0.00',
            'numero_deducao': '0',
            'valor_pis': '0.00',
            'valor_cofins': '0.00',
            'valor_inss': '0.00',
            'valor_ir': '0.00',
            'valor_csll': '0.00',
            'iss_retido': '2',
            'valor_iss': '0.00',
            'valor_iss_retido': '0.00',
            'outras_retencoes': '0.00',
            'base_calculo': '100.00',
            'aliquota_iss': '2.0000',
            'valor_liquido': '2.00',
            'desconto_incondicionado': '0.00',
            'desconto_condicionado': '0.00',
            'codigo_servico': '1719',
            'codigo_tributacao_municipio': '',
            'descricao': 'Venda de Servico',
            'codigo_municipio': '4106902',
            'tomador': {
                'tipo_cpfcnpj': '2',
                'cnpj_cpf': '',
                'razao_social': 'Empresa de Teste Ltda',
                'logradouro': 'Rua XV',
                'numero': '1234',
                'complemento': 'Loja 1',
                'bairro': 'Centro',
                'cidade': '4106902',
                'pais': '1058',
                'uf': 'PR',
                'cep': '81150320',
                'telefone': '41992705320',
                'inscricao_municipal': '',
                'email': 'xxxxx@ctbdm.com.br',
            },
            'prestador': {
                'cnpj': '14793990000177',
                'inscricao_municipal': '17196308664',
            },
        }
        return rps

    def _get_lote(self,xml_rps):
        lote = {
            'numero_lote': '1',
            'inscricao_municipal': '17196308664',
            'cnpj_prestador': '14793990000177',
            'lista_rps': [xml_rps],
        }
        return lote

    def _get_certificado(self):
        pfx_source = open(os.path.join(self.caminho+'/cert', 'teste.pfx'),'rb').read()
        #pfx_password = os.path.join(self.caminho+'/cert', 'key.txt')
        return Certificado(pfx_source, '1234')

    def _get_valid_lote(self):
        res = {}
        res['Certificado'] = self._get_certificado() 
        rps = self._get_rps()
        res['xml_rps'] = xml_gerar_rps(res['Certificado'], rps=rps)
        lote = self._get_lote(res['xml_rps'])
        res['xml_lote'] = xml_gerar_lote(res['Certificado'], lote=lote)
        return res

    def test_valid_lote(self):
        NFSe_to_send = self._get_valid_lote()
        #return NFSe_to_send
        with open('/home/defendi/Documentos/rps.xml', 'w') as outxml:
            outxml.write(NFSe_to_send['xml_rps']+'\n')
        with open('/home/defendi/Documentos/lote.xml', 'w') as outxml:
            outxml.write(NFSe_to_send['xml_lote']+'\n')
        return send_lote(NFSe_to_send['Certificado'], xml=NFSe_to_send['xml_lote'], ambiente='homologacao')

def main():
    nfse = test_nfse_curitibana()
    ret = nfse.test_valid_lote()
    print(str(ret))


if __name__ == '__main__':
    main()
