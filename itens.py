import utils


class Item:
    def __init__(self, codigo, descricao, unidade, custo=0.0,
                 lead_time=0, estoque_seguranca=0, lote_minimo=1):
        self.codigo = codigo
        self.descricao = descricao
        self.tipo = utils.tipo_do_codigo(codigo)
        self.unidade = unidade
        self.custo = custo
        self.lead_time = lead_time
        self.estoque_seguranca = estoque_seguranca
        self.lote_minimo = lote_minimo

    @property
    def fabricado(self):
        return self.tipo in ("PA", "SA")

    def to_dict(self):
        return {
            "descricao": self.descricao,
            "tipo": self.tipo,
            "unidade": self.unidade,
            "custo": self.custo,
            "lead_time": self.lead_time,
            "estoque_seguranca": self.estoque_seguranca,
            "lote_minimo": self.lote_minimo,
        }

    @classmethod
    def from_dict(cls, codigo, dados):
        return cls(
            codigo,
            dados["descricao"],
            dados["unidade"],
            dados["custo"],
            dados["lead_time"],
            dados["estoque_seguranca"],
            dados["lote_minimo"],
        )


class CadastroItens:
    ARQUIVO = "itens.json"
    CAMPOS_ALTERAVEIS = {
        "descricao", "unidade", "custo",
        "lead_time", "estoque_seguranca", "lote_minimo",
    }

    def __init__(self, repositorio):
        self.repositorio = repositorio
        self.itens = {}
        self.carregar()

    def carregar(self):
        dados = self.repositorio.carregar_json(self.ARQUIVO)
        self.itens = {
            codigo: Item.from_dict(codigo, campos)
            for codigo, campos in dados.items()
        }

    def salvar(self):
        dados = {codigo: item.to_dict() for codigo, item in self.itens.items()}
        self.repositorio.salvar_json(self.ARQUIVO, dados)

    def remover(self, codigo):
        self.obter(codigo)
        del self.itens[codigo]
        self.salvar()

    def existe(self, codigo):
        return codigo in self.itens

    def obter(self, codigo):
        if codigo not in self.itens:
            raise ValueError(f"item {codigo} nao cadastrado")
        return self.itens[codigo]

    def listar(self, tipo=None):
        itens = sorted(self.itens.values(), key=lambda item: item.codigo)
        if tipo:
            itens = [item for item in itens if item.tipo == tipo]
        return itens

    @staticmethod
    def _validar_valores(item):
        if not item.descricao.strip():
            raise ValueError("a descricao nao pode ficar vazia")
        if not item.unidade.strip():
            raise ValueError("a unidade de medida nao pode ficar vazia")
        if item.custo < 0:
            raise ValueError("o custo nao pode ser negativo")
        if item.lead_time < 0:
            raise ValueError("o lead time nao pode ser negativo")
        if item.estoque_seguranca < 0:
            raise ValueError("o estoque de seguranca nao pode ser negativo")
        if item.lote_minimo < 1:
            raise ValueError("o lote minimo deve ser de pelo menos 1")

    def adicionar(self, item):
        if not utils.codigo_valido(item.codigo):
            raise ValueError("codigo invalido, use Tipo-Numero (ex.: PA-001)")
        if self.existe(item.codigo):
            raise ValueError(f"o codigo {item.codigo} ja esta cadastrado")
        self._validar_valores(item)
        self.itens[item.codigo] = item
        self.salvar()

    def alterar(self, codigo, **campos):
        item = self.obter(codigo)
        invalidos = set(campos) - self.CAMPOS_ALTERAVEIS
        if invalidos:
            raise ValueError(
                f"campos nao alteraveis: {', '.join(sorted(invalidos))}"
            )
        copia = Item.from_dict(codigo, {**item.to_dict(), **campos})
        self._validar_valores(copia)
        self.itens[codigo] = copia
        self.salvar()

    def cadastrar_interativo(self):
        print(">> Cadastro de item")
        codigo = utils.ler_codigo(">> Codigo (ex.: PA-001): ")
        if self.existe(codigo):
            print(f"ERRO: o codigo {codigo} ja esta cadastrado.")
            return
        descricao = utils.ler_texto(">> Descricao: ")
        unidade = utils.ler_texto(">> Unidade de medida (un, m, L...): ")
        tipo = utils.tipo_do_codigo(codigo)
        custo = 0.0
        if tipo == "MP":
            custo = utils.ler_decimal(">> Custo unitario (R$): ", minimo=0)
        lead_time = utils.ler_inteiro(">> Lead time (semanas): ", minimo=0)
        estoque_seguranca = utils.ler_inteiro(
            ">> Estoque de seguranca: ", minimo=0
        )
        lote_minimo = utils.ler_inteiro(">> Lote minimo: ", minimo=1)
        item = Item(codigo, descricao, unidade, custo,
                    lead_time, estoque_seguranca, lote_minimo)
        try:
            self.adicionar(item)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Item {codigo} cadastrado com sucesso.")

    def alterar_interativo(self):
        print(">> Alteracao de item (Enter mantem o valor atual)")
        codigo = utils.ler_codigo(">> Codigo do item: ")
        if not self.existe(codigo):
            print(f"ERRO: o item {codigo} nao esta cadastrado.")
            return
        item = self.obter(codigo)
        campos = {
            "descricao": utils.ler_texto(
                f">> Descricao [{item.descricao}]: ", obrigatorio=False
            ) or item.descricao,
            "unidade": utils.ler_texto(
                f">> Unidade [{item.unidade}]: ", obrigatorio=False
            ) or item.unidade,
            "lead_time": utils.ler_inteiro(
                f">> Lead time [{item.lead_time}]: ",
                minimo=0, padrao=item.lead_time,
            ),
            "estoque_seguranca": utils.ler_inteiro(
                f">> Estoque de seguranca [{item.estoque_seguranca}]: ",
                minimo=0, padrao=item.estoque_seguranca,
            ),
            "lote_minimo": utils.ler_inteiro(
                f">> Lote minimo [{item.lote_minimo}]: ",
                minimo=1, padrao=item.lote_minimo,
            ),
        }
        if item.tipo == "MP":
            campos["custo"] = utils.ler_decimal(
                f">> Custo unitario [{utils.formatar_moeda(item.custo)}]: ",
                minimo=0, padrao=item.custo,
            )
        try:
            self.alterar(codigo, **campos)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Item {codigo} alterado com sucesso.")

    def exibir_lista(self):
        if not self.itens:
            print("Nenhum item cadastrado.")
            return
        print(f"{'Codigo':<8}{'Descricao':<30}{'Un':<5}"
              f"{'Custo':>10}{'LT':>4}{'ES':>6}{'Lote':>7}")
        print("-" * 70)
        for item in self.listar():
            print(f"{item.codigo:<8}{item.descricao[:28]:<30}{item.unidade:<5}"
                  f"{utils.formatar_moeda(item.custo):>10}{item.lead_time:>4}"
                  f"{item.estoque_seguranca:>6}{item.lote_minimo:>7}")