from menu import Menu
from persistencia import ErroPersistencia, Repositorio


def main():
    try:
        menu = Menu(Repositorio())
    except ErroPersistencia as erro:
        print(f"ERRO ao carregar os dados: {erro}")
        return
    try:
        menu.principal()
    except (KeyboardInterrupt, EOFError):
        print("\nSistema encerrado pelo usuario.")


if __name__ == "__main__":
    main()