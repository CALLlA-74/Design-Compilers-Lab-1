from builder import *


def main():
    regexp = input("Введите регулярное выражение: ")
    dfa = create_dfa(regexp)
    print("Детерминированный конечный автомат (см. файл \"ДКА.pdf\")")
    dfa.show_automaton("ДКА")

    mdfa = dfa.minimization()
    print("Минимизированный детерминированный конечный автомат (см. файл \"МДКА.pdf\")")
    mdfa.show_automaton("МДКА")

    while (True):
        check = input("Введите строку для моделирования МКА (для выхода введите '_end_'): ")
        if check == '_end_':
            return
        else:
            if mdfa.model_check(check):
                print("OK")
            else:
                print("INVALID STRING")


if __name__ == "__main__":
    main()
