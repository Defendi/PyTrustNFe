# -*- coding: utf-8 -*-
# © 2017 Edson Bernardino, ITK Soft
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# Classe para geração de PDF da DANFE a partir de xml etree.fromstring

import os
from io import BytesIO
from textwrap import wrap
import math
from xml.sax.saxutils import unescape

from reportlab.lib import utils
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, cm
from reportlab.lib.pagesizes import A4,A5,A6
from reportlab.lib.colors import black, gray
from reportlab.graphics.barcode import code128
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Paragraph, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import pytz
from datetime import datetime, timedelta


def chunks(cString, nLen):
    for start in range(0, len(cString), nLen):
        yield cString[start:start + nLen]


def format_cnpj_cpf(value):
    if len(value) < 12:  # CPF
        cValue = '%s.%s.%s-%s' % (value[:-8], value[-8:-5],
                                  value[-5:-2], value[-2:])
    else:
        cValue = '%s.%s.%s/%s-%s' % (value[:-12], value[-12:-9],
                                     value[-9:-6], value[-6:-2], value[-2:])
    return cValue


def getdateByTimezone(cDateUTC, timezone=None):
    '''
    Esse método trata a data recebida de acordo com o timezone do
    usuário. O seu retorno é dividido em duas partes:
    1) A data em si;
    2) As horas;
    :param cDateUTC: string contendo as informações da data
    :param timezone: timezone do usuário do sistema
    :return: data e hora convertidos para a timezone do usuário
    '''

    # Aqui cortamos a informação do timezone da string (+03:00)
    dt = cDateUTC[0:19]

    # Verificamos se a string está completa (data + hora + timezone)
    if timezone and len(cDateUTC) == 25:

        # tz irá conter informações da timezone contida em cDateUTC
        tz = cDateUTC[19:25]
        tz = int(tz.split(':')[0])

        dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')

        # dt agora será convertido para o horario em UTC
        dt = dt - timedelta(hours=tz)

        # tzinfo passará a apontar para <UTC>
        dt = pytz.utc.localize(dt)

        # valor de dt é convertido para a timezone do usuário
        dt = timezone.normalize(dt)
        dt = dt.strftime('%Y-%m-%dT%H:%M:%S')

    cDt = dt[0:10].split('-')
    cDt.reverse()
    return '/'.join(cDt), dt[11:16]


def format_number(cNumber):
    if cNumber:
        # Vírgula para a separação de milhar e 2f para 2 casas decimais
        cNumber = "{:,.2f}".format(float(cNumber))
        return cNumber.replace(",", "X").replace(".", ",").replace("X", ".")
    return ""


def tagtext(oNode=None, cTag=None):
    try:
        xpath = ".//{http://www.portalfiscal.inf.br/nfe}%s" % (cTag)
        cText = unescape(oNode.find(xpath).text)
    except:
        cText = ''
    return cText


REGIME_TRIBUTACAO = {
    '1': 'Simples Nacional',
    '2': 'Simples Nacional, excesso sublimite de receita bruta',
    '3': 'Regime Normal'
}


def get_image(path, width=False, height=False):
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    if not height and not width:
        width = iw
        height = ih
    elif height and not width:
        aspect = iw / float(ih)
        width = (height * aspect)
    elif not height and width:
        aspect = ih / float(iw)
        height = (width * aspect)
    return Image(path, width=width, height=height), width, height


class danfe_simplificado(object):

    def __init__(self, sizepage=A6, list_xml=None, 
                 orientation='portrait', logo=None, cce_xml=None,
                 timezone=None, rascunho=False):

        path = os.path.join(os.path.dirname(__file__), 'fonts')
        pdfmetrics.registerFont(
            TTFont('NimbusSanL-Regu',os.path.join(path, 'NimbusSanL Regular.ttf')))
        pdfmetrics.registerFont(
            TTFont('NimbusSanL-Bold',os.path.join(path, 'NimbusSanL Bold.ttf')))
        self.rascunho = rascunho
        self.nrLin = 0
        if sizepage == A5:
            self.width = 148    # 14.8 x 21 cm
            self.height = 210
            self.nLeft = 6
            self.nRight = 10
            self.nTop = 7
            self.nBottom = 8
            self.pLin = 7
            self.step = 3
        elif sizepage == A6:
            self.width = 105    # 14.8 x 21 cm
            self.height = 148
            self.nLeft = 4
            self.nRight = 10
            self.nTop = 6
            self.nBottom = 8
            self.pLin = 6
            self.step = 2

        else:
            raise NameError('Tamanho não implementado')

        self.logo = logo

        self.oPDF_IO = BytesIO()
        if orientation == 'landscape':
            raise NameError('Rotina não implementada')
        else:
            size = sizepage

        self.canvas = canvas.Canvas(self.oPDF_IO, pagesize=size)
        self.canvas.setTitle('DANFE SIMPLIFICADA')
        self.canvas.setStrokeColor(black)
        
        for oXML in list_xml:
            self.NrPages = 1
            self.Page = 1
            
            if sizepage == A5:
                self.bodyA5(oXML=oXML,timezone=timezone)
            if sizepage == A6:
                self.bodyA6(oXML=oXML,timezone=timezone)
            el_det = oXML.findall(".//{http://www.portalfiscal.inf.br/nfe}det")

            nId = 0
            if el_det is not None:
                list_desc = []
                list_cod_prod = []
                for nId, item in enumerate(el_det):
                    el_prod = item.find(".//{http://www.portalfiscal.inf.br/nfe}prod")
                    infAdProd = item.find(".//{http://www.portalfiscal.inf.br/nfe}infAdProd")

                    list_ = wrap(tagtext(oNode=el_prod, cTag='xProd'), 50)
                    if infAdProd is not None:
                        list_.extend(wrap(infAdProd.text, 50))
                    list_desc.append(list_)

                    list_cProd = wrap(tagtext(oNode=el_prod, cTag='cProd'), 14)
                    list_cod_prod.append(list_cProd)

                # Calculando nr. aprox. de páginas
                if nId > 25:
                    self.NrPages += math.ceil((nId - 25) / 70)

            self.canvas.setLineWidth(.5)

            index = self.produtos(oXML=oXML, el_det=el_det, max_index=nId,
                                 list_desc=list_desc, list_cod_prod=list_cod_prod,
                                 sizepage=sizepage)

            self.rodapeA6(oXML=oXML)

            self.rect(3, 3, self.width - 6, self.pLin)

            self.newpage()
        self.canvas.save()

    def bodyA5(self, oXML=None, timezone=None):
        elem_infNFe = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}infNFe")
        elem_ide = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}ide")
         
        cChave = elem_infNFe.attrib.get('Id')[3:]
        barcode128 = code128.Code128(cChave, barHeight=12 * mm, barWidth=0.27 * mm)
        # Labels
        self.canvas.setFont('NimbusSanL-Bold', 6)
        self.string(self.nLeft, self.pLin, 'DANFE SIMPLIFICADO')
        self.string(self.nLeft+55, self.pLin, 'CHAVE DE ACESSO')
        self.string(self.nLeft, self.pLin+6.5, 'SÉRIE/NÚMERO:')
        self.string(self.nLeft+55, self.pLin+7, 'PROTOCOLO DE AUTORIZAÇÃO DE USO')
        self.string(self.nLeft, self.pLin+10, 'DATA EMISSÃO:')
        
        self.hline(3, self.pLin + 29.5, self.width - 3)

        self.string(self.nLeft, self.pLin+32, 'EMITENTE')
        self.string(self.nLeft, self.pLin+53, 'DESTINATÁRIO')
        self.string(self.nLeft, self.pLin+47, 'CNPJ/CPF')
        self.string(self.nLeft + 60, self.pLin+47, 'IE')
        self.string(self.nLeft, self.pLin+67, 'CNPJ/CPF')
        self.string(self.nLeft + 60, self.pLin+67, 'IE')

        tpNF = tagtext(oNode=elem_ide, cTag='tpNF')
        self.canvas.setFont('NimbusSanL-Regu', 9)
        if tpNF == '1':
            self.string(self.nLeft, self.pLin+3, '1-Saída')
        else:
            self.string(self.nLeft, self.pLin+3, '2-Entrada')
        self.string(self.nLeft+55, self.pLin+3, cChave)
        barcode128.drawOn(self.canvas, (self.nLeft + 22) * mm,(self.height - self.pLin - 25) * mm)

        self.string(self.nLeft+17.5, self.pLin+6.5, '%s/%s' % (tagtext(oNode=elem_ide, cTag='serie'),tagtext(oNode=elem_ide, cTag='nNF')))

        cDt, cHr = getdateByTimezone(tagtext(oNode=elem_ide, cTag='dhEmi'), timezone)
        self.string(self.nLeft+17.5, self.pLin+10, cDt)

        if self.rascunho:
            self.string(self.nLeft+55, self.pLin+10, 'DOCUMENTO SEM VALOR FISCAL')
        else:
            elem_protNFe = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}protNFe")
            cProtocolo = tagtext(oNode=elem_protNFe, cTag='nProt')
            cDt, cHr = getdateByTimezone(tagtext(oNode=elem_protNFe, cTag='dhRecbto'), timezone)
            self.string(self.nLeft+55, self.pLin+10, cProtocolo + ' - ' + cDt + ' ' + cHr)

        elem_emit = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}emit")

        self.string(self.nLeft, self.pLin+36.5, tagtext(oNode=elem_emit, cTag='xNome'))
        cEnd = '%s, %s - %s' % (tagtext(oNode=elem_emit, cTag='xLgr'), 
                                        tagtext(oNode=elem_emit, cTag='nro'),
                                        tagtext(oNode=elem_emit, cTag='xBairro'))
        self.string(self.nLeft, self.pLin+40, cEnd)
        cCid = "%s %s - %s" % (tagtext(oNode=elem_emit, cTag='CEP'),
                               tagtext(oNode=elem_emit, cTag='xMun'),
                               tagtext(oNode=elem_emit, cTag='UF'))
        self.string(self.nLeft, self.pLin+43.5, cCid)
        self.string(self.nLeft+12, self.pLin+47, format_cnpj_cpf(tagtext(oNode=elem_emit, cTag='CNPJ')))
        if tagtext(oNode=elem_emit, cTag='IE'):
            self.string(self.nLeft + 63.5, self.pLin + 47,tagtext(oNode=elem_emit, cTag='IE'))

        self.hline(3, self.pLin + 50, self.width - 3)

        elem_dest = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}dest")

        self.string(self.nLeft, self.pLin+56.5, tagtext(oNode=elem_dest, cTag='xNome'))
        cEnd = '%s, %s - %s' % (tagtext(oNode=elem_dest, cTag='xLgr'), 
                                        tagtext(oNode=elem_dest, cTag='nro'),
                                        tagtext(oNode=elem_dest, cTag='xBairro'))
        self.string(self.nLeft, self.pLin+60, cEnd)
        cCid = "%s %s - %s" % (tagtext(oNode=elem_dest, cTag='CEP'),
                               tagtext(oNode=elem_dest, cTag='xMun'),
                               tagtext(oNode=elem_dest, cTag='UF'))
        self.string(self.nLeft, self.pLin+63.5, cCid)

        cnpj_cpf = tagtext(oNode=elem_dest, cTag='CNPJ')
        if cnpj_cpf:
            cnpj_cpf = format_cnpj_cpf(cnpj_cpf)
        else:
            cnpj_cpf = format_cnpj_cpf(tagtext(oNode=elem_dest, cTag='CPF'))
        self.string(self.nLeft+12, self.pLin+67, cnpj_cpf)

        if tagtext(oNode=elem_dest, cTag='IE/RG'):
            self.string(self.nLeft + 63.5, self.pLin + 67,tagtext(oNode=elem_dest, cTag='IE'))

        self.hline(3, self.pLin + 69, self.width - 3)

    def bodyA6(self, oXML=None, timezone=None):
        elem_infNFe = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}infNFe")
        elem_ide = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}ide")
         
        cChave = elem_infNFe.attrib.get('Id')[3:]
        barcode128 = code128.Code128(cChave, barHeight=10 * mm, barWidth=0.23 * mm)
        # Labels
        self.canvas.setLineWidth(.5)
        self.canvas.setFont('NimbusSanL-Bold', 7)
        self.string(self.nLeft, self.pLin, 'DANFE SIMPLIFICADO')
        self.canvas.setFont('NimbusSanL-Bold', 5)
        self.string(self.nLeft+31, self.pLin, 'CHAVE DE ACESSO')
        self.string(self.nLeft, self.pLin+5.5, 'SÉRIE/NÚMERO:')
        self.string(self.nLeft+31, self.pLin+5.5, 'PROTOCOLO DE AUTORIZAÇÃO DE USO')
        self.string(self.nLeft, self.pLin+8, 'DATA EMISSÃO:')
         
        self.hline(3, self.pLin + 23, self.width - 3)
  
        self.string(self.nLeft, self.pLin+25, 'EMITENTE')
        self.string(self.nLeft, self.pLin+39, 'DESTINATÁRIO')
        self.canvas.setFont('NimbusSanL-Bold', 6)
        self.string(self.nLeft, self.pLin+35.5, 'CNPJ/CPF')
        self.string(self.nLeft + 60, self.pLin+35.5, 'IE')
        self.string(self.nLeft, self.pLin+49.5, 'CNPJ/CPF')
        self.string(self.nLeft + 60, self.pLin+49.5, 'IE')
 
        tpNF = tagtext(oNode=elem_ide, cTag='tpNF')
        self.canvas.setFont('NimbusSanL-Regu', 7)
        if tpNF == '1':
            self.string(self.nLeft, self.pLin+3, '1-Saída')
        else:
            self.string(self.nLeft, self.pLin+3, '2-Entrada')
        self.string(self.nLeft+31, self.pLin+2.5, cChave)

        # Logo
        if self.logo:
            img, nwidth, nheight = get_image(self.logo, height=8 * mm)
            ih = (85 * mm / 2) - (nwidth / 2)
            img.drawOn(self.canvas, (self.nLeft + 1) * mm, ((self.height - self.pLin - 9) * mm) - nheight)
        
        barcode128.drawOn(self.canvas, (self.nLeft + 25) * mm,(self.height - self.pLin - 20) * mm)
 
        self.string(self.nLeft+15, self.pLin+5.5, '%s/%s' % (tagtext(oNode=elem_ide, cTag='serie'),tagtext(oNode=elem_ide, cTag='nNF')))
 
        cDt, cHr = getdateByTimezone(tagtext(oNode=elem_ide, cTag='dhEmi'), timezone)
        self.string(self.nLeft+15, self.pLin+8, cDt)
 
        if self.rascunho:
            self.string(self.nLeft+31, self.pLin+8, 'DOCUMENTO SEM VALOR FISCAL')
        else:
            elem_protNFe = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}protNFe")
            cProtocolo = tagtext(oNode=elem_protNFe, cTag='nProt')
            cDt, cHr = getdateByTimezone(tagtext(oNode=elem_protNFe, cTag='dhRecbto'), timezone)
            self.string(self.nLeft+31, self.pLin+8, cProtocolo + ' - ' + cDt + ' ' + cHr)
 
        elem_emit = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}emit")
 
        self.string(self.nLeft, self.pLin+28, tagtext(oNode=elem_emit, cTag='xNome'))
        cEnd = '%s, %s - %s' % (tagtext(oNode=elem_emit, cTag='xLgr'), 
                                        tagtext(oNode=elem_emit, cTag='nro'),
                                        tagtext(oNode=elem_emit, cTag='xBairro'))
        self.string(self.nLeft, self.pLin+30.5, cEnd)
        cCid = "%s %s - %s" % (tagtext(oNode=elem_emit, cTag='CEP'),
                               tagtext(oNode=elem_emit, cTag='xMun'),
                               tagtext(oNode=elem_emit, cTag='UF'))
        self.string(self.nLeft, self.pLin+33, cCid)
        self.string(self.nLeft+12, self.pLin+35.5, format_cnpj_cpf(tagtext(oNode=elem_emit, cTag='CNPJ')))
        if tagtext(oNode=elem_emit, cTag='IE'):
            self.string(self.nLeft + 63.5, self.pLin + 35.5,tagtext(oNode=elem_emit, cTag='IE'))
 
        self.hline(3, self.pLin + 37, self.width - 3)
 
        elem_dest = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}dest")
 
        self.string(self.nLeft, self.pLin+42, tagtext(oNode=elem_dest, cTag='xNome'))
        cEnd = '%s, %s - %s' % (tagtext(oNode=elem_dest, cTag='xLgr'), 
                                        tagtext(oNode=elem_dest, cTag='nro'),
                                        tagtext(oNode=elem_dest, cTag='xBairro'))
        self.string(self.nLeft, self.pLin+44.5, cEnd)
        cCid = "%s %s - %s" % (tagtext(oNode=elem_dest, cTag='CEP'),
                               tagtext(oNode=elem_dest, cTag='xMun'),
                               tagtext(oNode=elem_dest, cTag='UF'))
        self.string(self.nLeft, self.pLin+47, cCid)
 
        cnpj_cpf = tagtext(oNode=elem_dest, cTag='CNPJ')
        if cnpj_cpf:
            cnpj_cpf = format_cnpj_cpf(cnpj_cpf)
        else:
            cnpj_cpf = format_cnpj_cpf(tagtext(oNode=elem_dest, cTag='CPF'))
        self.string(self.nLeft+12, self.pLin+49.5, cnpj_cpf)
 
        if tagtext(oNode=elem_dest, cTag='IE/RG'):
            self.string(self.nLeft + 45.5, self.pLin + 49.5,tagtext(oNode=elem_dest, cTag='IE'))
 
        self.pLin += 51
        self.hline(3, self.pLin, self.width - 3)

    def produtos(self, oXML=None, el_det=None, index=0, max_index=0,
                 list_desc=None, list_cod_prod=None, nHeight=29, sizepage=A5):

        def pLin(nwLn = False):
            if nwLn:
                self.pLin += self.step
                self.nrLin += 1
            return self.pLin
        
        if sizepage==A6:
            self.pLin += 2
            self.canvas.setFont('NimbusSanL-Bold', 5)
            self.string(self.nLeft,    self.pLin, 'PRODUTOS/SERVIÇOS')
            self.pLin += 3
            self.string(self.nLeft        , self.pLin, 'COD.')
            self.string(self.nLeft+15     , self.pLin, 'DESCRIÇÃO')
            self.string(self.nLeft+64     , self.pLin, 'UN')
            self.stringRight(self.nLeft+76, self.pLin, 'QTD')
            self.stringRight(self.nLeft+85, self.pLin, 'V.UNIT')
            self.stringRight(self.nLeft+97, self.pLin, 'V.TOTAL')
            self.pLin += 3

        self.canvas.setFont('NimbusSanL-Regu', 6)
        for id in range(index, max_index + 1):
            item = el_det[id]
            el_prod = item.find(".//{http://www.portalfiscal.inf.br/nfe}prod")
            infAdProd = item.find(".//{http://www.portalfiscal.inf.br/nfe}infAdProd")

            desc_ = wrap(tagtext(oNode=el_prod, cTag='xProd'), 38)
            if infAdProd is not None:
                desc_.append('')
                desc_.extend(wrap(infAdProd.text, 38))

            self.string(self.nLeft, pLin(), str(tagtext(oNode=el_prod, cTag='cProd'))[:11])
            self.string(self.nLeft+64, pLin(), str(tagtext(oNode=el_prod, cTag='uCom'))[:4])
            self.stringRight(self.nLeft+76, pLin(), format_number(tagtext(oNode=el_prod, cTag='qCom')))
            self.stringRight(self.nLeft+85, pLin(), format_number(tagtext(oNode=el_prod, cTag='vUnCom')))
            self.stringRight(self.nLeft+97, pLin(), format_number(tagtext(oNode=el_prod, cTag='vProd')))
            for nr, ln in enumerate(desc_):
                self.string(self.nLeft+15, pLin(True if nr > 0 else False), ln)
            pLin(True)
            self.pLin += 1

    def rodapeA6(self, oXML=None):
        el_infAdic = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}infAdic")
        el_ICMSTot = oXML.find(".//{http://www.portalfiscal.inf.br/nfe}ICMSTot")

        self.hline(3, self.pLin, self.width - 3)
        self.canvas.setFont('NimbusSanL-Bold', 5)
        self.string(self.nLeft+60, self.pLin + 2, 'TOTAL DA NOTA')
        self.canvas.setFont('NimbusSanL-Regu', 8)
        self.stringRight(self.nLeft+97, self.pLin + 2.5, format_number(tagtext(oNode=el_ICMSTot, cTag='vNF')))
        self.pLin += 3

        self.hline(3, self.pLin, self.width - 3)
        self.canvas.setFont('NimbusSanL-Bold', 5)
        self.string(self.nLeft, self.pLin + 2, 'DADOS ADICIONAIS')

        fisco = tagtext(oNode=el_infAdic, cTag='infAdFisco')
        observacoes = tagtext(oNode=el_infAdic, cTag='infCpl')
        if fisco:
            observacoes = fisco + ' ' + observacoes

        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        styleN.fontSize = 6
        styleN.fontName = 'NimbusSanL-Regu'
        styleN.leading = 7
        P = Paragraph(observacoes, styles['Normal'])
        w, h = P.wrap(90 * mm, 40 * mm)
        altura = (self.height - self.pLin - 3) * mm
        P.drawOn(self.canvas, (self.nLeft + 1) * mm, altura - h)

        self.pLin += round(h/mm)+3

    def newpage(self):
        self.pLin = self.nTop
        self.nrLin = 0
        self.Page += 1
        self.canvas.showPage()

    def hline(self, x, y, width):
        y = self.height - y
        self.canvas.line(x * mm, y * mm, width * mm, y * mm)

    def vline(self, x, y, width):
        width = self.height - y - width
        y = self.height - y
        self.canvas.line(x * mm, y * mm, x * mm, width * mm)

    def rect(self, col, lin, nWidth, nHeight, fill=False):
        lin = self.height - nHeight - lin
        self.canvas.rect(col * mm, lin * mm, nWidth * mm, nHeight * mm,
                         stroke=True, fill=fill)

    def string(self, x, y, value):
        y = self.height - y
        self.canvas.drawString(x * mm, y * mm, value)

    def stringRight(self, x, y, value):
        y = self.height - y
        self.canvas.drawRightString(x * mm, y * mm, value)

    def stringcenter(self, x, y, value):
        y = self.height - y
        self.canvas.drawCentredString(x * mm, y * mm, value)

    def writeto_pdf(self, fileObj):
        pdf_out = self.oPDF_IO.getvalue()
        self.oPDF_IO.close()
        fileObj.write(pdf_out)

    def _paragraph(self, text, font, font_size, x, y):
        ptext = '<font size=%s>%s</font>' % (font_size, text)
        style = ParagraphStyle(name='Normal',
                               fontName=font,
                               fontSize=font_size,
                               spaceAfter=1,
                               )
        paragraph = Paragraph(ptext, style=style)
        w, h = paragraph.wrapOn(self.canvas, x, y)
        return w, h, paragraph
    