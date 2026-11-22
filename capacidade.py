import utils
from mps import HORIZONTE


class CentroTrabalho:
    def __init__(self, codigo, descricao, capacidade, custo_hora):
        self.codigo = codigo
        self.descricao = descricao
        self.capacidade = capacidade
        self.custo_hora = custo_hora

    def to_dict(self):
        return {
            "descricao": self.descricao,
            "capacidade": self.capacidade,
            "custo_hora": self.custo_hora,
        }

    @classmethod
    def from_dict(cls, codigo, dados):
        return cls(
            codigo,
            dados["descricao"],
            dados["capacidade"],
            dados["custo_hora"],
        )


class Capacidade:
    ARQUIVO_CENTROS = "centros.json"
    ARQUIVO_ROTEIROS = "roteiros.json"
    CAMPOS_ALTERAVEIS = {"descricao", "capacidade", "custo_hora"}

    def __init__(self, repositorio, cadastro_itens):
        self.repositorio = repositorio
        self.cadastro = cadastro_itens
        self.centros = {}
        self.roteiros = {}
        self.carregar()

    def carregar(self):
        dados = self.repositorio.carregar_json(self.ARQUIVO_CENTROS)
        self.centros = {
            codigo: CentroTrabalho.from_dict(codigo, campos)
            for codigo, campos in dados.items()
        }
        self.roteiros = self.repositorio.carregar_json(self.ARQUIVO_ROTEIROS)

    def salvar_centros(self):
        dados = {c: centro.to_dict() for c, centro in self.centros.items()}
        self.repositorio.salvar_json(self.ARQUIVO_CENTROS, dados)

    def salvar_roteiros(self):
        self.repositorio.salvar_json(self.ARQUIVO_ROTEIROS, self.roteiros)

    def existe_centro(self, codigo):
        return codigo in self.centros

    def obter_centro(self, codigo):
        if codigo not in self.centros:
            raise ValueError(f"centro {codigo} nao cadastrado")
        return self.centros[codigo]

    def listar_centros(self):
        return sorted(self.centros.values(), key=lambda c: c.codigo)

    @staticmethod
    def _validar_centro(centro):
        if not centro.descricao.strip():
            raise ValueError("a descricao nao pode ficar vazia")
        if centro.capacidade <= 0:
            raise ValueError("a capacidade deve ser maior que zero")
        if centro.custo_hora < 0:
            raise ValueError("o custo-hora nao pode ser negativo")

    def adicionar_centro(self, centro):
        if not utils.codigo_centro_valido(centro.codigo):
            raise ValueError("codigo invalido, use CT-Numero (ex.: CT-01)")
        if self.existe_centro(centro.codigo):
            raise ValueError(f"o centro {centro.codigo} ja esta cadastrado")
        self._validar_centro(centro)
        self.centros[centro.codigo] = centro
        self.salvar_centros()

    def alterar_centro(self, codigo, **campos):
        centro = self.obter_centro(codigo)
        invalidos = set(campos) - self.CAMPOS_ALTERAVEIS
        if invalidos:
            raise ValueError(
                f"campos nao alteraveis: {', '.join(sorted(invalidos))}"
            )
        copia = CentroTrabalho.from_dict(
            codigo, {**centro.to_dict(), **campos}
        )
        self._validar_centro(copia)
        self.centros[codigo] = copia
        self.salvar_centros()

    def itens_do_centro(self, codigo):
        return sorted(
            item for item, roteiro in self.roteiros.items()
            if roteiro["centro"] == codigo
        )

    def remover_centro(self, codigo):
        self.obter_centro(codigo)
        usados = self.itens_do_centro(codigo)
        if usados:
            raise ValueError(
                f"o centro {codigo} e usado no roteiro de: "
                f"{', '.join(usados)}"
            )
        del self.centros[codigo]
        self.salvar_centros()

    def roteiro(self, codigo_item):
        return self.roteiros.get(codigo_item)

    def definir_roteiro(self, codigo_item, codigo_centro, tempo):
        item = self.cadastro.obter(codigo_item)
        if not item.fabricado:
            raise ValueError(
                f"{codigo_item} e materia-prima e nao tem roteiro "
                "de fabricacao"
            )
        self.obter_centro(codigo_centro)
        if tempo <= 0:
            raise ValueError("o tempo por unidade deve ser maior que zero")
        self.roteiros[codigo_item] = {"centro": codigo_centro, "tempo": tempo}
        self.salvar_roteiros()

    def remover_roteiro(self, codigo_item):
        if codigo_item not in self.roteiros:
            raise ValueError(f"{codigo_item} nao possui roteiro")
        del self.roteiros[codigo_item]
        self.salvar_roteiros()

    def exibir_centros(self):
        if not self.centros:
            print("Nenhum centro de trabalho cadastrado.")
            return
        print(f"{'Codigo':<8}{'Descricao':<34}"
              f"{'Cap. (h/sem)':>13}{'Custo-hora':>12}")
        print("-" * 67)
        for centro in self.listar_centros():
            capacidade = utils.formatar_decimal(centro.capacidade)
            print(f"{centro.codigo:<8}{centro.descricao[:32]:<34}"
                  f"{capacidade:>13}"
                  f"{utils.formatar_moeda(centro.custo_hora):>12}")

    def exibir_roteiros(self):
        if not self.roteiros:
            print("Nenhum roteiro cadastrado.")
            return
        print(f"{'Item':<8}{'Descricao':<30}{'Centro':<8}"
              f"{'Tempo (h/un)':>13}")
        print("-" * 59)
        for codigo in sorted(self.roteiros):
            roteiro = self.roteiros[codigo]
            item = self.cadastro.obter(codigo)
            tempo = utils.formatar_quantidade(roteiro["tempo"])
            print(f"{codigo:<8}{item.descricao[:28]:<30}"
                  f"{roteiro['centro']:<8}{tempo:>13}")

    def cadastrar_centro_interativo(self):
        print(">> Cadastro de centro de trabalho")
        codigo = utils.ler_codigo_centro(">> Codigo (ex.: CT-01): ")
        if self.existe_centro(codigo):
            print(f"ERRO: o centro {codigo} ja esta cadastrado.")
            return
        descricao = utils.ler_texto(">> Descricao: ")
        capacidade = utils.ler_decimal(
            ">> Capacidade (horas/semana): ", minimo=0
        )
        custo_hora = utils.ler_decimal(">> Custo-hora (R$): ", minimo=0)
        centro = CentroTrabalho(codigo, descricao, capacidade, custo_hora)
        try:
            self.adicionar_centro(centro)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Centro {codigo} cadastrado com sucesso.")

    def alterar_centro_interativo(self):
        print(">> Alteracao de centro (Enter mantem o valor atual)")
        codigo = utils.ler_codigo_centro(">> Codigo do centro: ")
        if not self.existe_centro(codigo):
            print(f"ERRO: o centro {codigo} nao esta cadastrado.")
            return
        centro = self.obter_centro(codigo)
        atual = utils.formatar_decimal(centro.capacidade)
        campos = {
            "descricao": utils.ler_texto(
                f">> Descricao [{centro.descricao}]: ", obrigatorio=False
            ) or centro.descricao,
            "capacidade": utils.ler_decimal(
                f">> Capacidade [{atual}]: ",
                minimo=0, padrao=centro.capacidade,
            ),
            "custo_hora": utils.ler_decimal(
                f">> Custo-hora [{utils.formatar_moeda(centro.custo_hora)}]: ",
                minimo=0, padrao=centro.custo_hora,
            ),
        }
        try:
            self.alterar_centro(codigo, **campos)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Centro {codigo} alterado com sucesso.")

    def remover_centro_interativo(self):
        print(">> Remocao de centro de trabalho")
        codigo = utils.ler_codigo_centro(">> Codigo do centro: ")
        if not self.existe_centro(codigo):
            print(f"ERRO: o centro {codigo} nao esta cadastrado.")
            return
        confirmacao = utils.ler_opcao(
            f">> Remover {codigo}? [S/N]: ", ["S", "N"]
        )
        if confirmacao == "N":
            print("Operacao cancelada.")
            return
        try:
            self.remover_centro(codigo)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Centro {codigo} removido.")

    def definir_roteiro_interativo(self):
        print(">> Roteiro de fabricacao (operacao unica)")
        codigo = utils.ler_codigo(
            ">> Codigo do item fabricado (PA ou SA): ", tipos=("PA", "SA")
        )
        if not self.cadastro.existe(codigo):
            print(f"ERRO: o item {codigo} nao esta cadastrado.")
            return
        atual = self.roteiro(codigo)
        if atual:
            tempo_atual = utils.formatar_quantidade(atual["tempo"])
            print(f"Roteiro atual: {atual['centro']}, {tempo_atual} h/un.")
        self.exibir_centros()
        centro = utils.ler_codigo_centro(">> Codigo do centro de trabalho: ")
        tempo = utils.ler_decimal(">> Tempo por unidade (horas): ", minimo=0)
        try:
            self.definir_roteiro(codigo, centro, tempo)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Roteiro de {codigo} definido.")

    def remover_roteiro_interativo(self):
        print(">> Remocao de roteiro")
        codigo = utils.ler_codigo(">> Codigo do item: ", tipos=("PA", "SA"))
        try:
            self.remover_roteiro(codigo)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Roteiro de {codigo} removido.")


class CalculoCRP:
    def __init__(self, capacidade, ordens):
        self.capacidade = capacidade
        self.ordens = ordens

    def carga_semanal(self, codigo_centro):
        self.capacidade.obter_centro(codigo_centro)
        carga = [0.0] * HORIZONTE
        for ordem in self.ordens.listar():
            if ordem.tipo != "OP":
                continue
            roteiro = self.capacidade.roteiro(ordem.item)
            if roteiro is None or roteiro["centro"] != codigo_centro:
                continue
            semana = max(ordem.semana_liberacao, 1)
            if semana <= HORIZONTE:
                carga[semana - 1] += ordem.quantidade * roteiro["tempo"]
        return [round(horas, 4) for horas in carga]

    def uso_percentual(self, codigo_centro):
        centro = self.capacidade.obter_centro(codigo_centro)
        return [
            horas / centro.capacidade * 100
            for horas in self.carga_semanal(codigo_centro)
        ]

    def semanas_sobrecarga(self, codigo_centro):
        centro = self.capacidade.obter_centro(codigo_centro)
        return [
            semana
            for semana, horas in enumerate(
                self.carga_semanal(codigo_centro), start=1
            )
            if horas > centro.capacidade
        ]

    @staticmethod
    def _lista_de_semanas(semanas):
        textos = [str(semana) for semana in semanas]
        if len(textos) == 1:
            return f"na semana {textos[0]}"
        return f"nas semanas {', '.join(textos[:-1])} e {textos[-1]}"

    def exibir_carga(self, codigo_centro):
        centro = self.capacidade.obter_centro(codigo_centro)
        carga = self.carga_semanal(codigo_centro)
        usos = self.uso_percentual(codigo_centro)
        capacidade = utils.formatar_decimal(centro.capacidade)
        print(f"CARGA x CAPACIDADE - {centro.codigo} {centro.descricao} "
              f"({capacidade} h/semana)")
        print(f"{'Sem':>3}{'Carga(h)':>10}{'Uso(%)':>8}")
        sobrecarga = self.semanas_sobrecarga(codigo_centro)
        for semana, (horas, uso) in enumerate(zip(carga, usos), start=1):
            barra = "#" * round(uso / 10)
            aviso = " SOBRECARGA" if semana in sobrecarga else ""
            print(f"{semana:>3}{utils.formatar_decimal(horas):>10}"
                  f"{round(uso):>8}  {barra}{aviso}")
        if sobrecarga:
            print("Sugestao: antecipar OPs ou programar hora extra "
                  f"{self._lista_de_semanas(sobrecarga)}.")
        else:
            print("Nenhuma semana com sobrecarga.")

    def exibir_resumo(self):
        centros = self.capacidade.listar_centros()
        if not centros:
            print("Nenhum centro de trabalho cadastrado.")
            return
        print("CARGA x CAPACIDADE - uso (%) por semana; * = sobrecarga")
        semanas = "".join(
            f"{'S' + str(s):>7}" for s in range(1, HORIZONTE + 1)
        )
        print(f"{'Centro':<8}{'Cap.(h)':>8}{semanas}")
        print("-" * (16 + 7 * HORIZONTE))
        for centro in centros:
            sobrecarga = self.semanas_sobrecarga(centro.codigo)
            celulas = ""
            for semana, uso in enumerate(
                self.uso_percentual(centro.codigo), start=1
            ):
                marca = "*" if semana in sobrecarga else ""
                celulas += f"{str(round(uso)) + '%' + marca:>7}"
            capacidade = utils.formatar_decimal(centro.capacidade)
            print(f"{centro.codigo:<8}{capacidade:>8}{celulas}")

    def exibir_interativo(self):
        self.capacidade.exibir_centros()
        codigo = utils.ler_codigo_centro(">> Codigo do centro: ")
        try:
            self.exibir_carga(codigo)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
