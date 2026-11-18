import utils
from estrutura import Estrutura
from itens import CadastroItens
from persistencia import ErroPersistencia

LARGURA = 50


class Menu:
    def __init__(self, repositorio):
        self.itens = CadastroItens(repositorio)
        self.estrutura = Estrutura(repositorio, self.itens)

    @staticmethod
    def _cabecalho(titulo):
        print("=" * LARGURA)
        print(titulo)
        print("=" * LARGURA)

    @staticmethod
    def _executar(acao):
        try:
            acao()
        except (ValueError, ErroPersistencia) as erro:
            print(f"ERRO: {erro}.")

    def principal(self):
        while True:
            self._cabecalho("MRP II - PEDAL FORTE BICICLETAS")
            print("1. Cadastros (itens, estrutura, centros, roteiros)")
            print("2. Estoque (movimentar, saldo, kardex)")
            print("3. Plano Mestre de Producao (MPS)")
            print("4. Executar MRP")
            print("5. Ordens de producao e de compra")
            print("6. Carga x capacidade (CRP)")
            print("7. Custo padrao dos produtos")
            print("8. Relatorios (exportar CSV)")
            print("0. Sair")
            print("-" * LARGURA)
            opcao = utils.ler_opcao("Escolha uma opcao: ", list("123456780"))
            if opcao == "0":
                print("Ate logo!")
                return
            if opcao == "1":
                self.cadastros()
            else:
                print("Opcao ainda nao implementada.")

    def cadastros(self):
        acoes = {
            "1": ("Cadastrar item", self.itens.cadastrar_interativo),
            "2": ("Alterar item", self.itens.alterar_interativo),
            "3": ("Listar itens", self.itens.exibir_lista),
            "4": (
                "Adicionar componente a estrutura",
                self.estrutura.cadastrar_componente_interativo,
            ),
            "5": (
                "Alterar quantidade de componente",
                self.estrutura.alterar_quantidade_interativo,
            ),
            "6": (
                "Remover componente da estrutura",
                self.estrutura.remover_componente_interativo,
            ),
            "7": ("Exibir estrutura (BOM)", self.estrutura.exibir_interativo),
        }
        while True:
            self._cabecalho("CADASTROS")
            for chave, (titulo, _) in acoes.items():
                print(f"{chave}. {titulo}")
            print("0. Voltar")
            print("-" * LARGURA)
            opcao = utils.ler_opcao("Escolha uma opcao: ", [*acoes, "0"])
            if opcao == "0":
                return
            self._executar(acoes[opcao][1])