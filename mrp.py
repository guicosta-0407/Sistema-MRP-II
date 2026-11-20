import utils
from estoque import normalizar_numero
from mps import HORIZONTE
from ordens import PLANEJADA


class RegistroMRP:
    def __init__(self, codigo):
        self.codigo = codigo
        self.necessidade_bruta = [0] * HORIZONTE
        self.recebimentos_programados = [0] * HORIZONTE
        self.estoque_projetado = [0] * HORIZONTE
        self.necessidade_liquida = [0] * HORIZONTE
        self.recebimentos_planejados = [0] * HORIZONTE
        self.liberacoes_planejadas = [0] * HORIZONTE
        self.liberacoes_firmes = [0] * HORIZONTE


class CalculoMRP:
    ORDEM_DE_PROCESSAMENTO = ("PA", "SA", "MP")

    def __init__(self, cadastro_itens, estrutura, estoque, mps, ordens):
        self.cadastro = cadastro_itens
        self.estrutura = estrutura
        self.estoque = estoque
        self.mps = mps
        self.ordens = ordens
        self.registros = {}

    def executar(self):
        self.registros = {}
        self.ordens.apagar_planejadas()
        for tipo in self.ORDEM_DE_PROCESSAMENTO:
            for item in self.cadastro.listar(tipo):
                registro = self._calcular(item)
                self._gerar_ordens(item, registro)
                self.registros[item.codigo] = registro
        self.ordens.ultima_execucao = utils.data_hoje()
        self.ordens.salvar()

    def _necessidade_bruta(self, item):
        if item.tipo == "PA":
            return [normalizar_numero(q) for q in self.mps.demanda(item.codigo)]
        bruta = [0] * HORIZONTE
        for pai in self.estrutura.pais_de(item.codigo):
            registro_pai = self.registros[pai]
            por_unidade = next(
                r["quantidade"] for r in self.estrutura.componentes(pai)
                if r["componente"] == item.codigo
            )
            for indice in range(HORIZONTE):
                liberado = (registro_pai.liberacoes_planejadas[indice]
                            + registro_pai.liberacoes_firmes[indice])
                bruta[indice] += liberado * por_unidade
        return [normalizar_numero(q) for q in bruta]

    def _calcular(self, item):
        registro = RegistroMRP(item.codigo)
        registro.necessidade_bruta = self._necessidade_bruta(item)
        registro.recebimentos_programados = (
            self.ordens.recebimentos_programados(item.codigo)
        )
        registro.liberacoes_firmes = self.ordens.liberacoes_firmes(item.codigo)
        projetado = self.estoque.saldo(item.codigo)
        for indice in range(HORIZONTE):
            bruta = registro.necessidade_bruta[indice]
            programado = registro.recebimentos_programados[indice]
            liquida = normalizar_numero(max(
                0,
                bruta + item.estoque_seguranca - (projetado + programado),
            ))
            planejado = max(liquida, item.lote_minimo) if liquida > 0 else 0
            projetado = normalizar_numero(
                projetado + programado + planejado - bruta
            )
            registro.necessidade_liquida[indice] = liquida
            registro.recebimentos_planejados[indice] = normalizar_numero(planejado)
            registro.estoque_projetado[indice] = projetado
        return registro

    def _gerar_ordens(self, item, registro):
        for indice, quantidade in enumerate(registro.recebimentos_planejados):
            if quantidade <= 0:
                continue
            semana_entrega = indice + 1
            semana_liberacao = semana_entrega - item.lead_time
            self.ordens.adicionar_planejada(
                item, quantidade, semana_liberacao, semana_entrega
            )
            posicao = max(semana_liberacao, 1) - 1
            registro.liberacoes_planejadas[posicao] = normalizar_numero(
                registro.liberacoes_planejadas[posicao] + quantidade
            )

    def exibir_registro(self, codigo):
        item = self.cadastro.obter(codigo)
        registro = self.registros.get(codigo)
        if registro is None:
            raise ValueError("execute o MRP antes de consultar um registro")
        saldo = utils.formatar_quantidade(self.estoque.saldo(codigo))
        print(f"REGISTRO MRP - {item.codigo} {item.descricao}")
        print(f"Lead time: {item.lead_time} sem | "
              f"Est. seguranca: {utils.formatar_quantidade(item.estoque_seguranca)}"
              f" | Lote min.: {utils.formatar_quantidade(item.lote_minimo)}"
              f" | Estoque: {saldo}")
        print(f"{'Semana':<22}"
              + "".join(f"{semana:>7}" for semana in range(1, HORIZONTE + 1)))
        linhas = [
            ("Necessidade bruta", registro.necessidade_bruta),
            ("Receb. programados", registro.recebimentos_programados),
            ("Estoque projetado", registro.estoque_projetado),
            ("Necessidade liquida", registro.necessidade_liquida),
            ("Receb. planejados", registro.recebimentos_planejados),
            ("Liberacao planejada", registro.liberacoes_planejadas),
        ]
        if any(registro.liberacoes_firmes):
            linhas.append(("Liberacao ord. firmes", registro.liberacoes_firmes))
        for rotulo, valores in linhas:
            print(f"{rotulo:<22}"
                  + "".join(f"{utils.formatar_quantidade(v):>7}" for v in valores))
        for ordem in self.ordens.atrasadas():
            if ordem.item == codigo:
                print(f"ATENCAO: {ordem.numero} deveria ser liberada na semana "
                      f"{ordem.semana_liberacao} (antes da semana 1).")

    def exibir_excecoes(self):
        atrasadas = self.ordens.atrasadas()
        if not atrasadas:
            print("Nenhuma mensagem de excecao.")
            return
        print(f"{len(atrasadas)} mensagens de excecao: "
              "ordens com liberacao antes da semana 1.")
        for o in atrasadas:
            print(f"  - {o.numero} ({o.item}): liberar na semana "
                  f"{o.semana_liberacao}, entrega na semana {o.semana_entrega}")

    def executar_interativo(self):
        self.executar()
        planejadas = [o for o in self.ordens.listar() if o.status == PLANEJADA]
        producao = sum(1 for o in planejadas if o.tipo == "OP")
        print(f"MRP executado em {self.ordens.ultima_execucao}.")
        print(f"Ordens planejadas: {len(planejadas)} "
              f"({producao} OP e {len(planejadas) - producao} OC).")
        self.exibir_excecoes()

    def exibir_registro_interativo(self):
        codigo = utils.ler_codigo(">> Codigo do item: ")
        try:
            self.exibir_registro(codigo)
        except ValueError as erro:
            print(f"ERRO: {erro}.")