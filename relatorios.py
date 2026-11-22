import utils

PASTA = "exportacoes"


class Relatorios:
    def __init__(self, repositorio, cadastro_itens, estoque, ordens):
        self.repositorio = repositorio
        self.cadastro = cadastro_itens
        self.estoque = estoque
        self.ordens = ordens

    def _gravar(self, nome, campos, linhas):
        self.repositorio.pasta(PASTA)
        arquivo = f"{PASTA}/{nome}"
        self.repositorio.salvar_csv(
            arquivo, campos, linhas, encoding="utf-8-sig"
        )
        return self.repositorio.caminho(arquivo), len(linhas)

    def exportar_estoque(self):
        campos = ["codigo", "descricao", "tipo", "unidade", "saldo",
                  "estoque_seguranca", "situacao"]
        linhas = []
        for item, saldo in self.estoque.posicao():
            abaixo = saldo < item.estoque_seguranca
            linhas.append({
                "codigo": item.codigo,
                "descricao": item.descricao,
                "tipo": item.tipo,
                "unidade": item.unidade,
                "saldo": utils.formatar_quantidade(saldo),
                "estoque_seguranca": utils.formatar_quantidade(
                    item.estoque_seguranca
                ),
                "situacao": "ABAIXO" if abaixo else "OK",
            })
        return self._gravar("posicao_estoque.csv", campos, linhas)

    def exportar_ordens(self):
        campos = ["ordem", "tipo", "item", "descricao", "quantidade",
                  "semana_liberacao", "semana_entrega", "status",
                  "atrasada"]
        linhas = []
        ordens = self.ordens.listar() + self.ordens.listar(abertas=False)
        for ordem in ordens:
            linhas.append({
                "ordem": ordem.numero,
                "tipo": ordem.tipo,
                "item": ordem.item,
                "descricao": self.cadastro.obter(ordem.item).descricao,
                "quantidade": utils.formatar_quantidade(ordem.quantidade),
                "semana_liberacao": ordem.semana_liberacao,
                "semana_entrega": ordem.semana_entrega,
                "status": ordem.status,
                "atrasada": "SIM" if ordem.atrasada else "NAO",
            })
        return self._gravar("lista_ordens.csv", campos, linhas)

    @staticmethod
    def _informar(caminho, total):
        print(f"Arquivo gerado: {caminho} ({total} linhas)")

    def exportar_estoque_interativo(self):
        self._informar(*self.exportar_estoque())

    def exportar_ordens_interativo(self):
        self._informar(*self.exportar_ordens())

    def exportar_tudo_interativo(self):
        self.exportar_estoque_interativo()
        self.exportar_ordens_interativo()
