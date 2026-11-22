import utils


class CalculoCustos:
    def __init__(self, cadastro_itens, estrutura, capacidade):
        self.cadastro = cadastro_itens
        self.estrutura = estrutura
        self.capacidade = capacidade

    def mao_de_obra(self, codigo):
        roteiro = self.capacidade.roteiro(codigo)
        if roteiro is None:
            return None
        centro = self.capacidade.obter_centro(roteiro["centro"])
        horas = roteiro["tempo"]
        return {
            "centro": centro.codigo,
            "horas": horas,
            "custo_hora": centro.custo_hora,
            "total": round(horas * centro.custo_hora, 4),
        }

    def composicao(self, codigo):
        item = self.cadastro.obter(codigo)
        if not item.fabricado:
            raise ValueError(
                f"{codigo} e materia-prima; o custo e o cadastrado no item"
            )
        linhas = []
        for registro in self.estrutura.componentes(codigo):
            componente = self.cadastro.obter(registro["componente"])
            quantidade = registro["quantidade"]
            custo = self.custo_padrao(componente.codigo)
            linhas.append(
                (componente, quantidade, custo, round(quantidade * custo, 4))
            )
        return linhas, self.mao_de_obra(codigo)

    def custo_padrao(self, codigo):
        item = self.cadastro.obter(codigo)
        if not item.fabricado:
            return item.custo
        linhas, mao = self.composicao(codigo)
        total = sum(linha[3] for linha in linhas)
        if mao:
            total += mao["total"]
        return round(total, 4)

    def atualizar_custos(self):
        fabricados = [i for i in self.cadastro.listar() if i.fabricado]
        for item in fabricados:
            item.custo = self.custo_padrao(item.codigo)
        self.cadastro.salvar()
        return len(fabricados)

    def exibir_custo(self, codigo):
        item = self.cadastro.obter(codigo)
        linhas, mao = self.composicao(codigo)
        print(f"CUSTO PADRAO - {item.codigo} {item.descricao}")
        print(f"{'Item':<8}{'Descricao':<30}{'Qtde':>8}"
              f"{'Custo un.':>12}{'Total':>12}")
        print("-" * 70)
        if not linhas:
            print("(sem componentes cadastrados)")
        for componente, quantidade, custo, total in linhas:
            print(f"{componente.codigo:<8}{componente.descricao[:28]:<30}"
                  f"{utils.formatar_quantidade(quantidade):>8}"
                  f"{utils.formatar_moeda(custo):>12}"
                  f"{utils.formatar_moeda(total):>12}")
        if mao:
            horas = utils.formatar_quantidade(mao["horas"])
            rotulo = f"Mao de obra {mao['centro']}"
            print(f"{rotulo:<38}{horas + ' h':>8}"
                  f"{utils.formatar_moeda(mao['custo_hora']):>12}"
                  f"{utils.formatar_moeda(mao['total']):>12}")
        else:
            print("ATENCAO: item sem roteiro; mao de obra nao incluida.")
        print("-" * 70)
        total = utils.formatar_moeda(self.custo_padrao(codigo))
        print(f"{'CUSTO PADRAO TOTAL R$':<58}{total:>12}")

    def exibir_resumo(self):
        fabricados = [i for i in self.cadastro.listar() if i.fabricado]
        if not fabricados:
            print("Nenhum item fabricado cadastrado.")
            return
        print(f"{'Item':<8}{'Descricao':<30}{'Componentes':>13}"
              f"{'Mao de obra':>13}{'Total':>11}")
        print("-" * 75)
        for item in fabricados:
            linhas, mao = self.composicao(item.codigo)
            componentes = sum(linha[3] for linha in linhas)
            obra = mao["total"] if mao else 0.0
            print(f"{item.codigo:<8}{item.descricao[:28]:<30}"
                  f"{utils.formatar_moeda(componentes):>13}"
                  f"{utils.formatar_moeda(obra):>13}"
                  f"{utils.formatar_moeda(componentes + obra):>11}")

    def exibir_interativo(self):
        codigo = utils.ler_codigo(
            ">> Codigo do item fabricado (PA ou SA): ", tipos=("PA", "SA")
        )
        try:
            self.exibir_custo(codigo)
        except ValueError as erro:
            print(f"ERRO: {erro}.")

    def atualizar_interativo(self):
        quantidade = self.atualizar_custos()
        print(f"Custo padrao gravado em {quantidade} itens fabricados.")
