# -*- coding: utf-8 -*-
u"""
============================================================
 AS FIGURAS DESTE CADERNO SAEM DAS FOLHAS DE PAPEL

 ⭐ Regra do Marcos (14/set/2026): *"procure na internet, nada de imagem gerada
    por IA, utilize das atividades"*. Cada figura aqui foi RECORTADA de uma
    folha que a professora usa no papel — a MESMA folha que deu o gesto.

 Folhas de origem (colhidas em 22/set/2026 por `buscar-fotos.yml`, busca 1):
   · `f19` = `_sequencias/colheita/ano3/d19b1_8800e4.png` (1414x2000)
       "Pinte o numero de silabas das palavras e classifique-as em:
        (1) monossilaba (2) dissilaba (3) trissilaba (4) polissilaba"
       Grade de 3 colunas x 4 linhas, desenho em cima e a palavra embaixo.
       -> e a folha que da o GESTO das folhas 14 e 15 (pintar uma bolinha por
          silaba) e as doze figuras.
   · `f11` = `_sequencias/colheita/ano3/d11b1_158a27.jpg` (743x1050)
       "SEPARE OS NOMES DOS ANIMAIS EM SILABAS E RESPONDA AS PERGUNTAS -
        QUANTAS LETRAS? QUANTAS SILABAS?"
       -> e a folha que da o gesto da folha 5 (letra x silaba) e os cinco
          animais.

 ⚠️ AS DUAS SAO SCAN EM PRETO E BRANCO, e as figuras saem EM LINHA, nao
    coloridas. E o que a folha de papel da, e e o que a crianca ve na aula.
    Declarado no `POTE-SIL3-NUMERO.md §3`.

 ⚠️ A CAIXA SE CONFERE NA FOLHA DE ORIGEM, nunca no PNG (licao de 21/set/2026):
    o `aperta()` tira o branco de sobra e o recorte SEMPRE sai com cara de
    figura inteira, mesmo com metade do desenho cortada. Por isso duas coisas:
      · a caixa CRESCE ate a tinta acabar (`cresce_caixa`), em vez de ser
        marcada a olho;
      · o `img/RECORTE.json` guarda a folha e a caixa, e o portao `1i7` volta
        la para medir se a tinta continua para fora.

 Uso: python3 _sil3/recortar_das_folhas.py
============================================================
"""
from __future__ import print_function

import io
import json
import os
import sys

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "_padrao"))
from recorte_folha import limpa_fundo, tira_halo, aperta          # noqa: E402

IMG = os.path.join(AQUI, "img")
FOLHAS = {
    "f19": os.path.join(RAIZ, "_sequencias/colheita/ano3/d19b1_8800e4.png"),
    "f11": os.path.join(RAIZ, "_sequencias/colheita/ano3/d11b1_158a27.jpg"),
}

# ⚠️ A GRADE DA f19 NAO FOI MARCADA A OLHO — foi MEDIDA. As bordas saem da
#    projecao de tinta da propria folha (coluna/linha escura que atravessa a
#    pagina inteira): verticais em x = 44, 485, 927, 1369 e horizontais em
#    y = 417, 773, 1130, 1486, 1843. Sao 3 colunas x 4 linhas de 441 x 356 px.
#    **Fracao chutada nao e medida** — a primeira volta deste script escreveu as
#    fracoes de cabeca e custou duas rodadas de conserto.
F19 = [["s3_caderno", "s3_abacaxi", "s3_borboleta"],
       ["s3_pao", "s3_jacare", "s3_bone"],
       ["s3_chapeu", "s3_tres", "s3_cenoura"],
       ["s3_pe", "s3_cadeado", "s3_cachorro"]]
COL_BORDA = [44, 485, 927, 1369]
LIN_BORDA = [417, 773, 1130, 1486, 1843]
INSET = 7                # entra para dentro da borda da grade

# ⚠️ CADA QUADRO DA f19 TEM QUATRO COISAS, e so UMA delas e a figura:
#      · o DESENHO, no meio de cima            <- e o que a gente quer
#      · o `( )` do canto SUPERIOR DIREITO     <- e a resposta que a crianca
#        escreve; figura com a resposta impressa e defeito medido
#      · a PALAVRA escrita, logo abaixo        <- na tela quem escreve e o app
#      · as BOLINHAS de pintar, no rodape
#    E ainda ha a MARCA D'AGUA "@atividadesdiversificadas" em pe, colada na
#    lateral da pagina, que entra no quadro da primeira coluna.
#    Por isso o recorte aqui nao e uma caixa: e uma ESCOLHA DE MANCHAS.
PAR_X0, PAR_Y1 = 0.70, 0.32      # o `( )` mora no canto: x > 70%, y < 32%
# ⚠️ A MARCA D'AGUA NAO E UMA MANCHA COMPRIDA — e LETRA POR LETRA em pe, cada
#    uma baixinha. A primeira regra que escrevi pedia mancha alta (>45% do
#    quadro) e por isso nao pegou nenhuma: o pe saiu com 373 px de largura,
#    260 de desenho e o resto de "@atividadesdiversificadas". O que as letras
#    tem em comum nao e o tamanho, e o LUGAR: elas se espremem na beirada.
MARCA_BEIRA = 0.06               # mancha inteira nos 6% da lateral e marca
PALAVRA_Y0 = 0.64                # abaixo disso so ha palavra e bolinhas
CAIXA_MIN = 40                   # so mancha deste tamanho manda no tamanho
LETRA_MIN = 120                  # ⚠️ ACENTO NAO E LETRA para esta conta: o
#                                  acento do "e" de "pe" fica ACIMA do corpo
#                                  das letras e, se contar, o teto sobe e a
#                                  sola do pe e raspada. Corpo de letra tem
#                                  120 px de tinta para cima.
LETRA_MAX = 1400                 # mancha menor que isto, na faixa da palavra,
#                                  e LETRA — e e o topo delas que diz onde a
#                                  palavra comeca (o cachorro encosta o risco
#                                  da pata no "h" de "cachorro" e vira uma
#                                  mancha so; sem este corte a palavra ia junto)

# a f11 nao tem grade: cinco animais em coluna, cada um com o seu quadro
# ⚠️ ESTAS CINCO FORAM MEDIDAS DUAS VEZES. Na primeira eu escrevi as fracoes
#    de cabeca e o tatu saiu com 86x19 px e o tamandua com 18x15 — pedacinhos de
#    linha, nao bichos. **Fracao chutada nao e medida**: a segunda vez foi
#    abrindo a folha ampliada e lendo a posicao de cada desenho.
F11 = [
    (u"s3_tatu",     0.062, 0.236, 0.260, 0.338),
    (u"s3_girafa",   0.067, 0.383, 0.241, 0.529),
    (u"s3_tamandua", 0.094, 0.576, 0.256, 0.650),
    (u"s3_gato",     0.121, 0.690, 0.256, 0.795),
    (u"s3_urso",     0.125, 0.846, 0.252, 0.960),
]


def cresce_caixa(im, cx, teto=1.7, lim=232):
    u"""A caixa marcada a olho CORTA — a mancha de tinta que encosta na borda
    continua para fora dela. Aqui a caixa cresce ate a tinta acabar.

    ⚠️ A mancha so conta se 60% dela estiver DENTRO da caixa inicial (licao paga
       no `_dinheiro5`): sem isso, a LINHA DA GRADE da folha, que atravessa tudo,
       arrastaria a caixa ate engolir a folha inteira."""
    import numpy as np
    from scipy import ndimage

    x0, y0, x1, y1 = cx
    W, H = im.size
    mx, my = int((x1 - x0) * (teto - 1) / 2), int((y1 - y0) * (teto - 1) / 2)
    ax0, ay0 = max(0, x0 - mx), max(0, y0 - my)
    ax1, ay1 = min(W, x1 + mx), min(H, y1 + my)
    a = np.asarray(im.convert("L").crop((ax0, ay0, ax1, ay1)))
    marca, n = ndimage.label(a < lim)
    if not n:
        return cx
    jan = marca[y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0]
    dentro = set()
    for i in np.unique(jan):
        if not i:
            continue
        if (jan == i).sum() >= 0.60 * (marca == i).sum():
            dentro.add(int(i))
    if not dentro:
        return cx
    ys, xs = np.where(np.isin(marca, list(dentro)))
    return (ax0 + int(xs.min()), ay0 + int(ys.min()),
            ax0 + int(xs.max()) + 1, ay0 + int(ys.max()) + 1)


def caixa_do_desenho(im, cel, aviso):
    u"""Dentro do quadro da f19, acha a caixa SO DO DESENHO.

    Nao e a caixa que eu marquei: e a uniao das manchas de tinta que sobraram
    depois de jogar fora o `( )`, a marca d'agua e a palavra. Cada descarte e
    impresso, para o proximo que ler saber o que o script tirou."""
    import numpy as np
    from scipy import ndimage

    cx0, cy0, cx1, cy1 = cel
    x0, y0 = cx0 + INSET, cy0 + INSET
    x1, y1 = cx1 - INSET, cy1 - INSET
    L, A = float(x1 - x0), float(y1 - y0)
    a = np.asarray(im.convert("L").crop((x0, y0, x1, y1))) < 160
    marca, n = ndimage.label(a)
    if not n:
        return None
    caixas = ndimage.find_objects(marca)

    manchas = []
    for i, sl in enumerate(caixas):
        area = int((marca[sl] == i + 1).sum())
        # ⚠️ O PISO AQUI E BAIXO DE PROPOSITO. Com piso de 40 px o ACENTO do
        #    "e" de "pe" nao era classificado, entao nao era descartado, entao
        #    nao era apagado — e aparecia como um risquinho solto embaixo do
        #    desenho. Quem manda no TAMANHO da caixa continua sendo so a mancha
        #    grande (`CAIXA_MIN`); esta lista e para saber o que apagar.
        if area < 8:
            continue
        fx0, fx1 = sl[1].start / L, sl[1].stop / L
        fy0, fy1 = sl[0].start / A, sl[0].stop / A
        manchas.append({"i": i + 1, "area": area,
                        "x0": fx0, "x1": fx1, "y0": fy0, "y1": fy1,
                        "px": (sl[1].start, sl[0].start, sl[1].stop, sl[0].stop)})

    # 1. o `( )` do canto superior direito
    par = [m for m in manchas if m["x0"] > PAR_X0 and m["y1"] < PAR_Y1]
    # 2. a marca d'agua em pe, espremida na beirada do quadro
    dagua = [m for m in manchas
             if m["x1"] < MARCA_BEIRA or m["x0"] > 1 - MARCA_BEIRA]
    # 3. tudo que nasce abaixo da linha da palavra (palavra e bolinhas)
    rodape = [m for m in manchas if m["y0"] > PALAVRA_Y0]

    fora = {id(m) for m in par + dagua + rodape}
    desenho = [m for m in manchas if id(m) not in fora]
    if not desenho:
        return None
    mede = [m for m in desenho if m["area"] >= CAIXA_MIN] or desenho

    # 4. o TETO DA PALAVRA: as letras que sobraram soltas na faixa de baixo
    #    dizem onde a palavra comeca. Se uma mancha do desenho passar dali, ela
    #    esta grudada na palavra (o risco da pata do cachorro) e se corta ali.
    #    ⚠️ A MARCA D'AGUA TAMBEM E FEITA DE LETRAS, e ela desce a lateral
    #       INTEIRA — se entrar nesta conta, o teto sobe para a altura da
    #       primeira letrinha dela e o desenho e fatiado. Foi o que aconteceu
    #       com o pe: os dedos sairam cortados. Descarta-se a lateral ANTES.
    sob = {id(m) for m in dagua}
    letras = [m for m in rodape
              if LETRA_MIN <= m["area"] <= LETRA_MAX and id(m) not in sob]
    teto = min([m["px"][1] for m in letras]) - 4 if letras else y1 - y0

    px0 = min(m["px"][0] for m in mede)
    py0 = min(m["px"][1] for m in mede)
    px1 = max(m["px"][2] for m in mede)
    py1 = max(m["px"][3] for m in mede)
    cortou = py1 > teto
    py1 = min(py1, teto)

    # ⚠️ DESCARTAR A MANCHA NAO BASTA — O CORTE E RETANGULO. O `(` do chapeu e
    #    do pe comeca acima do desenho e TERMINA dentro dele: a mancha ficou de
    #    fora da conta da caixa e o rabo dela ficou dentro do retangulo, como um
    #    risquinho solto no canto. Por isso o que foi descartado se APAGA da
    #    folha antes de cortar — senao some da medida e continua na tela.
    #    ⚠️ E APAGAR SO O PRETO DEIXA O CINZA: a borda de cada traco do scan e
    #       clara demais para o corte de 160, entao o `(` sumia e a sombra dele
    #       ficava. Por isso a mancha descartada se ENGORDA 3 px antes de virar
    #       branco — longe do desenho, que mora no meio do quadro.
    peca = im.crop((x0, y0, x1, y1)).convert("RGB")
    sobra = np.isin(marca, [m["i"] for m in manchas if id(m) in fora])
    sobra = ndimage.binary_dilation(sobra, iterations=3)
    if sobra.any():
        arr = np.asarray(peca).copy()
        arr[sobra] = 255
        peca = Image.fromarray(arr)
    peca = peca.crop((px0, py0, px1, py1))

    if par:
        aviso.append(u"tirou o `( )` da resposta")
    if dagua:
        aviso.append(u"tirou a marca d'agua da lateral")
    if cortou:
        aviso.append(u"o desenho encostava na palavra; cortado no teto dela")
    return (x0 + px0, y0 + py0, x0 + px1, y0 + py1), peca


def pecas():
    u"""(nome, folha, caixa_em_px_ou_None, fracao) — a f19 se resolve por
    manchas (ver `caixa_do_desenho`); a f11 por caixa marcada + `cresce_caixa`."""
    fora = []
    for li, linha in enumerate(F19):
        for ci, nome in enumerate(linha):
            cel = (COL_BORDA[ci], LIN_BORDA[li],
                   COL_BORDA[ci + 1], LIN_BORDA[li + 1])
            fora.append((nome, "f19", cel, None))
    for nome, x0, y0, x1, y1 in F11:
        fora.append((nome, "f11", None, (x0, y0, x1, y1)))
    return fora


def main():
    if not os.path.isdir(IMG):
        os.makedirs(IMG)
    # ⚠️ AS TRÊS PEÇAS DE INTERFACE VÊM DO ESQUELETO e NÃO saem de folha de
    #    papel nenhuma — o selo aceso, o selo apagado e o troféu do fim. Elas
    #    se declaram `banco:` (é a convenção dos outros cadernos), senão o
    #    portão 1i5 diz, com razão, que há figura no disco sem procedência.
    abertas, recorte = {}, {}
    origem = {u"s3_selo.png": u"banco:selo",
              u"s3_selo_off.png": u"banco:selo",
              u"s3_trofeu.png": u"banco:trofeu"}
    for nome, folha, cel, frac in pecas():
        cam = FOLHAS[folha]
        if folha not in abertas:
            abertas[folha] = Image.open(cam).convert("RGB")
        f = abertas[folha]
        W, H = f.size
        aviso = []
        if cel is not None:
            achado = caixa_do_desenho(f, cel, aviso)
            if achado is None:
                print(u"  %-14s NAO ACHEI TINTA no quadro %s" % (nome, cel))
                continue
            cx, peca = achado
        else:
            fx0, fy0, fx1, fy1 = frac
            cx = (int(fx0 * W), int(fy0 * H), int(fx1 * W), int(fy1 * H))
            cx = cresce_caixa(f, cx)
            peca = f.crop(cx)
        c = limpa_fundo(peca.convert("RGBA"))
        c = tira_halo(c, voltas=2)
        c = aperta(c)
        c.thumbnail((400, 400))
        c.save(os.path.join(IMG, nome + ".png"))
        origem[nome + ".png"] = u"folha:%s (%s)" % (folha, os.path.basename(cam))
        recorte[nome + ".png"] = {
            u"folha": os.path.relpath(cam, RAIZ),
            u"caixa": list(cx),
            u"tamanho": list(c.size),
        }
        print(u"  %-14s %s  %dx%d   %s"
              % (nome, folha, c.size[0], c.size[1], u"; ".join(aviso)))

    for arq, dado in ((u"ORIGEM.json", origem), (u"RECORTE.json", recorte)):
        io.open(os.path.join(IMG, arq), "w", encoding="utf-8").write(
            json.dumps(dado, ensure_ascii=False, indent=1) + u"\n")
    print(u"\n%d figura(s) em %s" % (len(pecas()), IMG))


if __name__ == "__main__":
    main()
