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
            'valor_pis': '0.00',
            'valor_cofins': '0.00',
            'valor_inss': '0.00',
            'valor_ir': '0.00',
            'valor_csll': '0.00',
            'outras_retencoes': '0.00',
            'iss_retido': '2',
            'valor_iss': '0.00',
            'valor_iss_retido': '0.00',
            'desconto_incondicionado': '0.00',
            'desconto_condicionado': '0.00',
            'base_calculo': '100.00',
            'aliquota_iss': '2.0000',
            'valor_liquido': '2.00',
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

    def _get_valid(self):
        xmlString = """<RecepcionarLoteRps xmlns="http://www.e-governeapps2.com.br/"><EnviarLoteRpsEnvio xmlns="http://isscuritiba.curitiba.pr.gov.br/iss/nfse.xsd"><LoteRps><NumeroLote>00035</NumeroLote><Cnpj>14793990000177</Cnpj><InscricaoMunicipal>171906308664</InscricaoMunicipal><QuantidadeRps>5</QuantidadeRps><ListaRps><Rps><InfRps><IdentificacaoRps><Numero>104</Numero><Serie>041</Serie><Tipo>1</Tipo></IdentificacaoRps><DataEmissao>2020-04-24T09:45:21</DataEmissao><NaturezaOperacao>1</NaturezaOperacao><OptanteSimplesNacional>1</OptanteSimplesNacional><IncentivadorCultural>2</IncentivadorCultural><Status>1</Status><Servico><Valores><ValorServicos>250.00</ValorServicos><ValorDeducoes>0.00</ValorDeducoes><ValorPis>0.00</ValorPis><ValorCofins>0.00</ValorCofins><ValorInss>0.00</ValorInss><ValorIr>0.00</ValorIr><ValorCsll>0.00</ValorCsll><IssRetido>2</IssRetido><ValorIss>5.00</ValorIss><OutrasRetencoes>0.00</OutrasRetencoes><BaseCalculo>250.00</BaseCalculo><Aliquota>0.0200</Aliquota><ValorLiquidoNfse>250.00</ValorLiquidoNfse><DescontoIncondicionado>0.00</DescontoIncondicionado><DescontoCondicionado>0.00</DescontoCondicionado></Valores><ItemListaServico>1719</ItemListaServico><Discriminacao>Parcela Adicional Anual conforme Contrato</Discriminacao><CodigoMunicipio>4106902</CodigoMunicipio></Servico><Prestador><Cnpj>14793990000177</Cnpj><InscricaoMunicipal>171906308664</InscricaoMunicipal></Prestador><Tomador><IdentificacaoTomador><CpfCnpj><Cnpj>17699252000153</Cnpj></CpfCnpj></IdentificacaoTomador><RazaoSocial>USICLEVER SOLUCOES E MANUFATURA</RazaoSocial><Endereco><Endereco>Rua Carlos Essenfelder</Endereco><Numero>1600</Numero><Bairro>Boqueirao</Bairro><CodigoMunicipio>4106902</CodigoMunicipio><Uf>PR</Uf><Cep>81650090</Cep></Endereco><Contato><Telefone>413248686</Telefone><Email>usiclever@gmail.com;usiclever@usiclever.com.br</Email></Contato></Tomador></InfRps><Signature xmlns="http://www.w3.org/2000/09/xmldsig#"><SignedInfo><Reference URI=""><DigestValue>rTxIVRPyMfjZcY/a+kbjNVUaIck=</DigestValue></Reference></SignedInfo><SignatureValue>RdxcxWMNSTlsyrQ/YSJt5g0yjuvIWjcXlqkV9eNjDS+pVqQzORdAuURepQAQlK0t4mEBoedKfqVn5kUGGB+C0TOSHL2Nu5yPbcMhkUlesFZWIS8ZsQWt8Hz2vtqmKiA93HfaXaigqvq6BhRgmtG4MjyI4V3xRa0JBSu1YqkdEYqRTonjFRJNZQ6BI1Fu4puAk8Kw0b6xjjYGRZL68IMrZek4BfdlcLMiRBObCVvqAZzhzHrl8aTNNmJOVS7hJPbqXDoIkMAycsrDZa9IaQwOLsiFwaXmZ1VezVKu3nQSDR/BiNCHkvYdGezL1NJLZYNqjqrWuUklunDwqVF4VHoE0Q==</SignatureValue><KeyInfo><X509Data><X509Certificate>MIIIBjCCBe6gAwIBAgIQMtESn+WI5dgdHPRo8Pa4ZjANBgkqhkiG9w0BAQsFADB4 MQswCQYDVQQGEwJCUjETMBEGA1UEChMKSUNQLUJyYXNpbDE2MDQGA1UECxMtU2Vj cmV0YXJpYSBkYSBSZWNlaXRhIEZlZGVyYWwgZG8gQnJhc2lsIC0gUkZCMRwwGgYD VQQDExNBQyBDZXJ0aXNpZ24gUkZCIEc1MB4XDTIwMDEyMzExMjMyNloXDTIxMDEy MjExMjMyNlowgfAxCzAJBgNVBAYTAkJSMRMwEQYDVQQKDApJQ1AtQnJhc2lsMQsw CQYDVQQIDAJQUjERMA8GA1UEBwwIQ3VyaXRpYmExNjA0BgNVBAsMLVNlY3JldGFy aWEgZGEgUmVjZWl0YSBGZWRlcmFsIGRvIEJyYXNpbCAtIFJGQjEWMBQGA1UECwwN UkZCIGUtQ05QSiBBMTEXMBUGA1UECwwOMjQyMTcyNDAwMDAxMDAxQzBBBgNVBAMM OlJFQUxJIENPTlNVTFRPUklBIEUgR0VTVEFPIEVNUFJFU0FSSUFMIExUREE6MTQ3 OTM5OTAwMDAxNzcwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDSQ8Bq Qn6h/M+Lnipnf0LyWHqtx00A8xh1Zs5fyXTttUze0dVDUlr8p/kgxD5dKP5LFNdf UsIhSxhRqCziElbn5S25EdY67N147ryGHrdn3PLjwTWYQOsmdTxpOGpCNkTSZ/GF 4KeHHq/+GELW36awIqQvjGhN2d7siD4v0lKU7+bBfqQd7jcPN31HbUyBYmQ8vs+u RFEvgzT46m5sOD2xrt9ItlBDlrR9sjWVCZd60i73DhmhQZHnG/SYEFnMMjFt8pjs 4jHeidLOz4E0P8+c0oN6I/y/LlPsuIiv1mDiZ3nFvlE3oSplW5w9PWWPwHIuKGwU oBJZHMh9UdGQhsgzAgMBAAGjggMRMIIDDTCBwAYDVR0RBIG4MIG1oD4GBWBMAQME oDUEMzA5MDIxOTcyNjgzMDQzMzE5MzQwMDAwMDAwMDAwMDAwMDAwMDA2ODg5ODcx NFNFU1BQUqAbBgVgTAEDAqASBBBBUkxFSSBET1MgU0FOVE9ToBkGBWBMAQMDoBAE DjE0NzkzOTkwMDAwMTc3oBcGBWBMAQMHoA4EDDAwMDAwMDAwMDAwMIEic29jaWV0 YXJpb0ByZWFsaWNvbnN1bHRvcmlhLmNvbS5icjAJBgNVHRMEAjAAMB8GA1UdIwQY MBaAFFN9f52+0WHQILran+OJpxNzWM1CMH8GA1UdIAR4MHYwdAYGYEwBAgEMMGow aAYIKwYBBQUHAgEWXGh0dHA6Ly9pY3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIv cmVwb3NpdG9yaW8vZHBjL0FDX0NlcnRpc2lnbl9SRkIvRFBDX0FDX0NlcnRpc2ln bl9SRkIucGRmMIG8BgNVHR8EgbQwgbEwV6BVoFOGUWh0dHA6Ly9pY3AtYnJhc2ls LmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vbGNyL0FDQ2VydGlzaWduUkZC RzUvTGF0ZXN0Q1JMLmNybDBWoFSgUoZQaHR0cDovL2ljcC1icmFzaWwub3V0cmFs Y3IuY29tLmJyL3JlcG9zaXRvcmlvL2xjci9BQ0NlcnRpc2lnblJGQkc1L0xhdGVz dENSTC5jcmwwDgYDVR0PAQH/BAQDAgXgMB0GA1UdJQQWMBQGCCsGAQUFBwMCBggr BgEFBQcDBDCBrAYIKwYBBQUHAQEEgZ8wgZwwXwYIKwYBBQUHMAKGU2h0dHA6Ly9p Y3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vY2VydGlmaWNh ZG9zL0FDX0NlcnRpc2lnbl9SRkJfRzUucDdjMDkGCCsGAQUFBzABhi1odHRwOi8v b2NzcC1hYy1jZXJ0aXNpZ24tcmZiLmNlcnRpc2lnbi5jb20uYnIwDQYJKoZIhvcN AQELBQADggIBAIKHTFTfKGPtFEDNJ9SEH1LgNivhav3vK5SIEeKxTXGPcnHuULUd hTZcLAmMAlnjqj1zlAFthheSbF36LF+Bl2LhG5PXvprrBZXiphXQzqso0Pv7GaEa l+Y5ugY19v7JId569AgRNfc1m4IbMgbLnXQ0OmhDuEkKzLTUrnUzztTTxOxVgulR XJhVdI0l+e85ARzyWGFYDGQ5U1R2FDE9rvsYEjmAL7LFByDh2qvWrx6aeWlgy/Ta asL0/dN04b2XNWawkzsdS/o5h/xQ8oUuIZ4LkZYcb9scQ8Ird4zFDOODzfxSYATo cRC5ERnXGhOWCJYLECLr3JR0GvanfogBAMwDpPu/UwxJ0bsASoyqt6+JU8pznk6J /Fgw1LoF1DCIP2hkpsFet1GijbveovIIXchHCKNtW/0tQc0lCUasKgiJMS/0XdlP F44BwFmI5bQ3dH4bCeMolJVgEQ2GiUfkT3PEz2uNoz//Sl1ND+Tfr6+nOtjHsidV GA9rB7m/s/7j/88lsR7FUJaIYmJIdHz82yRABvMF2XEGL+6mJD2q69NIKcbLl139 NWkow6GVkcc5khwhQoCdev6y6WLjAh83IkQPKk8Mpe86PNyyIQVtpnlig5spSvqc ILInxJXjGwBfMBo1POxy3xHx7d59DBoWP/4HxE1EfY6yYTT/Sp6K11Z4 </X509Certificate></X509Data></KeyInfo></Signature></Rps><Rps><InfRps><IdentificacaoRps><Numero>103</Numero><Serie>041</Serie><Tipo>1</Tipo></IdentificacaoRps><DataEmissao>2020-04-24T09:45:19</DataEmissao><NaturezaOperacao>1</NaturezaOperacao><OptanteSimplesNacional>1</OptanteSimplesNacional><IncentivadorCultural>2</IncentivadorCultural><Status>1</Status><Servico><Valores><ValorServicos>1530.00</ValorServicos><ValorDeducoes>0.00</ValorDeducoes><ValorPis>0.00</ValorPis><ValorCofins>0.00</ValorCofins><ValorInss>0.00</ValorInss><ValorIr>0.00</ValorIr><ValorCsll>0.00</ValorCsll><IssRetido>2</IssRetido><ValorIss>30.60</ValorIss><OutrasRetencoes>0.00</OutrasRetencoes><BaseCalculo>1530.00</BaseCalculo><Aliquota>0.0200</Aliquota><ValorLiquidoNfse>1530.00</ValorLiquidoNfse><DescontoIncondicionado>0.00</DescontoIncondicionado><DescontoCondicionado>0.00</DescontoCondicionado></Valores><ItemListaServico>1719</ItemListaServico><Discriminacao>Parcela Adicional Anual conforme Contrato.</Discriminacao><CodigoMunicipio>4106902</CodigoMunicipio></Servico><Prestador><Cnpj>14793990000177</Cnpj><InscricaoMunicipal>171906308664</InscricaoMunicipal></Prestador><Tomador><IdentificacaoTomador><CpfCnpj><Cnpj>29615024000137</Cnpj></CpfCnpj></IdentificacaoTomador><RazaoSocial>BAVARIA CURITIBA COMERCIO DE EQUIPAMENTOS E PECAS PARA VEICU</RazaoSocial><Endereco><Endereco>RUA GENERAL RAUL DA CUNHA BELLO</Endereco><Numero>105</Numero><Bairro>PINHEIRINHO</Bairro><CodigoMunicipio>4106902</CodigoMunicipio><Uf>PR</Uf><Cep>81150320</Cep></Endereco><Contato><Telefone>413156011</Telefone></Contato></Tomador></InfRps><Signature xmlns="http://www.w3.org/2000/09/xmldsig#"><SignedInfo><Reference URI=""><DigestValue>aUPcoIRh8tWVXzdK8ZBV25w2b6s=</DigestValue></Reference></SignedInfo><SignatureValue>PpWq0In2ToMuksHB1fRHhSIvtlj+oYUU22Y6Zk0WalC1nAnR3YB+u/TSJCMxHx7PpYHMBU0eOCmxNU/WAB/4G20URLnscUi2PWYx2NWgCq58bBUSFDQDFfmXGHK9SjCo/6bbIjCRQ35+R7YQnK0W9d4WJKKKeBlOb4EoUuRUcECoP7IQIz640ehgzyoNLGDTPN6zAm6OJYHXcRuwgkSX/zN58EKO/yyFU3FZa05607TTFF3/XBa6ADv0SUua+vb+WGWSTPY2Qm2Hmh17v5ZKls87sYKZWahxBbXnAP+r41VTdoo83XUd2O3vIztc2zw6QWLKfxOf5wRD+FREYjTfbg==</SignatureValue><KeyInfo><X509Data><X509Certificate>MIIIBjCCBe6gAwIBAgIQMtESn+WI5dgdHPRo8Pa4ZjANBgkqhkiG9w0BAQsFADB4 MQswCQYDVQQGEwJCUjETMBEGA1UEChMKSUNQLUJyYXNpbDE2MDQGA1UECxMtU2Vj cmV0YXJpYSBkYSBSZWNlaXRhIEZlZGVyYWwgZG8gQnJhc2lsIC0gUkZCMRwwGgYD VQQDExNBQyBDZXJ0aXNpZ24gUkZCIEc1MB4XDTIwMDEyMzExMjMyNloXDTIxMDEy MjExMjMyNlowgfAxCzAJBgNVBAYTAkJSMRMwEQYDVQQKDApJQ1AtQnJhc2lsMQsw CQYDVQQIDAJQUjERMA8GA1UEBwwIQ3VyaXRpYmExNjA0BgNVBAsMLVNlY3JldGFy aWEgZGEgUmVjZWl0YSBGZWRlcmFsIGRvIEJyYXNpbCAtIFJGQjEWMBQGA1UECwwN UkZCIGUtQ05QSiBBMTEXMBUGA1UECwwOMjQyMTcyNDAwMDAxMDAxQzBBBgNVBAMM OlJFQUxJIENPTlNVTFRPUklBIEUgR0VTVEFPIEVNUFJFU0FSSUFMIExUREE6MTQ3 OTM5OTAwMDAxNzcwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDSQ8Bq Qn6h/M+Lnipnf0LyWHqtx00A8xh1Zs5fyXTttUze0dVDUlr8p/kgxD5dKP5LFNdf UsIhSxhRqCziElbn5S25EdY67N147ryGHrdn3PLjwTWYQOsmdTxpOGpCNkTSZ/GF 4KeHHq/+GELW36awIqQvjGhN2d7siD4v0lKU7+bBfqQd7jcPN31HbUyBYmQ8vs+u RFEvgzT46m5sOD2xrt9ItlBDlrR9sjWVCZd60i73DhmhQZHnG/SYEFnMMjFt8pjs 4jHeidLOz4E0P8+c0oN6I/y/LlPsuIiv1mDiZ3nFvlE3oSplW5w9PWWPwHIuKGwU oBJZHMh9UdGQhsgzAgMBAAGjggMRMIIDDTCBwAYDVR0RBIG4MIG1oD4GBWBMAQME oDUEMzA5MDIxOTcyNjgzMDQzMzE5MzQwMDAwMDAwMDAwMDAwMDAwMDA2ODg5ODcx NFNFU1BQUqAbBgVgTAEDAqASBBBBUkxFSSBET1MgU0FOVE9ToBkGBWBMAQMDoBAE DjE0NzkzOTkwMDAwMTc3oBcGBWBMAQMHoA4EDDAwMDAwMDAwMDAwMIEic29jaWV0 YXJpb0ByZWFsaWNvbnN1bHRvcmlhLmNvbS5icjAJBgNVHRMEAjAAMB8GA1UdIwQY MBaAFFN9f52+0WHQILran+OJpxNzWM1CMH8GA1UdIAR4MHYwdAYGYEwBAgEMMGow aAYIKwYBBQUHAgEWXGh0dHA6Ly9pY3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIv cmVwb3NpdG9yaW8vZHBjL0FDX0NlcnRpc2lnbl9SRkIvRFBDX0FDX0NlcnRpc2ln bl9SRkIucGRmMIG8BgNVHR8EgbQwgbEwV6BVoFOGUWh0dHA6Ly9pY3AtYnJhc2ls LmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vbGNyL0FDQ2VydGlzaWduUkZC RzUvTGF0ZXN0Q1JMLmNybDBWoFSgUoZQaHR0cDovL2ljcC1icmFzaWwub3V0cmFs Y3IuY29tLmJyL3JlcG9zaXRvcmlvL2xjci9BQ0NlcnRpc2lnblJGQkc1L0xhdGVz dENSTC5jcmwwDgYDVR0PAQH/BAQDAgXgMB0GA1UdJQQWMBQGCCsGAQUFBwMCBggr BgEFBQcDBDCBrAYIKwYBBQUHAQEEgZ8wgZwwXwYIKwYBBQUHMAKGU2h0dHA6Ly9p Y3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vY2VydGlmaWNh ZG9zL0FDX0NlcnRpc2lnbl9SRkJfRzUucDdjMDkGCCsGAQUFBzABhi1odHRwOi8v b2NzcC1hYy1jZXJ0aXNpZ24tcmZiLmNlcnRpc2lnbi5jb20uYnIwDQYJKoZIhvcN AQELBQADggIBAIKHTFTfKGPtFEDNJ9SEH1LgNivhav3vK5SIEeKxTXGPcnHuULUd hTZcLAmMAlnjqj1zlAFthheSbF36LF+Bl2LhG5PXvprrBZXiphXQzqso0Pv7GaEa l+Y5ugY19v7JId569AgRNfc1m4IbMgbLnXQ0OmhDuEkKzLTUrnUzztTTxOxVgulR XJhVdI0l+e85ARzyWGFYDGQ5U1R2FDE9rvsYEjmAL7LFByDh2qvWrx6aeWlgy/Ta asL0/dN04b2XNWawkzsdS/o5h/xQ8oUuIZ4LkZYcb9scQ8Ird4zFDOODzfxSYATo cRC5ERnXGhOWCJYLECLr3JR0GvanfogBAMwDpPu/UwxJ0bsASoyqt6+JU8pznk6J /Fgw1LoF1DCIP2hkpsFet1GijbveovIIXchHCKNtW/0tQc0lCUasKgiJMS/0XdlP F44BwFmI5bQ3dH4bCeMolJVgEQ2GiUfkT3PEz2uNoz//Sl1ND+Tfr6+nOtjHsidV GA9rB7m/s/7j/88lsR7FUJaIYmJIdHz82yRABvMF2XEGL+6mJD2q69NIKcbLl139 NWkow6GVkcc5khwhQoCdev6y6WLjAh83IkQPKk8Mpe86PNyyIQVtpnlig5spSvqc ILInxJXjGwBfMBo1POxy3xHx7d59DBoWP/4HxE1EfY6yYTT/Sp6K11Z4 </X509Certificate></X509Data></KeyInfo></Signature></Rps><Rps><InfRps><IdentificacaoRps><Numero>102</Numero><Serie>041</Serie><Tipo>1</Tipo></IdentificacaoRps><DataEmissao>2020-04-24T09:45:17</DataEmissao><NaturezaOperacao>1</NaturezaOperacao><OptanteSimplesNacional>1</OptanteSimplesNacional><IncentivadorCultural>2</IncentivadorCultural><Status>1</Status><Servico><Valores><ValorServicos>125.00</ValorServicos><ValorDeducoes>0.00</ValorDeducoes><ValorPis>0.00</ValorPis><ValorCofins>0.00</ValorCofins><ValorInss>0.00</ValorInss><ValorIr>0.00</ValorIr><ValorCsll>0.00</ValorCsll><IssRetido>2</IssRetido><ValorIss>2.50</ValorIss><OutrasRetencoes>0.00</OutrasRetencoes><BaseCalculo>125.00</BaseCalculo><Aliquota>0.0200</Aliquota><ValorLiquidoNfse>125.00</ValorLiquidoNfse><DescontoIncondicionado>0.00</DescontoIncondicionado><DescontoCondicionado>0.00</DescontoCondicionado></Valores><ItemListaServico>1719</ItemListaServico><Discriminacao>Parcela Adicional Anual conforme Contrato.</Discriminacao><CodigoMunicipio>4106902</CodigoMunicipio></Servico><Prestador><Cnpj>14793990000177</Cnpj><InscricaoMunicipal>171906308664</InscricaoMunicipal></Prestador><Tomador><IdentificacaoTomador><CpfCnpj><Cnpj>23554342000159</Cnpj></CpfCnpj></IdentificacaoTomador><RazaoSocial>QCK BRASIL FOODS LTDA EPP</RazaoSocial><Endereco><Endereco>RUA 3250</Endereco><Numero>10</Numero><Complemento>SALA 03</Complemento><Bairro>CENTRO</Bairro><CodigoMunicipio>4202008</CodigoMunicipio><Uf>SC</Uf><Cep>88330278</Cep></Endereco><Contato><Telefone>4130797667</Telefone><Email>gabriel@quickies.com.br; financeiro@quickies.com.br; diogo@quickies.com.br</Email></Contato></Tomador></InfRps><Signature xmlns="http://www.w3.org/2000/09/xmldsig#"><SignedInfo><Reference URI=""><DigestValue>s+bDxC7O8ojONheLetLzu3Q/VS8=</DigestValue></Reference></SignedInfo><SignatureValue>pY/m5ECKpTMVV1TWHWXNrNzV19tg/EFTX6AoAT4905Vskg6fgBBzkSbl2rfOHB7NrcM7FpVBUHLBRHWg8RXXWl4EvS+nXX4EI4W0SJzNxe9l00ZnKRst4t0uohrLwdoJtLjUOBpVaFUDaRQRxJDz/lCdEzAFLDjX4kcSVYu6yNGJjAiNDKz6GoDOGJTlWBlJ6P4SUzjQNjOCrGCBj2g4AVf7aBFJI113/lwFpgv+WB05MMM5fm3Fry4SJPkdMDjW3XPNnbClivp1iqHLgsw3DJUZ9bDZIrtp0kGpki1BtbCB99CB5a4N2MZUfxaYkT994dJQF7Ngvq6m7j2uxPyR/A==</SignatureValue><KeyInfo><X509Data><X509Certificate>MIIIBjCCBe6gAwIBAgIQMtESn+WI5dgdHPRo8Pa4ZjANBgkqhkiG9w0BAQsFADB4 MQswCQYDVQQGEwJCUjETMBEGA1UEChMKSUNQLUJyYXNpbDE2MDQGA1UECxMtU2Vj cmV0YXJpYSBkYSBSZWNlaXRhIEZlZGVyYWwgZG8gQnJhc2lsIC0gUkZCMRwwGgYD VQQDExNBQyBDZXJ0aXNpZ24gUkZCIEc1MB4XDTIwMDEyMzExMjMyNloXDTIxMDEy MjExMjMyNlowgfAxCzAJBgNVBAYTAkJSMRMwEQYDVQQKDApJQ1AtQnJhc2lsMQsw CQYDVQQIDAJQUjERMA8GA1UEBwwIQ3VyaXRpYmExNjA0BgNVBAsMLVNlY3JldGFy aWEgZGEgUmVjZWl0YSBGZWRlcmFsIGRvIEJyYXNpbCAtIFJGQjEWMBQGA1UECwwN UkZCIGUtQ05QSiBBMTEXMBUGA1UECwwOMjQyMTcyNDAwMDAxMDAxQzBBBgNVBAMM OlJFQUxJIENPTlNVTFRPUklBIEUgR0VTVEFPIEVNUFJFU0FSSUFMIExUREE6MTQ3 OTM5OTAwMDAxNzcwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDSQ8Bq Qn6h/M+Lnipnf0LyWHqtx00A8xh1Zs5fyXTttUze0dVDUlr8p/kgxD5dKP5LFNdf UsIhSxhRqCziElbn5S25EdY67N147ryGHrdn3PLjwTWYQOsmdTxpOGpCNkTSZ/GF 4KeHHq/+GELW36awIqQvjGhN2d7siD4v0lKU7+bBfqQd7jcPN31HbUyBYmQ8vs+u RFEvgzT46m5sOD2xrt9ItlBDlrR9sjWVCZd60i73DhmhQZHnG/SYEFnMMjFt8pjs 4jHeidLOz4E0P8+c0oN6I/y/LlPsuIiv1mDiZ3nFvlE3oSplW5w9PWWPwHIuKGwU oBJZHMh9UdGQhsgzAgMBAAGjggMRMIIDDTCBwAYDVR0RBIG4MIG1oD4GBWBMAQME oDUEMzA5MDIxOTcyNjgzMDQzMzE5MzQwMDAwMDAwMDAwMDAwMDAwMDA2ODg5ODcx NFNFU1BQUqAbBgVgTAEDAqASBBBBUkxFSSBET1MgU0FOVE9ToBkGBWBMAQMDoBAE DjE0NzkzOTkwMDAwMTc3oBcGBWBMAQMHoA4EDDAwMDAwMDAwMDAwMIEic29jaWV0 YXJpb0ByZWFsaWNvbnN1bHRvcmlhLmNvbS5icjAJBgNVHRMEAjAAMB8GA1UdIwQY MBaAFFN9f52+0WHQILran+OJpxNzWM1CMH8GA1UdIAR4MHYwdAYGYEwBAgEMMGow aAYIKwYBBQUHAgEWXGh0dHA6Ly9pY3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIv cmVwb3NpdG9yaW8vZHBjL0FDX0NlcnRpc2lnbl9SRkIvRFBDX0FDX0NlcnRpc2ln bl9SRkIucGRmMIG8BgNVHR8EgbQwgbEwV6BVoFOGUWh0dHA6Ly9pY3AtYnJhc2ls LmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vbGNyL0FDQ2VydGlzaWduUkZC RzUvTGF0ZXN0Q1JMLmNybDBWoFSgUoZQaHR0cDovL2ljcC1icmFzaWwub3V0cmFs Y3IuY29tLmJyL3JlcG9zaXRvcmlvL2xjci9BQ0NlcnRpc2lnblJGQkc1L0xhdGVz dENSTC5jcmwwDgYDVR0PAQH/BAQDAgXgMB0GA1UdJQQWMBQGCCsGAQUFBwMCBggr BgEFBQcDBDCBrAYIKwYBBQUHAQEEgZ8wgZwwXwYIKwYBBQUHMAKGU2h0dHA6Ly9p Y3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vY2VydGlmaWNh ZG9zL0FDX0NlcnRpc2lnbl9SRkJfRzUucDdjMDkGCCsGAQUFBzABhi1odHRwOi8v b2NzcC1hYy1jZXJ0aXNpZ24tcmZiLmNlcnRpc2lnbi5jb20uYnIwDQYJKoZIhvcN AQELBQADggIBAIKHTFTfKGPtFEDNJ9SEH1LgNivhav3vK5SIEeKxTXGPcnHuULUd hTZcLAmMAlnjqj1zlAFthheSbF36LF+Bl2LhG5PXvprrBZXiphXQzqso0Pv7GaEa l+Y5ugY19v7JId569AgRNfc1m4IbMgbLnXQ0OmhDuEkKzLTUrnUzztTTxOxVgulR XJhVdI0l+e85ARzyWGFYDGQ5U1R2FDE9rvsYEjmAL7LFByDh2qvWrx6aeWlgy/Ta asL0/dN04b2XNWawkzsdS/o5h/xQ8oUuIZ4LkZYcb9scQ8Ird4zFDOODzfxSYATo cRC5ERnXGhOWCJYLECLr3JR0GvanfogBAMwDpPu/UwxJ0bsASoyqt6+JU8pznk6J /Fgw1LoF1DCIP2hkpsFet1GijbveovIIXchHCKNtW/0tQc0lCUasKgiJMS/0XdlP F44BwFmI5bQ3dH4bCeMolJVgEQ2GiUfkT3PEz2uNoz//Sl1ND+Tfr6+nOtjHsidV GA9rB7m/s/7j/88lsR7FUJaIYmJIdHz82yRABvMF2XEGL+6mJD2q69NIKcbLl139 NWkow6GVkcc5khwhQoCdev6y6WLjAh83IkQPKk8Mpe86PNyyIQVtpnlig5spSvqc ILInxJXjGwBfMBo1POxy3xHx7d59DBoWP/4HxE1EfY6yYTT/Sp6K11Z4 </X509Certificate></X509Data></KeyInfo></Signature></Rps><Rps><InfRps><IdentificacaoRps><Numero>101</Numero><Serie>041</Serie><Tipo>1</Tipo></IdentificacaoRps><DataEmissao>2020-04-24T09:43:28</DataEmissao><NaturezaOperacao>1</NaturezaOperacao><OptanteSimplesNacional>1</OptanteSimplesNacional><IncentivadorCultural>2</IncentivadorCultural><Status>1</Status><Servico><Valores><ValorServicos>275.00</ValorServicos><ValorDeducoes>0.00</ValorDeducoes><ValorPis>0.00</ValorPis><ValorCofins>0.00</ValorCofins><ValorInss>0.00</ValorInss><ValorIr>0.00</ValorIr><ValorCsll>0.00</ValorCsll><IssRetido>2</IssRetido><ValorIss>5.50</ValorIss><OutrasRetencoes>0.00</OutrasRetencoes><BaseCalculo>275.00</BaseCalculo><Aliquota>0.0200</Aliquota><ValorLiquidoNfse>275.00</ValorLiquidoNfse><DescontoIncondicionado>0.00</DescontoIncondicionado><DescontoCondicionado>0.00</DescontoCondicionado></Valores><ItemListaServico>1719</ItemListaServico><Discriminacao>Parcela Adicional Anual conforme Contrato.</Discriminacao><CodigoMunicipio>4106902</CodigoMunicipio></Servico><Prestador><Cnpj>14793990000177</Cnpj><InscricaoMunicipal>171906308664</InscricaoMunicipal></Prestador><Tomador><IdentificacaoTomador><CpfCnpj><Cnpj>11294517000157</Cnpj></CpfCnpj></IdentificacaoTomador><RazaoSocial>PERFEITA MOBILIA INDUSTRIA E COMERCIO DE MOVEIS LTDA - ME</RazaoSocial><Endereco><Endereco>RUA JOSE RODRIGUES PINHEIRO</Endereco><Numero>1705</Numero><Bairro>CAPAO RASO</Bairro><CodigoMunicipio>4106902</CodigoMunicipio><Uf>PR</Uf><Cep>81130200</Cep></Endereco><Contato><Telefone>413248378</Telefone><Email>administrativo@perfettoforhome.com.br</Email></Contato></Tomador></InfRps><Signature xmlns="http://www.w3.org/2000/09/xmldsig#"><SignedInfo><Reference URI=""><DigestValue>NvAAj1CAirjMdB5jdgMFozMc4io=</DigestValue></Reference></SignedInfo><SignatureValue>NAXLWvwn4z1iWV74vVjr8RBSlPCbzeSSEp3dYOXGpNF5iFoWovWR80osd+i8+Mq3qmCQfjr9fCWrr41oc0p6eVwn+jNOfNeVjnVVR24G84qwcz4f8GfnZnCVEAxYieMNxmTgMa70WI2o+s6MtZyHk467mGp6beG/3/nOfAbB3GHgQqyEQy9yMdmzTd9ANnj/8hUEe6Q4GogF7ssucTyDT2+c2FyUIoWByDn9zBQhIW95HJFbDMtOCgkavXHHLwCnqDt2SjAlJxFhY4jgZc7Kd9CYGlS/6mosIMErm7OvB5/gsGGAlMOU1ifa2Zk1zPiQJXGg7DA6LcMyfKtdFmjVyw==</SignatureValue><KeyInfo><X509Data><X509Certificate>MIIIBjCCBe6gAwIBAgIQMtESn+WI5dgdHPRo8Pa4ZjANBgkqhkiG9w0BAQsFADB4 MQswCQYDVQQGEwJCUjETMBEGA1UEChMKSUNQLUJyYXNpbDE2MDQGA1UECxMtU2Vj cmV0YXJpYSBkYSBSZWNlaXRhIEZlZGVyYWwgZG8gQnJhc2lsIC0gUkZCMRwwGgYD VQQDExNBQyBDZXJ0aXNpZ24gUkZCIEc1MB4XDTIwMDEyMzExMjMyNloXDTIxMDEy MjExMjMyNlowgfAxCzAJBgNVBAYTAkJSMRMwEQYDVQQKDApJQ1AtQnJhc2lsMQsw CQYDVQQIDAJQUjERMA8GA1UEBwwIQ3VyaXRpYmExNjA0BgNVBAsMLVNlY3JldGFy aWEgZGEgUmVjZWl0YSBGZWRlcmFsIGRvIEJyYXNpbCAtIFJGQjEWMBQGA1UECwwN UkZCIGUtQ05QSiBBMTEXMBUGA1UECwwOMjQyMTcyNDAwMDAxMDAxQzBBBgNVBAMM OlJFQUxJIENPTlNVTFRPUklBIEUgR0VTVEFPIEVNUFJFU0FSSUFMIExUREE6MTQ3 OTM5OTAwMDAxNzcwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDSQ8Bq Qn6h/M+Lnipnf0LyWHqtx00A8xh1Zs5fyXTttUze0dVDUlr8p/kgxD5dKP5LFNdf UsIhSxhRqCziElbn5S25EdY67N147ryGHrdn3PLjwTWYQOsmdTxpOGpCNkTSZ/GF 4KeHHq/+GELW36awIqQvjGhN2d7siD4v0lKU7+bBfqQd7jcPN31HbUyBYmQ8vs+u RFEvgzT46m5sOD2xrt9ItlBDlrR9sjWVCZd60i73DhmhQZHnG/SYEFnMMjFt8pjs 4jHeidLOz4E0P8+c0oN6I/y/LlPsuIiv1mDiZ3nFvlE3oSplW5w9PWWPwHIuKGwU oBJZHMh9UdGQhsgzAgMBAAGjggMRMIIDDTCBwAYDVR0RBIG4MIG1oD4GBWBMAQME oDUEMzA5MDIxOTcyNjgzMDQzMzE5MzQwMDAwMDAwMDAwMDAwMDAwMDA2ODg5ODcx NFNFU1BQUqAbBgVgTAEDAqASBBBBUkxFSSBET1MgU0FOVE9ToBkGBWBMAQMDoBAE DjE0NzkzOTkwMDAwMTc3oBcGBWBMAQMHoA4EDDAwMDAwMDAwMDAwMIEic29jaWV0 YXJpb0ByZWFsaWNvbnN1bHRvcmlhLmNvbS5icjAJBgNVHRMEAjAAMB8GA1UdIwQY MBaAFFN9f52+0WHQILran+OJpxNzWM1CMH8GA1UdIAR4MHYwdAYGYEwBAgEMMGow aAYIKwYBBQUHAgEWXGh0dHA6Ly9pY3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIv cmVwb3NpdG9yaW8vZHBjL0FDX0NlcnRpc2lnbl9SRkIvRFBDX0FDX0NlcnRpc2ln bl9SRkIucGRmMIG8BgNVHR8EgbQwgbEwV6BVoFOGUWh0dHA6Ly9pY3AtYnJhc2ls LmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vbGNyL0FDQ2VydGlzaWduUkZC RzUvTGF0ZXN0Q1JMLmNybDBWoFSgUoZQaHR0cDovL2ljcC1icmFzaWwub3V0cmFs Y3IuY29tLmJyL3JlcG9zaXRvcmlvL2xjci9BQ0NlcnRpc2lnblJGQkc1L0xhdGVz dENSTC5jcmwwDgYDVR0PAQH/BAQDAgXgMB0GA1UdJQQWMBQGCCsGAQUFBwMCBggr BgEFBQcDBDCBrAYIKwYBBQUHAQEEgZ8wgZwwXwYIKwYBBQUHMAKGU2h0dHA6Ly9p Y3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vY2VydGlmaWNh ZG9zL0FDX0NlcnRpc2lnbl9SRkJfRzUucDdjMDkGCCsGAQUFBzABhi1odHRwOi8v b2NzcC1hYy1jZXJ0aXNpZ24tcmZiLmNlcnRpc2lnbi5jb20uYnIwDQYJKoZIhvcN AQELBQADggIBAIKHTFTfKGPtFEDNJ9SEH1LgNivhav3vK5SIEeKxTXGPcnHuULUd hTZcLAmMAlnjqj1zlAFthheSbF36LF+Bl2LhG5PXvprrBZXiphXQzqso0Pv7GaEa l+Y5ugY19v7JId569AgRNfc1m4IbMgbLnXQ0OmhDuEkKzLTUrnUzztTTxOxVgulR XJhVdI0l+e85ARzyWGFYDGQ5U1R2FDE9rvsYEjmAL7LFByDh2qvWrx6aeWlgy/Ta asL0/dN04b2XNWawkzsdS/o5h/xQ8oUuIZ4LkZYcb9scQ8Ird4zFDOODzfxSYATo cRC5ERnXGhOWCJYLECLr3JR0GvanfogBAMwDpPu/UwxJ0bsASoyqt6+JU8pznk6J /Fgw1LoF1DCIP2hkpsFet1GijbveovIIXchHCKNtW/0tQc0lCUasKgiJMS/0XdlP F44BwFmI5bQ3dH4bCeMolJVgEQ2GiUfkT3PEz2uNoz//Sl1ND+Tfr6+nOtjHsidV GA9rB7m/s/7j/88lsR7FUJaIYmJIdHz82yRABvMF2XEGL+6mJD2q69NIKcbLl139 NWkow6GVkcc5khwhQoCdev6y6WLjAh83IkQPKk8Mpe86PNyyIQVtpnlig5spSvqc ILInxJXjGwBfMBo1POxy3xHx7d59DBoWP/4HxE1EfY6yYTT/Sp6K11Z4 </X509Certificate></X509Data></KeyInfo></Signature></Rps><Rps><InfRps><IdentificacaoRps><Numero>100</Numero><Serie>041</Serie><Tipo>1</Tipo></IdentificacaoRps><DataEmissao>2020-04-24T09:43:25</DataEmissao><NaturezaOperacao>1</NaturezaOperacao><OptanteSimplesNacional>1</OptanteSimplesNacional><IncentivadorCultural>2</IncentivadorCultural><Status>1</Status><Servico><Valores><ValorServicos>483.23</ValorServicos><ValorDeducoes>0.00</ValorDeducoes><ValorPis>0.00</ValorPis><ValorCofins>0.00</ValorCofins><ValorInss>0.00</ValorInss><ValorIr>0.00</ValorIr><ValorCsll>0.00</ValorCsll><IssRetido>2</IssRetido><ValorIss>9.66</ValorIss><OutrasRetencoes>0.00</OutrasRetencoes><BaseCalculo>483.23</BaseCalculo><Aliquota>0.0200</Aliquota><ValorLiquidoNfse>483.23</ValorLiquidoNfse><DescontoIncondicionado>0.00</DescontoIncondicionado><DescontoCondicionado>0.00</DescontoCondicionado></Valores><ItemListaServico>1719</ItemListaServico><Discriminacao>[010] Servicos Mensais de Assessoria Contabil/Fiscal Conforme Contrato</Discriminacao><CodigoMunicipio>4106902</CodigoMunicipio></Servico><Prestador><Cnpj>14793990000177</Cnpj><InscricaoMunicipal>171906308664</InscricaoMunicipal></Prestador><Tomador><IdentificacaoTomador><CpfCnpj><Cnpj>17447219000136</Cnpj></CpfCnpj></IdentificacaoTomador><RazaoSocial>CLINICA MEDICA CEIDIM EIRELI ME</RazaoSocial><Endereco><Endereco>Rod PR 412 (Engenheiro Darci Gomes de Moraes)</Endereco><Numero>421</Numero><Bairro>Balneario Prais de Leste</Bairro><CodigoMunicipio>4119954</CodigoMunicipio><Uf>PR</Uf><Cep>83255000</Cep></Endereco><Contato><Telefone>413458690</Telefone><Email>daniele@ceidim.com.br</Email></Contato></Tomador></InfRps><Signature xmlns="http://www.w3.org/2000/09/xmldsig#"><SignedInfo><Reference URI=""><DigestValue>8Aki7OmCVhF8ARVKVBVhp8lPWZc=</DigestValue></Reference></SignedInfo><SignatureValue>tlOUU/DrQfM0dhuM/tlu4UXXJTWLBL1l+3mDzCPLkMMWxNZQx0Gb8nc2mzmBibNpSZxo15e3o/dGukuRlzJeEsvo3e6R/jhQd3hmvI7J0ccNuGJe4LVJv8MjSiHXKcr7lvy+2uXGWmrYAX5RJTQgg4GY95nVLxqlIgFc5tgVvkCFgP3bAe5nPybFupX6JbnseUAD1PfW9oVTKHx8nejT0e1XgM8rdtfua3Lju9AWR4LnGkokZ6O85MaadNVsJqRQLWaDQOt0r69/QF9GPJogDX02k1pl7YRhEaocTxmIprzriRjt4IFgLeD+OF28QmpddTCWf2pssW9k/ow5Hb6UNw==</SignatureValue><KeyInfo><X509Data><X509Certificate>MIIIBjCCBe6gAwIBAgIQMtESn+WI5dgdHPRo8Pa4ZjANBgkqhkiG9w0BAQsFADB4 MQswCQYDVQQGEwJCUjETMBEGA1UEChMKSUNQLUJyYXNpbDE2MDQGA1UECxMtU2Vj cmV0YXJpYSBkYSBSZWNlaXRhIEZlZGVyYWwgZG8gQnJhc2lsIC0gUkZCMRwwGgYD VQQDExNBQyBDZXJ0aXNpZ24gUkZCIEc1MB4XDTIwMDEyMzExMjMyNloXDTIxMDEy MjExMjMyNlowgfAxCzAJBgNVBAYTAkJSMRMwEQYDVQQKDApJQ1AtQnJhc2lsMQsw CQYDVQQIDAJQUjERMA8GA1UEBwwIQ3VyaXRpYmExNjA0BgNVBAsMLVNlY3JldGFy aWEgZGEgUmVjZWl0YSBGZWRlcmFsIGRvIEJyYXNpbCAtIFJGQjEWMBQGA1UECwwN UkZCIGUtQ05QSiBBMTEXMBUGA1UECwwOMjQyMTcyNDAwMDAxMDAxQzBBBgNVBAMM OlJFQUxJIENPTlNVTFRPUklBIEUgR0VTVEFPIEVNUFJFU0FSSUFMIExUREE6MTQ3 OTM5OTAwMDAxNzcwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDSQ8Bq Qn6h/M+Lnipnf0LyWHqtx00A8xh1Zs5fyXTttUze0dVDUlr8p/kgxD5dKP5LFNdf UsIhSxhRqCziElbn5S25EdY67N147ryGHrdn3PLjwTWYQOsmdTxpOGpCNkTSZ/GF 4KeHHq/+GELW36awIqQvjGhN2d7siD4v0lKU7+bBfqQd7jcPN31HbUyBYmQ8vs+u RFEvgzT46m5sOD2xrt9ItlBDlrR9sjWVCZd60i73DhmhQZHnG/SYEFnMMjFt8pjs 4jHeidLOz4E0P8+c0oN6I/y/LlPsuIiv1mDiZ3nFvlE3oSplW5w9PWWPwHIuKGwU oBJZHMh9UdGQhsgzAgMBAAGjggMRMIIDDTCBwAYDVR0RBIG4MIG1oD4GBWBMAQME oDUEMzA5MDIxOTcyNjgzMDQzMzE5MzQwMDAwMDAwMDAwMDAwMDAwMDA2ODg5ODcx NFNFU1BQUqAbBgVgTAEDAqASBBBBUkxFSSBET1MgU0FOVE9ToBkGBWBMAQMDoBAE DjE0NzkzOTkwMDAwMTc3oBcGBWBMAQMHoA4EDDAwMDAwMDAwMDAwMIEic29jaWV0 YXJpb0ByZWFsaWNvbnN1bHRvcmlhLmNvbS5icjAJBgNVHRMEAjAAMB8GA1UdIwQY MBaAFFN9f52+0WHQILran+OJpxNzWM1CMH8GA1UdIAR4MHYwdAYGYEwBAgEMMGow aAYIKwYBBQUHAgEWXGh0dHA6Ly9pY3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIv cmVwb3NpdG9yaW8vZHBjL0FDX0NlcnRpc2lnbl9SRkIvRFBDX0FDX0NlcnRpc2ln bl9SRkIucGRmMIG8BgNVHR8EgbQwgbEwV6BVoFOGUWh0dHA6Ly9pY3AtYnJhc2ls LmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vbGNyL0FDQ2VydGlzaWduUkZC RzUvTGF0ZXN0Q1JMLmNybDBWoFSgUoZQaHR0cDovL2ljcC1icmFzaWwub3V0cmFs Y3IuY29tLmJyL3JlcG9zaXRvcmlvL2xjci9BQ0NlcnRpc2lnblJGQkc1L0xhdGVz dENSTC5jcmwwDgYDVR0PAQH/BAQDAgXgMB0GA1UdJQQWMBQGCCsGAQUFBwMCBggr BgEFBQcDBDCBrAYIKwYBBQUHAQEEgZ8wgZwwXwYIKwYBBQUHMAKGU2h0dHA6Ly9p Y3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vY2VydGlmaWNh ZG9zL0FDX0NlcnRpc2lnbl9SRkJfRzUucDdjMDkGCCsGAQUFBzABhi1odHRwOi8v b2NzcC1hYy1jZXJ0aXNpZ24tcmZiLmNlcnRpc2lnbi5jb20uYnIwDQYJKoZIhvcN AQELBQADggIBAIKHTFTfKGPtFEDNJ9SEH1LgNivhav3vK5SIEeKxTXGPcnHuULUd hTZcLAmMAlnjqj1zlAFthheSbF36LF+Bl2LhG5PXvprrBZXiphXQzqso0Pv7GaEa l+Y5ugY19v7JId569AgRNfc1m4IbMgbLnXQ0OmhDuEkKzLTUrnUzztTTxOxVgulR XJhVdI0l+e85ARzyWGFYDGQ5U1R2FDE9rvsYEjmAL7LFByDh2qvWrx6aeWlgy/Ta asL0/dN04b2XNWawkzsdS/o5h/xQ8oUuIZ4LkZYcb9scQ8Ird4zFDOODzfxSYATo cRC5ERnXGhOWCJYLECLr3JR0GvanfogBAMwDpPu/UwxJ0bsASoyqt6+JU8pznk6J /Fgw1LoF1DCIP2hkpsFet1GijbveovIIXchHCKNtW/0tQc0lCUasKgiJMS/0XdlP F44BwFmI5bQ3dH4bCeMolJVgEQ2GiUfkT3PEz2uNoz//Sl1ND+Tfr6+nOtjHsidV GA9rB7m/s/7j/88lsR7FUJaIYmJIdHz82yRABvMF2XEGL+6mJD2q69NIKcbLl139 NWkow6GVkcc5khwhQoCdev6y6WLjAh83IkQPKk8Mpe86PNyyIQVtpnlig5spSvqc ILInxJXjGwBfMBo1POxy3xHx7d59DBoWP/4HxE1EfY6yYTT/Sp6K11Z4 </X509Certificate></X509Data></KeyInfo></Signature></Rps></ListaRps></LoteRps><Signature xmlns="http://www.w3.org/2000/09/xmldsig#"><SignedInfo><CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/><SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/><Reference URI=""><Transforms><Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/><Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/></Transforms><DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/><DigestValue>S+6UjpVnBmRm//sDelnLLOqvVxM=</DigestValue></Reference></SignedInfo><SignatureValue>docj6CTNwDCMfGQSOFwNRhcnLI+/qCKJBUHZhL1fxLk5C0Wn+BDTUmOZJX/OpG2VnS8lsp8H2ae6kxAtGv+1MIXH6YSWgfOCb+2m+d2xIpeI0NaXtechAghQCg5E0zfNiBRVRpjxNVajHmNpSZnxCai+qGvRhfNYUQDgvWzmLWqDpjfVy5z4OpFoPD552NGKz58/WxS2suVf0eP1dpyn5WptrpfkuYciVGGVZs0jFGjTNxd8PaPlxplaSqzI9ZomHNVwPs7UnNZKOWgGhvUDfLVIBBHH+uvLEwwB4E/4Zn9s9pA78q/TTJfZhcGKwNqkZHg7Xv9iRXPolGBY2PjCJQ==</SignatureValue><KeyInfo><X509Data><X509Certificate>MIIIBjCCBe6gAwIBAgIQMtESn+WI5dgdHPRo8Pa4ZjANBgkqhkiG9w0BAQsFADB4
MQswCQYDVQQGEwJCUjETMBEGA1UEChMKSUNQLUJyYXNpbDE2MDQGA1UECxMtU2Vj
cmV0YXJpYSBkYSBSZWNlaXRhIEZlZGVyYWwgZG8gQnJhc2lsIC0gUkZCMRwwGgYD
VQQDExNBQyBDZXJ0aXNpZ24gUkZCIEc1MB4XDTIwMDEyMzExMjMyNloXDTIxMDEy
MjExMjMyNlowgfAxCzAJBgNVBAYTAkJSMRMwEQYDVQQKDApJQ1AtQnJhc2lsMQsw
CQYDVQQIDAJQUjERMA8GA1UEBwwIQ3VyaXRpYmExNjA0BgNVBAsMLVNlY3JldGFy
aWEgZGEgUmVjZWl0YSBGZWRlcmFsIGRvIEJyYXNpbCAtIFJGQjEWMBQGA1UECwwN
UkZCIGUtQ05QSiBBMTEXMBUGA1UECwwOMjQyMTcyNDAwMDAxMDAxQzBBBgNVBAMM
OlJFQUxJIENPTlNVTFRPUklBIEUgR0VTVEFPIEVNUFJFU0FSSUFMIExUREE6MTQ3
OTM5OTAwMDAxNzcwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDSQ8Bq
Qn6h/M+Lnipnf0LyWHqtx00A8xh1Zs5fyXTttUze0dVDUlr8p/kgxD5dKP5LFNdf
UsIhSxhRqCziElbn5S25EdY67N147ryGHrdn3PLjwTWYQOsmdTxpOGpCNkTSZ/GF
4KeHHq/+GELW36awIqQvjGhN2d7siD4v0lKU7+bBfqQd7jcPN31HbUyBYmQ8vs+u
RFEvgzT46m5sOD2xrt9ItlBDlrR9sjWVCZd60i73DhmhQZHnG/SYEFnMMjFt8pjs
4jHeidLOz4E0P8+c0oN6I/y/LlPsuIiv1mDiZ3nFvlE3oSplW5w9PWWPwHIuKGwU
oBJZHMh9UdGQhsgzAgMBAAGjggMRMIIDDTCBwAYDVR0RBIG4MIG1oD4GBWBMAQME
oDUEMzA5MDIxOTcyNjgzMDQzMzE5MzQwMDAwMDAwMDAwMDAwMDAwMDA2ODg5ODcx
NFNFU1BQUqAbBgVgTAEDAqASBBBBUkxFSSBET1MgU0FOVE9ToBkGBWBMAQMDoBAE
DjE0NzkzOTkwMDAwMTc3oBcGBWBMAQMHoA4EDDAwMDAwMDAwMDAwMIEic29jaWV0
YXJpb0ByZWFsaWNvbnN1bHRvcmlhLmNvbS5icjAJBgNVHRMEAjAAMB8GA1UdIwQY
MBaAFFN9f52+0WHQILran+OJpxNzWM1CMH8GA1UdIAR4MHYwdAYGYEwBAgEMMGow
aAYIKwYBBQUHAgEWXGh0dHA6Ly9pY3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIv
cmVwb3NpdG9yaW8vZHBjL0FDX0NlcnRpc2lnbl9SRkIvRFBDX0FDX0NlcnRpc2ln
bl9SRkIucGRmMIG8BgNVHR8EgbQwgbEwV6BVoFOGUWh0dHA6Ly9pY3AtYnJhc2ls
LmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vbGNyL0FDQ2VydGlzaWduUkZC
RzUvTGF0ZXN0Q1JMLmNybDBWoFSgUoZQaHR0cDovL2ljcC1icmFzaWwub3V0cmFs
Y3IuY29tLmJyL3JlcG9zaXRvcmlvL2xjci9BQ0NlcnRpc2lnblJGQkc1L0xhdGVz
dENSTC5jcmwwDgYDVR0PAQH/BAQDAgXgMB0GA1UdJQQWMBQGCCsGAQUFBwMCBggr
BgEFBQcDBDCBrAYIKwYBBQUHAQEEgZ8wgZwwXwYIKwYBBQUHMAKGU2h0dHA6Ly9p
Y3AtYnJhc2lsLmNlcnRpc2lnbi5jb20uYnIvcmVwb3NpdG9yaW8vY2VydGlmaWNh
ZG9zL0FDX0NlcnRpc2lnbl9SRkJfRzUucDdjMDkGCCsGAQUFBzABhi1odHRwOi8v
b2NzcC1hYy1jZXJ0aXNpZ24tcmZiLmNlcnRpc2lnbi5jb20uYnIwDQYJKoZIhvcN
AQELBQADggIBAIKHTFTfKGPtFEDNJ9SEH1LgNivhav3vK5SIEeKxTXGPcnHuULUd
hTZcLAmMAlnjqj1zlAFthheSbF36LF+Bl2LhG5PXvprrBZXiphXQzqso0Pv7GaEa
l+Y5ugY19v7JId569AgRNfc1m4IbMgbLnXQ0OmhDuEkKzLTUrnUzztTTxOxVgulR
XJhVdI0l+e85ARzyWGFYDGQ5U1R2FDE9rvsYEjmAL7LFByDh2qvWrx6aeWlgy/Ta
asL0/dN04b2XNWawkzsdS/o5h/xQ8oUuIZ4LkZYcb9scQ8Ird4zFDOODzfxSYATo
cRC5ERnXGhOWCJYLECLr3JR0GvanfogBAMwDpPu/UwxJ0bsASoyqt6+JU8pznk6J
/Fgw1LoF1DCIP2hkpsFet1GijbveovIIXchHCKNtW/0tQc0lCUasKgiJMS/0XdlP
F44BwFmI5bQ3dH4bCeMolJVgEQ2GiUfkT3PEz2uNoz//Sl1ND+Tfr6+nOtjHsidV
GA9rB7m/s/7j/88lsR7FUJaIYmJIdHz82yRABvMF2XEGL+6mJD2q69NIKcbLl139
NWkow6GVkcc5khwhQoCdev6y6WLjAh83IkQPKk8Mpe86PNyyIQVtpnlig5spSvqc
ILInxJXjGwBfMBo1POxy3xHx7d59DBoWP/4HxE1EfY6yYTT/Sp6K11Z4
</X509Certificate></X509Data></KeyInfo></Signature></EnviarLoteRpsEnvio></RecepcionarLoteRps>"""
        return xmlString


    def test_valid_lote(self):
        pfx_source = open(os.path.join(self.caminho+'/cert', 'teste.pfx'),'rb').read()
        #pfx_password = os.path.join(self.caminho+'/cert', 'key.txt')
        certificado = Certificado(pfx_source, '1234')

#         rps = self._get_rps()
#         xml_rps = xml_gerar_rps(certificado, rps=rps)
        xml_rps = '<rps></rps>'
        lote = self._get_valid()
        xml_to_send = xml_gerar_lote(certificado, lote=lote)
        
        return valid_xml(certificado, xml=xml_to_send, ambiente='nproducao')

def main():
    nfse = test_nfse_curitibana()
    ret = nfse.test_valid_lote()
    print(str(ret))


if __name__ == '__main__':
    main()
