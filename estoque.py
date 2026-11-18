import utils

TIPOS = {"E": "ENTRADA", "S": "SAIDA", "A": "AJUSTE"}


def normalizar_numero(valor):
    valor = round(float(valor), 4)
    return int(valor) if valor.is_integer() else valor


class Movimento:
    CAMPOS = ["data", "codigo", "tipo", "quantidade", "saldo", "documento"]

    def __init__(self, data, codigo, tipo, quantidade, saldo, documento):
        self.data = data
        self.codigo = codigo
        self.tipo = tipo
        self.quantidade = quantidade
        self.saldo = saldo
        self.documento = documento

    def to_linha(self):
        return {campo: getattr(self, campo) for campo in self.CAMPOS}

    @classmethod
    def from_linha(cls, linha):
        return cls(
            linha["data"],
            linha["codigo"],
            linha["tipo"],
            normalizar_numero(linha["quantidade"]),
            normalizar_numero(linha["saldo"]),
            linha["documento"],
        )


class Estoque:
    ARQUIVO_SALDOS = "estoque.json"
    ARQUIVO_MOVIMENTOS = "movimentos.csv"

    def __init__(self, repositorio, cadastro_itens):
        self.repositorio = repositorio
        self.cadastro = cadastro_itens
        self.saldos = {}
        self.movimentos = []
        self.carregar()

    def carregar(self):
        self.saldos = self.repositorio.carregar_json(self.ARQUIVO_SALDOS)
        linhas = self.repositorio.carregar_csv(self.ARQUIVO_MOVIMENTOS)
        self.movimentos = [Movimento.from_linha(linha) for linha in linhas]

    def salvar_saldos(self):
        self.repositorio.salvar_json(self.ARQUIVO_SALDOS, self.saldos)

    def saldo(self, codigo):
        return self.saldos.get(codigo, 0)

    def kardex(self, codigo):
        return [m for m in self.movimentos if m.codigo == codigo]

    def possui_movimento(self, codigo):
        return any(m.codigo == codigo for m in self.movimentos)

    def abaixo_seguranca(self, codigo):
        item = self.cadastro.obter(codigo)
        return self.saldo(codigo) < item.estoque_seguranca

    def posicao(self):
        return [
            (item, self.saldo(item.codigo))
            for item in self.cadastro.listar()
        ]

    def registrar(self, codigo, tipo, quantidade, documento, data=None):
        item = self.cadastro.obter(codigo)
        if tipo not in TIPOS.values():
            raise ValueError("tipo de movimentacao invalido")
        documento = documento.strip()
        if not documento:
            raise ValueError("informe o documento ou motivo da movimentacao")
        if tipo != "AJUSTE" and quantidade <= 0:
            raise ValueError("a quantidade deve ser maior que zero")
        if tipo == "AJUSTE" and quantidade == 0:
            raise ValueError("o ajuste nao pode ser zero")
        variacao = -quantidade if tipo == "SAIDA" else quantidade
        saldo_atual = self.saldo(codigo)
        novo_saldo = normalizar_numero(saldo_atual + variacao)
        if novo_saldo < 0:
            atual = utils.formatar_quantidade(saldo_atual)
            raise ValueError(
                f"saldo insuficiente (saldo atual: {atual} {item.unidade})"
            )
        movimento = Movimento(
            data or utils.data_hoje(),
            codigo,
            tipo,
            normalizar_numero(variacao),
            novo_saldo,
            documento,
        )
        self.repositorio.anexar_csv(
            self.ARQUIVO_MOVIMENTOS, Movimento.CAMPOS, movimento.to_linha()
        )
        self.movimentos.append(movimento)
        self.saldos[codigo] = novo_saldo
        self.salvar_saldos()
        return movimento

    @staticmethod
    def _com_sinal(valor):
        texto = utils.formatar_quantidade(valor)
        return f"+{texto}" if valor > 0 else texto

    def _exibir_alerta(self, item):
        if not self.abaixo_seguranca(item.codigo):
            return
        saldo = utils.formatar_quantidade(self.saldo(item.codigo))
        seguranca = utils.formatar_quantidade(item.estoque_seguranca)
        print(f"ALERTA: saldo ({saldo} {item.unidade}) abaixo do estoque "
              f"de seguranca ({seguranca} {item.unidade}).")

    def exibir_kardex(self, codigo):
        item = self.cadastro.obter(codigo)
        print(f"KARDEX - {item.codigo} {item.descricao} ({item.unidade})")
        movimentos = self.kardex(codigo)
        if not movimentos:
            print("Nenhuma movimentacao registrada.")
        else:
            print(f"{'Data':<12}{'Tipo':<9}{'Qtde':>8}{'Saldo':>8}  Documento")
            for m in movimentos:
                quantidade = self._com_sinal(m.quantidade)
                saldo = utils.formatar_quantidade(m.saldo)
                print(f"{m.data:<12}{m.tipo:<9}{quantidade:>8}"
                      f"{saldo:>8}  {m.documento}")
        self._exibir_alerta(item)

    def exibir_posicao(self):
        posicao = self.posicao()
        if not posicao:
            print("Nenhum item cadastrado.")
            return
        print(f"{'Codigo':<8}{'Descricao':<30}{'Saldo':>9}"
              f"{'Seguranca':>11}  Situacao")
        print("-" * 70)
        for item, saldo in posicao:
            situacao = "ABAIXO" if saldo < item.estoque_seguranca else "OK"
            print(f"{item.codigo:<8}{item.descricao[:28]:<30}"
                  f"{utils.formatar_quantidade(saldo):>9}"
                  f"{utils.formatar_quantidade(item.estoque_seguranca):>11}"
                  f"  {situacao}")

    def movimentar_interativo(self):
        print(">> Movimentacao de estoque")
        codigo = utils.ler_codigo(">> Codigo do item: ")
        if not self.cadastro.existe(codigo):
            print(f"ERRO: o item {codigo} nao esta cadastrado.")
            return
        item = self.cadastro.obter(codigo)
        opcao = utils.ler_opcao(
            ">> Tipo [E]ntrada [S]aida [A]juste: ", list(TIPOS)
        )
        tipo = TIPOS[opcao]
        if tipo == "AJUSTE":
            quantidade = utils.ler_decimal(
                ">> Quantidade do ajuste (negativo reduz): "
            )
        else:
            quantidade = utils.ler_decimal(">> Quantidade: ", minimo=0)
        documento = utils.ler_texto(">> Documento/motivo: ")
        data = utils.ler_data(">> Data [Enter = hoje]: ")
        try:
            self.registrar(codigo, tipo, quantidade, documento, data)
        except ValueError as erro:
            print(f"ERRO: {erro}. Operacao cancelada.")
            return
        saldo = utils.formatar_quantidade(self.saldo(codigo))
        print(f"{tipo} registrada. Saldo atual de {codigo}: "
              f"{saldo} {item.unidade}.")
        self._exibir_alerta(item)

    def consultar_interativo(self):
        codigo = utils.ler_codigo(">> Codigo do item: ")
        try:
            self.exibir_kardex(codigo)
        except ValueError as erro:
            print(f"ERRO: {erro}.")