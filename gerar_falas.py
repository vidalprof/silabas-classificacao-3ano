# -*- coding: utf-8 -*-
u"""
============================================================
 ESQUELETO — gerador das falas da folha viva

 ⚠️ REGRA DA CASA: o `falas.json` é a VERDADE. Texto escrito aqui = voz gravada.
    Texto mudou = voz regravada (o `entregar.yml` compara o carimbo sha1). É isto
    que acaba com "a tela diz uma coisa e a voz diz outra" — e atividade sem
    `falas.json` NÃO TEM COMO SER CONFERIDA, porque mp3 não se lê.

 ⚠️ UMA FONTE SÓ. As palavras, as frases e os textos moram no bloco
    `/*DADOS-INI*/` do `index.html` e são LIDOS daqui. Nada de segunda lista
    para desencontrar: já custou caro nesta casa um relatório sair zero com a
    folha inteira respondida.

 ⚠️ TODA TELA É NARRADA, e o alto-falante entra também em CADA RESPOSTA que a
    criança toca. Regra do Marcos: *"o alto-falante nas respostas também, para
    ajudar os alunos que não sabem ler"*. Sem isso a criança que ainda soletra
    escolhe pelo tamanho da palavra e a folha vira sorteio.

 ⚠️ A DICA NUNCA DIZ A RESPOSTA. Ela manda olhar uma pista, ou faz outra
    pergunta. Responder no segundo erro não é ajudar: é tirar da criança a única
    chance de pensar de novo.

 ⚠️ PALAVRAS QUE A VOZ ERRA (medido, e o portão `_qa/falas.py` reprova):
    "complete" vira "complite" — usar "preencha". Letra solta ("som S") sai como
    o NOME da letra: ancorar num exemplo ("o som de SAPO").

 Uso:  python3 <pasta>/gerar_falas.py
 Saída: reescreve os blocos FALAS e VOZOK do index.html, o `falas.json` e o
        `voz.txt`.
============================================================
"""
from __future__ import print_function

import collections
import io
import json
import os
import re
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
CAM = os.path.join(AQUI, u"index.html")
PREFIXO = u"s3_"                     # <- o prefixo desta atividade
VOZ = u"pt-BR-AntonioNeural"

D = io.open(CAM, encoding=u"utf-8").read()


def bloco(nome):
    u"""Lê um objeto do bloco DADOS do index.html. Uma fonte só.

    ⚠️ ELE CONTA AS CHAVES, e isso foi conserto de 15/set/2026. O esqueleto
       procurava o fim do objeto por uma marca de texto (`\n});`) — e QUALQUER
       objeto que não terminasse exatamente assim fazia a leitura passar
       adiante e engolir o bloco seguinte. No primeiro caderno do 2º ano os
       vinte e três blocos falharam de uma vez, todos com o mesmo erro, e a
       mensagem do json não dizia nada sobre a causa. Contar chave por chave
       (pulando as que estão DENTRO de texto) acha o fim de qualquer objeto.
    """
    i = D.find(u"var " + nome + u" = ")
    if i < 0:
        raise SystemExit(u"nao achei o bloco `var %s` no index.html" % nome)
    i = D.index(u"{", i)
    nivel, j, dentro, escapa = 0, i, False, False
    while j < len(D):
        c = D[j]
        if dentro:
            if escapa:
                escapa = False
            elif c == u"\\":
                escapa = True
            elif c == u'"':
                dentro = False
        else:
            if c == u'"':
                dentro = True
            elif c == u"{":
                nivel += 1
            elif c == u"}":
                nivel -= 1
                if nivel == 0:
                    j += 1
                    break
        j += 1
    txt = D[i:j]
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    txt = re.sub(r'"\s*\+\s*\n\s*"', "", txt)                 # junta "a" + "b"
    # ⚠️ SEM O `"?` DOS DOIS LADOS, e isso foi conserto de 20/set/2026.
    #    Esta linha normaliza chave sem aspas (`chave:` -> `"chave":`). Com o
    #    `"?` ela também casava DENTRO de uma string: a opção
    #        ["b", "Não: é um MÚSCULO que ajuda o ar a entrar"]
    #    virava  ["b", "Não": é um MÚSCULO ...]  e o json.loads morria com
    #    "Expecting ',' delimiter", sem dizer uma palavra sobre a causa.
    #    Qualquer caderno com DOIS-PONTOS dentro de um texto caía nisso.
    #    Chave já entre aspas não precisa de conserto nenhum — então a regex
    #    só olha as SEM aspas, e string nenhuma é tocada.
    txt = re.sub(r'([\{,]\s*)([A-Za-zÀ-ÿ_0-9]+)\s*:', r'\1"\2":', txt)
    txt = re.sub(r",(\s*[\}\]])", r"\1", txt)
    return json.loads(txt)


# ⚠️⚠️ A ENTIDADE HTML TAMBÉM É MARCAÇÃO, e isto foi lição paga (15/set/2026,
#    caderno de inglês do 8º ano). O `lp` tirava as TAGS e deixava as
#    ENTIDADES, então a lista de ingredientes da pizza — escrita com `&middot;`
#    para virar o ponto que separa os itens — ia para a fila de gravação como
#    *"Oil and middot Tomato sauce and middot Some onions"*. O portão
#    `_qa/revisor.py` pegou; se não pegasse, a voz teria dito isso à criança.
_ENT = {u"&middot;": u",", u"&nbsp;": u" ", u"&amp;": u" e ", u"&mdash;": u" ",
        u"&ndash;": u" ", u"&hellip;": u" ", u"&quot;": u'"', u"&lt;": u"",
        u"&gt;": u"", u"&#39;": u"'", u"&apos;": u"'"}


def lp(s):
    u"""tira a marcação e deixa o texto do jeito que a voz vai dizer"""
    t = re.sub(r"<[^>]+>", " ", s or u"")
    for _e, _v in _ENT.items():
        t = t.replace(_e, _v)
    t = re.sub(r"\s+", u" ", t)
    # ⚠️ e a tag que vira espaco deixa um vao ANTES da pontuacao ("o cinema ."),
    #    que o `_qa/revisor.py` acusa — com razao: a voz faz a pausa no lugar
    #    errado. Cola a pontuacao de volta na palavra.
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    # ⚠️ E A VIRGULA DA PAUSA PODE ENCOSTAR NUMA QUE JA EXISTIA (15/set/2026):
    #    a frase "My dad, ___ travels a lot" virou "My dad,, travels a lot" —
    #    duas virgulas coladas, que o Edge TTS le como uma pausa estranha e
    #    longa demais. Uma so, sempre.
    t = re.sub(r",\s*,+", u",", t)
    return t.strip()


def ch(w):
    return re.sub(r"[^a-z]", "",
                  unicodedata.normalize("NFKD", w.lower())
                  .encode("ascii", "ignore").decode())


F = collections.OrderedDict()


def p(k, v):
    F[k] = v


# ---------------------------------------------------------------------------
# AS FALAS DO MOTOR — estas toda folha viva tem
# ---------------------------------------------------------------------------
p(u"capa", u"Aprendendo a classificar as palavras pelo número de sílabas. "
           u"Trinta e cinco folhas para descobrir se uma palavra é monossílaba, "
           u"dissílaba, trissílaba ou polissílaba. Escreva o seu nome ali embaixo "
           u"e toque em Começar.")
p(u"folhaPronta", u"Folha pronta! Muito bem.")
p(u"escreva", u"Escreva a palavra usando o teclado.")
p(u"ligue", u"Toque numa palavra do lado esquerdo e depois na do lado direito.")
p(u"toque_palavra", u"Primeiro toque numa palavra ali embaixo. Depois toque na "
                    u"gaveta dela.")
p(u"toque_figura", u"Primeiro toque numa figura ali embaixo. Depois toque na "
                   u"gaveta dela.")
p(u"pegue_lapis", u"Antes de pintar, pegue uma canetinha ali em cima.")
p(u"caca_toque", u"Toque primeiro na casa onde a palavra começa.")
p(u"vozOn", u"Narração ligada!")
p(u"fim", u"Você chegou ao fim! Agora você sabe pôr qualquer palavra na gaveta "
          u"dela. E fica a pergunta: o nome da sua rua, quantas sílabas tem?")

# ==============================================================================
#  AS SÍLABAS FALADAS — e este bloco é obrigatório em caderno que fale sílaba
#
#  ⚠️⚠️ POR QUE NÃO DÁ PARA SINTETIZAR A SÍLABA SOLTA (e a casa já pagou por
#     isto DUAS vezes — set/2026 e 16/set/2026, as duas o Marcos ouvindo):
#     a voz não lê SOM, lê PALAVRA. Entregue "SA" a ela e ela soletra "esse-á";
#     "VA" vira "vê-á"; "ÇÃ" ela nem tenta, porque ç não começa palavra em
#     português. Escrever a sílaba "como se fala" conserta UM caso e nunca
#     fecha a família.
#
#  O QUE FUNCIONA é o contrário: gravar a PALAVRA INTEIRA — que a voz pronuncia
#  certo, porque é palavra de verdade — alinhar letra a letra com o
#  `ctc-forced-aligner` e CORTAR a sílaba de dentro dela. Quem faz isso é o
#  `_padrao/silabas_voz.py`, dentro do `entregar.yml`, lendo o `silabas.json`
#  que sai daqui. O portão é o `_qa/silabas.py`.
#
#  COMO SE USA: para cada palavra do caderno, uma linha
#      _reg(u"CAVALO", [u"CA", u"VA", u"LO"])
#  e, no app, a sílaba fala por `falarSilaba(null, 0, "VA")` — nunca por
#  `falar("sil_va")`. Caderno que não fala sílaba não escreve nada: o
#  `silabas.json` sai com `"palavras": {}` e o `entregar.yml` nem baixa o
#  alinhador por ele.
#
#  ⚠️ NÃO HÁ FALA DE RESERVA POR SÍLABA. Faltando o recorte, o app diz a
#     PALAVRA INTEIRA. Uma reserva sintetizada seria o defeito voltando pela
#     porta dos fundos — e calado, que é pior.
# ==============================================================================
_SIL_DE = {}          # palavra -> [sílabas, NA ORDEM da palavra]
_MAPA_SIL = {}        # sílaba  -> [palavra, posição]
_RECUSADAS = []


def _reg(palavra, silabas):
    u"""⚠️ A LISTA TEM DE ESTAR NA ORDEM DA PALAVRA. O alinhador corta pelos
    limites das letras: ["RO","CAR"] para CARRO faz sair "ro" onde devia sair
    "car" — e a criança ouve o pedaço errado, sem erro nenhum na tela. Folha de
    ORDENAR guarda as sílabas EMBARALHADAS: passe-as por `_ordena` antes.
    ⚠️ E ganha sempre a partição MAIS FINA: "PIPO"+"CA" fecha PIPOCA sem ser
    separação silábica, e sobrescrevendo PI-PO-CA deixaria a sílaba PI muda."""
    silabas = list(silabas)
    if u"".join(silabas).upper() != palavra.upper():
        _RECUSADAS.append((palavra, silabas))
        return
    velha = _SIL_DE.get(palavra.lower())
    if velha and len(velha) >= len(silabas):
        return
    _SIL_DE[palavra.lower()] = silabas


def _ordena(palavra, embaralhadas):
    u"""as mesmas sílabas na ORDEM em que formam a palavra — sem inventar
    nenhuma: encaixa da esquerda para a direita e desiste se não fechar."""
    resto, saida, alvo = list(embaralhadas), [], palavra.upper()
    while alvo:
        for _i, _sb in enumerate(resto):
            if alvo.startswith(_sb.upper()):
                saida.append(_sb)
                alvo = alvo[len(_sb):]
                resto.pop(_i)
                break
        else:
            return None
    return saida if not resto else None


def _achaSilaba(s):
    u"""a palavra de onde a sílaba será recortada. Ganha a MAIS CURTA: menos
    letras na gravação, menos lugar para o alinhador errar."""
    cand = [_w for _w in sorted(_SIL_DE) if s in _SIL_DE[_w]]
    if not cand:
        return None
    _w = min(cand, key=lambda w: (len(_SIL_DE[w]), len(w), w))
    return [_w, _SIL_DE[_w].index(s)]


def _mapeia(soltas):
    u"""monta o SILMAP das sílabas que o app fala sozinhas, e DEVOLVE as órfãs.
    ⚠️ Sílaba órfã não é erro — o app diz a palavra inteira — mas tem de sair
    IMPRESSA, senão aquele botão emudece sem ninguém saber. Distratora que não
    mora em palavra nenhuma do caderno pede uma PALAVRA-CARREGADORA: uma
    palavra de verdade, curta, registrada só para ser gravada e cortada."""
    orfas = []
    for _s in sorted(set(soltas)):
        _achou = _achaSilaba(_s)
        if _achou:
            _MAPA_SIL[_s] = _achou
        else:
            orfas.append(_s)
    # e a PALAVRA INTEIRA de cada uma precisa existir como fala: é dela que o
    # recorte sai, e é ela que o app diz quando o recorte falta.
    for _w in sorted(_SIL_DE):
        p(u"pal_" + ch(_w), _w.upper() + u".")
    return orfas


# ⚠️ O `_mapeia` SÓ PODE RODAR DEPOIS DE AS PALAVRAS ESTAREM REGISTRADAS —
#    ele procura, para cada sílaba solta, de qual palavra do caderno ela sai.
#    Rodando antes, o SILMAP sai VAZIO e cada pedaço da folha 15 emudece sem
#    erro nenhum. A chamada mora no fim da seção das folhas.


# ---------------------------------------------------------------------------
# A SAÍDA
# ---------------------------------------------------------------------------
# AS FALAS DAS FOLHAS — uma seção por bloco, LENDO OS DADOS do index.html.
#
# ⚠️ UMA FONTE SÓ. Se a frase da tela morasse aqui e lá, a voz diria uma coisa
#    e a folha mostraria outra — e é esse o defeito que o `falas.json` existe
#    para matar. Tudo o que se escreve aqui ou sai dos DADOS, ou é a narração
#    da folha (que não existe na tela).
#
# ⚠️ A DICA NUNCA ENTREGA A RESPOSTA. Ela diz ONDE OLHAR: *"conte quantas vezes
#    a boca abre"*, nunca *"são três"*. Quem mede é o portão `0j`.
# ---------------------------------------------------------------------------

NOMEGAV = {u"k1": u"monossílaba", u"k2": u"dissílaba",
           u"k3": u"trissílaba", u"k4": u"polissílaba"}
DIZGAV = {u"k1": u"uma sílaba", u"k2": u"duas sílabas",
          u"k3": u"três sílabas", u"k4": u"quatro sílabas ou mais"}
QUANTAS = {1: u"uma", 2: u"duas", 3: u"três", 4: u"quatro", 5: u"cinco"}


def classe(n):
    return NOMEGAV[u"k%d" % min(n, 4)]


# ---- o cartaz das quatro gavetas: o nome, a regra e a voz de cada uma -------
for _gk in (u"gA", u"gB", u"gC", u"gD", u"gE", u"gF"):
    for _k in NOMEGAV:
        p(u"gav_%s_%s" % (_gk, _k),
          u"%s: palavra de %s." % (NOMEGAV[_k].capitalize(), DIZGAV[_k]))
for _k in NOMEGAV:
    p(u"lapis_" + _k, u"Canetinha das palavras de %s." % DIZGAV[_k])

# ---- a voz de CADA PALAVRA do caderno --------------------------------------
# ⚠️⚠️ O ACENTO TEM DE SUMIR DO MESMO JEITO NOS DOIS LADOS. Quem grava usa
#    `ch()` (NFKD: ã vira a, ç vira c) e quem pede usa o `chaveQuadro` do app.
#    As duas são a MESMA regra escrita duas vezes — mexeu numa, mexe na outra,
#    e o portão `1p` reprova se desencontrarem. Foi assim que dezessete
#    palavras ficaram mudas no 2º ano, todas com til ou cedilha.
_PALAVRAS = {}


def _pal(w, silabas=None):
    w = w.strip()
    if not w:
        return
    _PALAVRAS[w] = 1
    p(u"pal_" + ch(w), w + u".")
    if silabas:
        _reg(w, silabas)


# 1, 2, 3 e 19 — bater palma e pintar a bolinha
BOL = bloco(u"BOL")
p(u"p1enun", u"Folha um. Diga a palavra em voz alta e bata palma cada vez que a "
             u"boca abrir. Depois pinte uma bolinha por palma e toque em Pronto.")
p(u"p2enun", u"Folha dois. O mesmo gesto, e agora as palavras são compridas. "
             u"Bata palma devagar: cada palma é uma bolinha.")
p(u"p3enun", u"Folha três. Agora sem figura nenhuma, só a palavra escrita. "
             u"Diga a palavra baixinho, bata palma e pinte as bolinhas.")
p(u"p19enun", u"Folha dezenove. Uma parada para respirar: o gesto da primeira "
              u"folha, com palavras novas. Bata palma e pinte uma bolinha por palma.")
for _k, _B in BOL.items():
    _pal(_B[u"p"], _B[u"s"])
    _n = len(_B[u"s"])
    _fo = 1 if _k[0] == u"a" else (2 if _k[0] == u"b" else (3 if _k[0] == u"c" else 19))
    p(u"certo%d_%s" % (_fo, _k),
      u"Isso! %s tem %s %s: %s." % (_B[u"p"], QUANTAS[_n],
                                    u"sílaba" if _n == 1 else u"sílabas",
                                    u", ".join(_B[u"s"])))
    p(u"dica%d_%s" % (_fo, _k),
      u"Diga a palavra devagar e bata palma. Cada vez que a boca abre é uma "
      u"bolinha — nem mais, nem menos.")

# 4, 5 e 6 — cortar a palavra onde ela se parte
COR = bloco(u"COR")
p(u"p4enun", u"Folha quatro. Toque na fresta onde a palavra se parte. Uma tesoura "
             u"aparece ali. Estas se partem uma vez só.")
p(u"p5enun", u"Folha cinco. Mesmo gesto, e agora a palavra se parte mais de uma "
             u"vez. Corte em todas as frestas até a palavra ficar toda em pedaços.")
p(u"p6enun", u"Folha seis. Agora repare no número. Cada palavra abaixo diz quantas "
             u"letras tem. Corte em sílabas e veja: são sempre menos.")
for _k, _C in COR.items():
    _pal(_C[u"p"])
    _fo = 4 if _k[0] == u"d" else (5 if _k[0] == u"e" else 6)
    _n = len(_C[u"g"]) + 1
    p(u"certo%d_%s" % (_fo, _k),
      u"Muito bem! %s se parte em %s pedaços." % (_C[u"p"], QUANTAS[_n]))
    p(u"dica%d_%s" % (_fo, _k),
      u"Diga a palavra devagar. O corte fica onde a sua voz faz uma pausa e recomeça.")

# 7 e 8 — os quatro nomes
LIGA = bloco(u"LIGA")
p(u"p7enun", u"Folha sete. Cada número de sílabas tem um nome. O cartaz está aí "
             u"embaixo: use-o. Toque na palavra e depois no nome dela.")
p(u"p8enun", u"Folha oito. Agora sem o cartaz. Conte as sílabas de cabeça e ligue "
             u"cada palavra ao nome dela.")
for _k, _L in LIGA.items():
    _pal(_L[u"p"])
    _fo = 7 if _k[0] == u"h" else 8
    p(u"lig_" + _k, _L[u"p"] + u".")
    p(u"ligc_" + _k, _L[u"c"] + u".")
    p(u"certo%d_%s" % (_fo, _k),
      u"Isso! %s tem %s, então é %s." % (_L[u"p"], DIZGAV[u"k%d" % _L[u"n"]],
                                         NOMEGAV[u"k%d" % _L[u"n"]]))
    p(u"dica%d_%s" % (_fo, _k),
      u"Conte as sílabas da palavra primeiro. Só depois procure o nome que "
      u"combina com esse número.")

# 9 a 14 — as gavetas (palavra escrita) e as gavetas com figura
GAV = bloco(u"GAV")
p(u"p9enun", u"Folha nove. Duas gavetas, bem diferentes uma da outra: de uma "
             u"sílaba e de quatro ou mais. Arraste cada palavra, ou toque nela e "
             u"depois na gaveta.")
p(u"p10enun", u"Folha dez. Agora as quatro gavetas abertas. Conte as sílabas da "
              u"palavra e guarde-a no lugar dela.")
p(u"p11enun", u"Folha onze. Quatro gavetas outra vez, e agora com as palavras da "
              u"escola, as que você vê todo dia.")
p(u"p12enun", u"Folha doze. Agora as palavras se parecem. Pano, panela e panelinha "
              u"começam igual: só contar as sílabas separa uma da outra.")
p(u"p13enun", u"Folha treze. Agora a peça é a figura, sem a palavra escrita. Diga "
              u"o nome do desenho, conte as sílabas e guarde na gaveta dela.")
p(u"p14enun", u"Folha catorze. As mesmas gavetas e agora doze figuras, inclusive "
              u"as compridas. Toque na figura para ouvir o nome dela.")
_FOGAV = {u"gA": 9, u"gB": 10, u"gC": 11, u"gD": 12, u"gE": 13, u"gF": 14}
for _gk, _G in GAV.items():
    _fo = _FOGAV[_gk]
    for _k, _P in _G[u"pal"].items():
        _pal(_P[u"p"])
        p(u"diz2_%s_%s" % (_gk, _k), _P[u"p"] + u".")
        p(u"certo%d_%s" % (_fo, _k),
          u"Isso! %s é %s." % (_P[u"p"], NOMEGAV[_P[u"c"]]))
        p(u"dica%d_%s" % (_fo, _k),
          u"Diga a palavra batendo palma e conte as palmas. O número das palmas "
          u"é o da gaveta.")

# 15 e 16 — montar a palavra
ORD = bloco(u"ORD")
p(u"p15enun", u"Folha quinze. As sílabas se embaralharam. Toque nelas na ordem "
              u"para a palavra voltar. Cada pedaço fala quando você toca nele.")
p(u"p16enun", u"Folha dezesseis. Agora são palavras de quatro pedaços. Diga a "
              u"palavra baixinho antes de começar: ajuda a achar o primeiro.")
for _k, _O in ORD.items():
    _pal(_O[u"p"], _O[u"s"])
    _fo = 15 if _k[0] == u"v" else 16
    p(u"ord_" + _k, _O[u"p"] + u".")
    p(u"certo%d_%s" % (_fo, _k),
      u"Muito bem! %s, com %s pedaços." % (_O[u"p"], QUANTAS[len(_O[u"s"])]))
    p(u"dica%d_%s" % (_fo, _k),
      u"Comece pelo pedaço com que a palavra COMEÇA. Ouça-a de novo e repare "
      u"no primeiro som.")

# 17 e 18 — o ditado
DIT = bloco(u"DIT")
p(u"p17enun", u"Folha dezessete. Um ditado: ouça a palavra e guarde-a na gaveta "
              u"certa. Depois que você escolher, a palavra aparece para conferir.")
p(u"p18enun", u"Folha dezoito. Mesmo ditado, e agora a palavra não aparece nunca. "
              u"Só o som. Conte as aberturas da boca enquanto ouve.")
for _k, _D in DIT.items():
    _pal(_D[u"p"])
    _fo = 17 if _k[0] == u"x" else 18
    p(u"dit_" + _k, _D[u"p"] + u".")
    p(u"certo%d_%s" % (_fo, _k),
      u"Isso! %s é %s." % (_D[u"p"], NOMEGAV[_D[u"c"]]))
    p(u"dica%d_%s" % (_fo, _k),
      u"Toque no alto-falante de novo e repita a palavra junto, batendo palma.")

# 20 e 21 — a cantiga
CANT = bloco(u"CANT")
p(u"p20enun", u"Folha vinte. Uma cantiga de roda. Pegue a canetinha da cor certa "
              u"e pinte quatro palavras dela, pela legenda.")
p(u"p21enun", u"Folha vinte e um. A mesma cantiga, e agora todas as palavras "
              u"destacadas, as nove. A legenda é a mesma.")
for _k, _Z in CANT[u"pal"].items():
    _pal(_Z[u"p"])
    for _fo in (20, 21):
        p(u"certo%d_%s" % (_fo, _k),
          u"Isso! %s é %s." % (_Z[u"p"], NOMEGAV[_Z[u"c"]]))
        p(u"dica%d_%s" % (_fo, _k),
          u"Essa canetinha não é a dessa palavra. Conte as sílabas dela e veja de "
          u"que cor é a gaveta do número que deu.")

# 22 — a trilha
TRI = bloco(u"TRI")
p(u"p22enun", u"Folha vinte e dois. Leve a borboleta até a flor. Em cada passo, "
              u"toque só na palavra de três sílabas.")
for _P in TRI[u"passos"]:
    for _o in _P[u"ops"]:
        _pal(_o[u"p"])
    p(u"certo22_" + _P[u"c"], u"Boa! A borboleta avançou um passo.")
    p(u"dica22_" + _P[u"c"],
      u"Bata palma em cada palavra do passo. Só uma delas tem três palmas.")

# 23 e 24 — achar no texto
TEX = bloco(u"TEX")
p(u"p23enun", u"Folha vinte e três. Leia o texto. Entre as palavras do quadro "
              u"abaixo, marque as de duas sílabas, quantas quiser, e só depois "
              u"toque em Conferir.")
p(u"p24enun", u"Folha vinte e quatro. Agora um texto maior. Entre as palavras do "
              u"quadro, marque as de quatro sílabas ou mais e confira.")
for _k, _T in TEX.items():
    p(u"tex_" + _k, _T[u"texto"])
    for _pc in _T[u"pecas"]:
        _pal(_pc[u"t"])
p(u"certo23_a", u"Isso! Tatu, saiu e toca têm duas sílabas cada uma.")
p(u"dica23_a", u"Confira uma por uma, batendo palma. Deixe marcada só a que der "
               u"duas palmas.")
p(u"certo24_a", u"Muito bem! Biblioteca, professora e borboleta são as compridas.")
p(u"dica24_a", u"Bata palma em cada palavra do quadro. Marque só as que passarem "
               u"de três palmas.")

# 25 a 28 — decidir sozinha
QUI = bloco(u"QUI")
p(u"p25enun", u"Folha vinte e cinco. Olhe a figura, diga o nome dela e escolha a "
              u"gaveta.")
p(u"p26enun", u"Folha vinte e seis. Agora ninguém arrasta nada: só a palavra "
              u"escrita e os quatro nomes. E ela cresce diante de você: pão, "
              u"pãozinho. Conte outra vez.")
p(u"p27enun", u"Folha vinte e sete. Cuidado com estas. Elas têm muitas letras e a "
              u"boca abre poucas vezes. Escolha, e depois veja por quê.")
p(u"p28enun", u"Folha vinte e oito. E agora o contrário. Estas parecem curtas e "
              u"têm mais pedaços do que se pensa. Diga-as devagar antes de escolher.")
_FOQUI = {u"A": 25, u"B": 26, u"C": 27, u"D": 28}
for _k, _Q in QUI.items():
    _pal(_Q[u"p"], _Q.get(u"s"))
    _fo = _FOQUI[_k[0]]
    p(u"certo%d_%s" % (_fo, _k),
      u"Isso! %s é %s." % (_Q[u"p"], NOMEGAV[_Q[u"r"]]))
    p(u"dica%d_%s" % (_fo, _k),
      u"Não conte as letras: conte as vezes que a boca abre. Diga a palavra bem "
      u"devagar.")

# 29 — o caça-palavras
CACA = bloco(u"CACA")
p(u"p29enun", u"Folha vinte e nove. Aqui cada casa é uma sílaba, não uma letra. "
              u"Ache as palavras compridas: toque na primeira casa e depois na "
              u"última.")
for _k, _C in CACA[u"pal"].items():
    _pal(_C[u"p"])
    p(u"certo29_" + _k, u"Achou! %s, toda numa linha." % _C[u"p"])
    p(u"dica29_" + _k, u"Procure a casa com o primeiro pedaço da palavra e siga "
                       u"a linha até o último.")

# 30 — a cruzadinha
CRZ = bloco(u"CRZ")
p(u"p30enun", u"Folha trinta. Uma cruzadinha em que a pista diz quantas sílabas "
              u"a palavra tem. Toque numa pista e escreva.")
for _k, _C in CRZ.items():
    _pal(_C[u"p"])
    p(u"crz_" + _k, _C[u"d"])
    p(u"certo30_" + _k, u"Isso! %s." % _C[u"p"])
    p(u"dica30_" + _k, u"Leia a pista de novo: ela diz quantas sílabas a palavra "
                       u"tem, e isso já elimina quase todas.")

# 31 — escreva o nome da figura
ESCR = bloco(u"ESCR")
p(u"p31enun", u"Folha trinta e um. Agora sem pista escrita: só a figura. Escreva "
              u"o nome dela, letra por letra. No computador dá para usar o teclado "
              u"de verdade.")
for _k, _E in ESCR.items():
    p(u"esc_" + _k, _E[u"d"])
    p(u"certo31_" + _k, u"Muito bem escrito!")
    p(u"dica31_" + _k, u"Diga o nome da figura em voz alta e escreva um pedaço de "
                       u"cada vez.")

# 32 — o desafio
DESAF = bloco(u"DESAF")
p(u"p32enun", u"Folha trinta e dois. O desafio: escreva você uma palavra de cada "
              u"tamanho. Se faltar ideia, o banco de palavras está embaixo de cada "
              u"linha.")
for _k, _D in DESAF.items():
    p(u"des_" + _k, u"Escreva " + _D[u"pede"] + u".")
    p(u"certo32_" + _k, u"Essa vale! Você escolheu e acertou o tamanho.")
    p(u"dica32_" + _k, u"Bata palma na palavra que você escreveu e conte. Se o "
                       u"número não bater, escolha outra do banco ali embaixo.")

# 33 — a memória
MEM = bloco(u"MEM")
p(u"p33enun", u"Folha trinta e três. Vire duas cartas e ache a figura e o nome da "
              u"gaveta dela. As figuras são as mesmas das folhas de papel.")
for _k, _M in MEM.items():
    _pal(_M[u"p"])
    p(u"memok_" + _k, u"Par! %s é %s." % (_M[u"p"], _M[u"c"].lower()))
p(u"memfim", u"Tabuleiro limpo! Você lembrou de todas.")
p(u"memdica", u"Guarde onde cada carta estava: elas voltam para baixo no mesmo lugar.")

# 34 — a forca
FORC = bloco(u"FORC")
p(u"p34enun", u"Folha trinta e quatro. Leia a pista, que diz quantas sílabas a "
              u"palavra tem, e adivinhe-a letra por letra. A cada erro a mira "
              u"fecha um pouco.")
for _k, _F in FORC.items():
    _pal(_F[u"p"])
    p(u"for_" + _k, _F[u"d"])
    p(u"foco_" + _k, u"Acertou! %s." % _F[u"p"])
    p(u"fopou_" + _k, u"A mira fechou. A palavra era %s: guarde-a." % _F[u"p"])
    p(u"fodica_" + _k, u"Essa letra não está aqui. Comece pelas vogais: toda "
                       u"sílaba tem pelo menos uma.")

# ---- as sílabas que o app fala SOZINHAS (folhas 15 e 16) -------------------
# ⚠️ O motor corta cada uma de dentro do mp3 da PALAVRA INTEIRA: a voz não lê
#    som, lê palavra — entregue "TA" a ela e sai "tê-á". Por isso o mapa.
_SOLTAS = []
for _k, _O in ORD.items():
    _SOLTAS.extend(_O[u"s"])
_ORFAS = _mapeia(_SOLTAS)

# 35 — o cartaz
CARTAZ = bloco(u"CARTAZ")
p(u"p35enun", u"Folha trinta e cinco. Este cartaz é seu: monte-o e leve na cabeça. "
              u"Em cada linha, escolha o exemplo que cabe naquele nome.")
for _k, _C in CARTAZ.items():
    _pal(_C[u"ex"])
    p(u"cartaz_" + _k, u"%s: palavra de %s. Por exemplo, %s."
                       % (_C[u"n"].capitalize(), _C[u"d"], _C[u"ex"]))
    p(u"certo35_" + _k, u"Isso! %s tem %s." % (_C[u"ex"], _C[u"d"]))
    p(u"dica35_" + _k, u"Leia a linha outra vez: ela diz quantas sílabas o exemplo "
                       u"precisa ter.")


# ---------------------------------------------------------------------------
def chave(s):
    u"""O nome do mp3 sai do TEXTO, não da chave da fala — assim duas chaves que
    dizem a mesma frase gravam um arquivo só."""
    s = re.sub(r"\s+", u" ", s or u"").strip().lower()
    hh = 5381
    for c in s:
        hh = ((hh * 33) ^ ord(c)) & 0xFFFFFFFF
    d, out = hh, u""
    if d == 0:
        return u"0"
    while d:
        out = u"0123456789abcdefghijklmnopqrstuvwxyz"[d % 36] + out
        d //= 36
    return out


falas, vistos = [], {}
for k in sorted(F.keys()):
    txt = F[k]
    if not txt:
        continue
    c = chave(txt)
    if c in vistos:
        continue
    vistos[c] = 1
    falas.append({u"id": PREFIXO + c, u"texto": txt, u"voz": VOZ})

html = io.open(CAM, encoding=u"utf-8").read()
blocoF = (u"/*FALAS-INI*/\nvar FALAS = "
          + json.dumps(F, ensure_ascii=False, indent=1, sort_keys=True) + u";\n/*FALAS-FIM*/")
blocoV = (u"/*VOZOK-INI*/var VOZOK = "
          + json.dumps(dict((c, 1) for c in vistos), ensure_ascii=False) + u";/*VOZOK-FIM*/")
novo = re.sub(r"/\*FALAS-INI\*/.*?/\*FALAS-FIM\*/", lambda m: blocoF, html, flags=re.S)
novo = re.sub(r"/\*VOZOK-INI\*/.*?/\*VOZOK-FIM\*/", lambda m: blocoV, novo, flags=re.S)

# ⭐ o `silabas.json` é o que o `entregar.yml` lê para cortar cada sílaba de
#    dentro do mp3 da palavra inteira, e o `SILMAP` é o que o app usa para saber
#    de qual palavra veio cada pedaço. Uma fonte só para os dois.
io.open(os.path.join(AQUI, u"silabas.json"), u"w", encoding=u"utf-8").write(
    json.dumps({u"prefixo": PREFIXO, u"voz": VOZ,
                u"palavras": dict((w, _SIL_DE[w]) for w in sorted(_SIL_DE))},
               ensure_ascii=False, indent=1))
blocoS = (u"/*SILMAP-INI*/var SILMAP = "
          + json.dumps(_MAPA_SIL, ensure_ascii=False, sort_keys=True) + u";/*SILMAP-FIM*/")
novo = re.sub(r"/\*SILMAP-INI\*/.*?/\*SILMAP-FIM\*/", lambda m: blocoS, novo, flags=re.S)
io.open(CAM, u"w", encoding=u"utf-8").write(novo)
io.open(os.path.join(AQUI, u"falas.json"), u"w", encoding=u"utf-8").write(
    json.dumps(falas, ensure_ascii=False, indent=1))
io.open(os.path.join(AQUI, u"voz.txt"), u"w", encoding=u"utf-8").write(VOZ + u"\n")
print(u"FALAS: %d chaves; falas.json: %d fala(s) para gravar; "
      u"silabas: %d palavra(s) para recortar, %d silaba(s) no mapa"
      % (len(F), len(falas), len(_SIL_DE), len(_MAPA_SIL)))
if _ORFAS:
    print(u"   \u26a0\ufe0f %d silaba(s) SEM palavra de origem (o app dira a palavra "
          u"inteira): %s" % (len(_ORFAS), u", ".join(_ORFAS)))
if _RECUSADAS:
    print(u"   \u26a0\ufe0f %d lista(s) recusada(s) por nao formarem a palavra: %s"
          % (len(_RECUSADAS), u", ".join(
              u"%s=%s" % (w, u"-".join(sl)) for w, sl in _RECUSADAS[:8])))
