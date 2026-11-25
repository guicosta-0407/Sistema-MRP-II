import utils

LARGURA_ARVORE = 48


class Estrutura:
    ARQUIVO = "estrutura.json"
    COMPONENTES_PERMITIDOS = {
        "PA": ("SA", "MP"),
        "SA": ("MP",),
        "MP": (),
    }

    def __init__(self, repositorio, cadastro_itens):
        self.repositorio = repositorio
        self.cadastro = cadastro_itens
        self.bom = {}
        self.carregar()

    def carregar(self):
        self.bom = self.repositorio.carregar_json(self.ARQUIVO)

    def salvar(self):
        self.repositorio.salvar_json(self.ARQUIVO, self.bom)

    def componentes(self, pai):
        return self.bom.get(pai, [])

    def pais_de(self, codigo):
        return [
            pai
            for pai, registros in self.bom.items()
            if any(r["componente"] == codigo for r in registros)
        ]

    def em_uso(self, codigo):
        tem_estrutura_propria = bool(self.bom.get(codigo))
        return tem_estrutura_propria or bool(self.pais_de(codigo))

    def _validar(self, pai, componente, quantidade):
        item_pai = self.cadastro.obter(pai)
        item_componente = self.cadastro.obter(componente)
        permitidos = self.COMPONENTES_PERMITIDOS[item_pai.tipo]
        if not permitidos:
            raise ValueError(f"{pai} e materia-prima e nao possui estrutura")
        if item_componente.tipo not in permitidos:
            raise ValueError(
                f"um {item_pai.tipo} so aceita componentes do tipo "
                f"{' ou '.join(permitidos)}"
            )
        if quantidade <= 0:
            raise ValueError("a quantidade deve ser maior que zero")

    def adicionar_componente(self, pai, componente, quantidade):
        self._validar(pai, componente, quantidade)
        lista = self.bom.setdefault(pai, [])
        if any(c["componente"] == componente for c in lista):
            raise ValueError(
                f"{componente} ja e componente de {pai}; "
                "use a alteracao de quantidade"
            )
        lista.append({"componente": componente, "quantidade": quantidade})
        self.salvar()

    def alterar_quantidade(self, pai, componente, quantidade):
        if quantidade <= 0:
            raise ValueError("a quantidade deve ser maior que zero")
        for registro in self.componentes(pai):
            if registro["componente"] == componente:
                registro["quantidade"] = quantidade
                self.salvar()
                return
        raise ValueError(f"{componente} nao e componente de {pai}")

    def remover_componente(self, pai, componente):
        lista = self.componentes(pai)
        restantes = [c for c in lista if c["componente"] != componente]
        if len(restantes) == len(lista):
            raise ValueError(f"{componente} nao e componente de {pai}")
        if restantes:
            self.bom[pai] = restantes
        else:
            del self.bom[pai]
        self.salvar()

    def explodir(self, codigo, nivel=1):
        resultado = []
        for registro in self.componentes(codigo):
            filho = registro["componente"]
            resultado.append((nivel, filho, registro["quantidade"]))
            resultado.extend(self.explodir(filho, nivel + 1))
        return resultado

    def niveis(self, codigo):
        agrupado = {0: [codigo]}
        for nivel, filho, _ in self.explodir(codigo):
            agrupado.setdefault(nivel, []).append(filho)
        return agrupado

    def _desenhar(self, codigo, prefixo, linhas):
        registros = self.componentes(codigo)
        for indice, registro in enumerate(registros):
            ultimo = indice == len(registros) - 1
            conector = "└── " if ultimo else "├── "
            item = self.cadastro.obter(registro["componente"])
            inicio = f"{prefixo}{conector}{item.codigo} {item.descricao} "
            quantidade = utils.formatar_quantidade(registro["quantidade"])
            linhas.append(
                f"{inicio.ljust(LARGURA_ARVORE, '.')} "
                f"{quantidade} {item.unidade}"
            )
            extensao = "    " if ultimo else "│   "
            self._desenhar(item.codigo, prefixo + extensao, linhas)

    def exibir_arvore(self, codigo):
        raiz = self.cadastro.obter(codigo)
        print(f"{raiz.codigo} {raiz.descricao}")
        if not self.componentes(codigo):
            print("(sem componentes cadastrados)")
            return
        linhas = []
        self._desenhar(codigo, "", linhas)
        print("\n".join(linhas))
        partes = []
        for nivel, codigos in sorted(self.niveis(codigo).items()):
            partes.append(f"{nivel} = {', '.join(dict.fromkeys(codigos))}")
        print("Niveis: " + " | ".join(partes))

    def cadastrar_componente_interativo(self):
        print(">> Cadastro de componente da estrutura")
        pai = utils.ler_codigo(
            ">> Codigo do item pai (PA ou SA): ", tipos=("PA", "SA")
        )
        if not self.cadastro.existe(pai):
            print(f"ERRO: o item {pai} nao esta cadastrado.")
            return
        permitidos = self.COMPONENTES_PERMITIDOS[utils.tipo_do_codigo(pai)]
        componente = utils.ler_codigo(
            f">> Codigo do componente ({' ou '.join(permitidos)}): ",
            tipos=permitidos,
        )
        quantidade = utils.ler_decimal(">> Quantidade por unidade: ", minimo=0)
        try:
            self.adicionar_componente(pai, componente, quantidade)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Componente {componente} adicionado a {pai}.")

    def alterar_quantidade_interativo(self):
        print(">> Alteracao de quantidade de componente")
        pai = utils.ler_codigo(">> Codigo do item pai: ", tipos=("PA", "SA"))
        componente = utils.ler_codigo(">> Codigo do componente: ")
        quantidade = utils.ler_decimal(
            ">> Nova quantidade por unidade: ", minimo=0
        )
        try:
            self.alterar_quantidade(pai, componente, quantidade)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Quantidade de {componente} em {pai} alterada.")

    def remover_componente_interativo(self):
        print(">> Remocao de componente da estrutura")
        pai = utils.ler_codigo(">> Codigo do item pai: ", tipos=("PA", "SA"))
        componente = utils.ler_codigo(">> Codigo do componente: ")
        try:
            self.remover_componente(pai, componente)
        except ValueError as erro:
            print(f"ERRO: {erro}.")
            return
        print(f"Componente {componente} removido de {pai}.")

    def exibir_interativo(self):
        codigo = utils.ler_codigo(">> Codigo do produto: ")
        try:
            self.exibir_arvore(codigo)
        except ValueError as erro:
            print(f"ERRO: {erro}.")

    def onde_usado_interativo(self):
        print(">> Onde o item e usado")
        codigo = utils.ler_codigo(">> Codigo do item: ")
        if not self.cadastro.existe(codigo):
            print(f"ERRO: o item {codigo} nao esta cadastrado.")
            return
        pais = self.pais_de(codigo)
        if not pais:
            print(f"{codigo} nao e usado como componente em nenhum item.")
            return
        print(f"{codigo} e componente de:")
        for pai in pais:
            item_pai = self.cadastro.obter(pai)
            quantidade = next(
                r["quantidade"]
                for r in self.componentes(pai)
                if r["componente"] == codigo
            )
            print(
                f"  - {pai} {item_pai.descricao} "
                f"({utils.formatar_quantidade(quantidade)} {item_pai.unidade})"
            )