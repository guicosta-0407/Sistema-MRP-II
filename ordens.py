import re

import utils
from estoque import normalizar_numero
from mps import HORIZONTE

PLANEJADA = "PLANEJADA"
FIRME = "FIRME"
LIBERADA = "LIBERADA"
ENCERRADA = "ENCERRADA"
PADRAO_ORDEM = re.compile(r"^(OP|OC)-(\d+)$")


def normalizar_numero_ordem(texto):
    achado = PADRAO_ORDEM.match(texto.strip().upper())
    if not achado:
        raise ValueError("numero invalido, use OP-0001 ou OC-0001")
    return f"{achado.group(1)}-{int(achado.group(2)):04d}"


class Ordem:
    def __init__(self, numero, item, quantidade, semana_liberacao,
                 semana_entrega, status=PLANEJADA, atrasada=False):
        self.numero = numero
        self.tipo = numero.split("-")[0]
        self.item = item
        self.quantidade = quantidade
        self.semana_liberacao = semana_liberacao
        self.semana_entrega = semana_entrega
        self.status = status
        self.atrasada = atrasada

    @property
    def aberta(self):
        return self.status != ENCERRADA

    @property
    def status_exibicao(self):
        if self.atrasada and self.status == PLANEJADA:
            return "ATRASADA"
        return self.status

    def to_dict(self):
        return {
            "item": self.item,
            "quantidade": self.quantidade,
            "semana_liberacao": self.semana_liberacao,
            "semana_entrega": self.semana_entrega,
            "status": self.status,
            "atrasada": self.atrasada,
        }

    @classmethod
    def from_dict(cls, numero, dados):
        return cls(
            numero,
            dados["item"],
            dados["quantidade"],
            dados["semana_liberacao"],
            dados["semana_entrega"],
            dados["status"],
            dados["atrasada"],
        )


class GerenciadorOrdens:
    ARQUIVO = "ordens.json"

    def __init__(self, repositorio, cadastro_itens, estrutura, estoque):
        self.repositorio = repositorio
        self.cadastro = cadastro_itens
        self.estrutura = estrutura
        self.estoque = estoque
        self.ordens = {}
        self.numeracao_inicial = {"OP": 1, "OC": 1}
        self.ultima_execucao = None
        self.carregar()

    def carregar(self):
        dados = self.repositorio.carregar_json(self.ARQUIVO)
        self.numeracao_inicial.update(dados.get("numeracao_inicial", {}))
        self.ultima_execucao = dados.get("ultima_execucao")
        self.ordens = {
            numero: Ordem.from_dict(numero, campos)
            for numero, campos in dados.get("ordens", {}).items()
        }

    def salvar(self):
        dados = {
            "numeracao_inicial": self.numeracao_inicial,
            "ultima_execucao": self.ultima_execucao,
            "ordens": {n: o.to_dict() for n, o in self.ordens.items()},
        }
        self.repositorio.salvar_json(self.ARQUIVO, dados)

    def obter(self, numero):
        if numero not in self.ordens:
            raise ValueError(f"ordem {numero} nao encontrada")
        return self.ordens[numero]

    def listar(self, abertas=True):
        ordens = [o for o in self.ordens.values() if o.aberta == abertas]
        return sorted(ordens, key=lambda o: (o.tipo != "OP", o.numero))

    def possui_ordem(self, codigo):
        return any(o.item == codigo for o in self.ordens.values())

    def atrasadas(self):
        return [
            o for o in self.listar()
            if o.atrasada and o.status in (PLANEJADA, FIRME)
        ]

    def proximo_numero(self, tipo):
        usados = [
            int(numero.split("-")[1])
            for numero, ordem in self.ordens.items() if ordem.tipo == tipo
        ]
        ultimo = max([self.numeracao_inicial.get(tipo, 1) - 1] + usados)
        return f"{tipo}-{ultimo + 1:04d}"

    def apagar_planejadas(self):
        self.ordens = {
            n: o for n, o in self.ordens.items() if o.status != PLANEJADA
        }

    def adicionar_planejada(self, item, quantidade, semana_liberacao,
                            semana_entrega):
        tipo = "OP" if item.fabricado else "OC"
        numero = self.proximo_numero(tipo)
        ordem = Ordem(numero, item.codigo, quantidade, semana_liberacao,
                      semana_entrega, PLANEJADA, semana_liberacao < 1)
        self.ordens[numero] = ordem
        return ordem

    def recebimentos_programados(self, codigo):
        recebimentos = [0] * HORIZONTE
        for ordem in self.ordens.values():
            if ordem.item == codigo and ordem.status in (FIRME, LIBERADA):
                semana = max(ordem.semana_entrega, 1)
                if semana <= HORIZONTE:
                    recebimentos[semana - 1] += ordem.quantidade
        return [normalizar_numero(q) for q in recebimentos]

    def liberacoes_firmes(self, codigo):
        liberacoes = [0] * HORIZONTE
        for ordem in self.ordens.values():
            if ordem.item == codigo and ordem.status in (FIRME, LIBERADA):
                semana = max(ordem.semana_liberacao, 1)
                if semana <= HORIZONTE:
                    liberacoes[semana - 1] += ordem.quantidade
        return [normalizar_numero(q) for q in liberacoes]

    def _avancar(self, numero, de, para, rotulo):
        ordem = self.obter(numero)
        if ordem.status != de:
            raise ValueError(
                f"{numero} esta {ordem.status}; so ordens {de}S "
                f"podem ser {rotulo}"
            )
        ordem.status = para
        self.salvar()
        return ordem

    def firmar(self, numero):
        return self._avancar(numero, PLANEJADA, FIRME, "firmadas")

    def liberar(self, numero):
        return self._avancar(numero, FIRME, LIBERADA, "liberadas")

    def _exigir_liberada(self, numero, tipo, orientacao):
        ordem = self.obter(numero)
        if ordem.tipo != tipo:
            raise ValueError(f"{numero} nao e ordem do tipo {tipo}; {orientacao}")
        if ordem.status != LIBERADA:
            raise ValueError(
                f"{numero} esta {ordem.status}; so ordens LIBERADAS "
                "podem ser encerradas"
            )
        return ordem

    def apontar(self, numero):
        ordem = self._exigir_liberada(
            numero, "OP", "use o recebimento para ordens de compra"
        )
        consumos = [
            (r["componente"], normalizar_numero(r["quantidade"] * ordem.quantidade))
            for r in self.estrutura.componentes(ordem.item)
        ]
        if not consumos:
            raise ValueError(
                f"{ordem.item} nao possui estrutura cadastrada; "
                "cadastre a BOM antes de apontar"
            )
        faltas = []
        for codigo, necessario in consumos:
            saldo = self.estoque.saldo(codigo)
            if saldo < necessario:
                unidade = self.cadastro.obter(codigo).unidade
                faltas.append(
                    f"{codigo} (necessario {utils.formatar_quantidade(necessario)}"
                    f", saldo {utils.formatar_quantidade(saldo)} {unidade})"
                )
        if faltas:
            raise ValueError(
                "apontamento rejeitado, faltam componentes: " + "; ".join(faltas)
            )
        documento = f"{numero} ({ordem.item})"
        for codigo, necessario in consumos:
            self.estoque.registrar(codigo, "SAIDA", necessario, documento)
        self.estoque.registrar(
            ordem.item, "ENTRADA", ordem.quantidade, f"{numero} - producao"
        )
        ordem.status = ENCERRADA
        self.salvar()
        return ordem

    def receber(self, numero):
        ordem = self._exigir_liberada(
            numero, "OC", "use o apontamento para ordens de producao"
        )
        self.estoque.registrar(
            ordem.item, "ENTRADA", ordem.quantidade, f"{numero} - recebimento"
        )
        ordem.status = ENCERRADA
        self.salvar()
        return ordem

    @staticmethod
    def _semana(valor):
        return f"S{valor}"

    def _exibir_tabela(self, ordens):
        print(f"{'Ordem':<9}{'Tipo':<6}{'Item':<8}{'Qtde':>8}  "
              f"{'Liberar':<9}{'Entregar':<10}Status")
        print("-" * 64)
        for o in ordens:
            quantidade = utils.formatar_quantidade(o.quantidade)
            print(f"{o.numero:<9}{o.tipo:<6}{o.item:<8}{quantidade:>8}  "
                  f"{self._semana(o.semana_liberacao):<9}"
                  f"{self._semana(o.semana_entrega):<10}{o.status_exibicao}")

    def exibir_abertas(self):
        execucao = self.ultima_execucao or "nunca executado"
        print(f"ORDENS EM ABERTO - execucao do MRP em {execucao}")
        ordens = self.listar()
        if not ordens:
            print("Nenhuma ordem em aberto.")
            return
        self._exibir_tabela(ordens)
        atrasadas = len(self.atrasadas())
        if atrasadas:
            print(f"{atrasadas} mensagens de excecao: "
                  "ordens com liberacao antes da semana 1.")

    def exibir_encerradas(self):
        print("ORDENS ENCERRADAS")
        ordens = self.listar(abertas=False)
        if not ordens:
            print("Nenhuma ordem encerrada.")
            return
        self._exibir_tabela(ordens)

    @staticmethod
    def _ler_numero():
        while True:
            texto = input(">> Numero da ordem (Enter cancela): ")
            if not texto.strip():
                return None
            try:
                return normalizar_numero_ordem(texto)
            except ValueError as erro:
                print(f"ERRO: {erro}.")

    def gerenciar_interativo(self):
        acoes = {
            "F": (self.firmar, "firmada"),
            "L": (self.liberar, "liberada"),
            "A": (self.apontar, "apontada e encerrada"),
            "R": (self.receber, "recebida e encerrada"),
        }
        while True:
            self.exibir_abertas()
            opcao = utils.ler_opcao(
                "[F] Firmar [L] Liberar [A] Apontar producao "
                "[R] Receber compra [V] Voltar: ",
                [*acoes, "V"],
            )
            if opcao == "V":
                return
            numero = self._ler_numero()
            if numero is None:
                print("Operacao cancelada.")
                continue
            funcao, resultado = acoes[opcao]
            try:
                funcao(numero)
            except ValueError as erro:
                print(f"ERRO: {erro}.")
                continue
            print(f"Ordem {numero} {resultado}.")