import utils

HORIZONTE = 8


class PlanoMestre:
    ARQUIVO = "mps.json"

    def __init__(self, repositorio, cadastro_itens):
        self.repositorio = repositorio
        self.cadastro = cadastro_itens
        self.plano = {}
        self.carregar()

    def carregar(self):
        self.plano = self.repositorio.carregar_json(self.ARQUIVO)

    def salvar(self):
        self.repositorio.salvar_json(self.ARQUIVO, self.plano)

    def possui_demanda(self, codigo):
        return codigo in self.plano

    def produtos(self):
        return sorted(self.plano)

    def demanda(self, codigo):
        return list(self.plano.get(codigo, [0] * HORIZONTE))

    def definir_plano(self, codigo, demandas):
        item = self.cadastro.obter(codigo)
        if item.tipo != "PA":
            raise ValueError(
                f"{codigo} nao e produto acabado; o MPS aceita apenas PA"
            )
        if len(demandas) != HORIZONTE:
            raise ValueError(f"informe a demanda das {HORIZONTE} semanas")
        if any(quantidade < 0 for quantidade in demandas):
            raise ValueError("a demanda nao pode ser negativa")
        self.plano[codigo] = [int(quantidade) for quantidade in demandas]
        self.salvar()

    def remover(self, codigo):
        if codigo not in self.plano:
            raise ValueError(f"{codigo} nao esta no plano mestre")
        del self.plano[codigo]
        self.salvar()

    def exibir(self):
        if not self.plano:
            print("Nenhum produto no plano mestre.")
            return
        print(f"PLANO MESTRE DE PRODUCAO - horizonte de {HORIZONTE} semanas")
        semanas = "".join(f"{'S' + str(s):>6}" for s in range(1, HORIZONTE + 1))
        print(f"{'Item':<8}{'Descricao':<26}{semanas}{'Total':>7}")
        print("-" * (8 + 26 + 6 * HORIZONTE + 7))
        for codigo in self.produtos():
            item = self.cadastro.obter(codigo)
            demandas = self.plano[codigo]
            colunas = "".join(f"{quantidade:>6}" for quantidade in demandas)
            print(f"{codigo:<8}{item.descricao[:24]:<26}{colunas}"
                  f"{sum(demandas):>7}")

    def definir_interativo(self):
        print(">> Plano mestre (Enter mantem a demanda atual)")
        codigo = utils.ler_codigo(
            ">> Codigo do produto acabado: ", tipos=("PA",)
        )
        if not self.cadastro.existe(codigo):
            print(f"ERRO: o item {codigo} nao esta cadastrado.")
            return
        atuais = self.demanda(codigo)
        novas = []
        for semana in range(1, HORIZONTE + 1):
            atual = atuais[semana - 1]
            novas.append(utils.ler_inteiro(
                f">> Demanda da semana {semana} [{atual}]: ",
                minimo=0, padrao=atual,
            ))
        try:
            self.definir_plano(codigo, novas)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Plano de {codigo} salvo.")

    def remover_interativo(self):
        print(">> Remocao de produto do plano mestre")
        codigo = utils.ler_codigo(">> Codigo do produto: ", tipos=("PA",))
        try:
            self.remover(codigo)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"{codigo} removido do plano mestre.")