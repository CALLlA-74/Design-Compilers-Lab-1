import os

os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

from graphviz import Digraph
from prettytable import PrettyTable


class DFA:
    def __init__(self, table, init_state, final_states, alphabet: list):
        self.table = table
        self.init_state = list(set(init_state))
        self.final_states = list(set(final_states))

        self.states = list(set([k[0] for k in self.table.keys()]).union(set(self.final_states)))    # self._init_incidence_list()

        self.alphabet = {}
        for i in range(len(alphabet)):
            self.alphabet[alphabet[i]] = i

    @staticmethod
    def _get_incidence_list(states: list, table: dict) -> list:
        incidence_list = [[] for _ in states]
        for k, v in table.items():
            for val in v:
                incidence_list[states.index(k[0])].append(states.index(val))
        return incidence_list

    def show_automaton(self, title: str, show_end=True, show_isolated_empty=True):
        dot = Digraph()

        dot.node('S', 'Start')
        if show_end:
            dot.node('E', 'End')

        for i in self.init_state:
            dot.edge('S', str(i))

        for st in self.final_states:
            if show_end:
                dot.edge(str(st), 'E')
            else:
                dot.node(str(st), shape='cds')

        is_empty_isolated = True
        for st_from, v in self.table:
            for st_to in self.table[(st_from, v)]:
                if (str(st_from) == '∅' or str(st_to) == '∅') and st_from != st_to:
                    is_empty_isolated = False

        for st_from, v in self.table:
            for st_to in self.table[(st_from, v)]:
                st_from = str(st_from)
                st_to = str(st_to)
                if not show_isolated_empty and is_empty_isolated and st_from == '∅':
                    continue
                if st_from == '∅':
                    st_from = ""
                if st_to == '∅':
                    st_to = ""
                dot.node(st_from)
                dot.node(st_to)
                dot.edge(st_from, st_to, v)

        dot.render(title, view=True)

    @staticmethod
    def _get_inverse_states(alphabet: dict, states: list, table: dict):
        inverse_states = [[[] for _ in alphabet] for _ in states]
        for st_from, c in table.keys():
            for st_to in table[(st_from, c)]:
                inverse_states[states.index(st_to)][alphabet[c]].append(states.index(st_from))

        content = [[[states[state] for state in st_list] for st_list in row] for row in inverse_states]
        DFA._print_table(title="таблица обратных ребер (шаг 1)", col_names=list(alphabet.keys()), content=content,
                         row_names=states)
        return inverse_states

    @staticmethod
    def _buildMarkedTable(alphabet: dict, states: list, final_states: list, inverse_edges):
        marked = [[False for _ in range(len(states))] for _ in range(len(states))]
        q = []

        for i in range(len(states)):
            for j in range(len(states)):
                if marked[i][j] is False and ((states[i] in final_states) != (states[j] in final_states)):
                    marked[i][j] = marked[j][i] = True
                    q.append((i, j))
        """DFA._print_table(title="Пары вершин, соединяющие терминальные и нетерминальные состояния (шаг 3)", col_names=states,
                         content=marked, row_names=states)"""

        while len(q) > 0:
            i, j = q[0]
            q.remove((i, j))
            for c in alphabet.values():
                for r in inverse_edges[i][c]:
                    for s in inverse_edges[j][c]:
                        if not marked[r][s]:
                            marked[r][s] = marked[s][r] = True
                            q.append((r, s))
        DFA._print_table(title="Таблица пар эквивалентных состояний (шаги 3 и 4)", col_names=states, content=marked, row_names=states)
        return marked

    @staticmethod
    def _dfs(states: list, table: dict, init_state: list) -> list:
        incidence_list = DFA._get_incidence_list(states=states, table=table)
        visited = [False for _ in states]
        q = [states.index(init_state[0])]
        while len(q) > 0:
            curr = q[-1]
            q.pop(len(q) - 1)
            visited[curr] = True
            for to in incidence_list[curr]:
                if not visited[to]:
                    q.append(to)

        DFA._print_table(title="массив достижимости состояний из стартового (шаг 2)", content=[visited], col_names=states)
        return visited

    def minimization(self):
        prepared_states = ['∅'] + self.states.copy()
        idx = prepared_states.index(self.init_state[0])
        if idx != 1:
            prepared_states[1], prepared_states[idx] = prepared_states[idx], prepared_states[1]

        prepared_states_table = self.table.copy()
        for c in self.alphabet.keys():
            for st in prepared_states:
                if (st, c) not in prepared_states_table:
                    prepared_states_table[(st, c)] = [prepared_states[0]]

        prepared_dfa = DFA(table=prepared_states_table, init_state=self.init_state.copy(),
                       final_states=self.final_states.copy(), alphabet=list(self.alphabet.keys()))
        print("ДКА с добавленным состоянием ∅, в которое ведут все переходы по всем символам, которых не было в исходном ДКА (см. файл \"Prepared DFA.pdf\")")
        prepared_dfa.show_automaton("Prepared DFA")

        inverse_edges = DFA._get_inverse_states(alphabet=self.alphabet, states=prepared_states, table=prepared_states_table)
        reachable = self._dfs(states=prepared_states, table=prepared_states_table, init_state=self.init_state)
        marked = self._buildMarkedTable(alphabet=self.alphabet, states=prepared_states,
                                        final_states=self.final_states, inverse_edges=inverse_edges)

        component = [-1 for _ in prepared_states]
        for i in range(len(prepared_states)):
            if not marked[0][i]:
                component[i] = 0

        components_count = 0
        for i in range(1, len(prepared_states)):
            if not reachable[i]:
                continue
            if component[i] == -1:
                components_count += 1
                component[i] = components_count
                for j in range(i+1, len(prepared_states)):
                    if not marked[i][j]:
                        component[j] = components_count

        self._print_table(title="Классы эквивалентности (шаг 5)", content=[component], col_names=prepared_states)

        new_table = {}
        new_states = {}
        for comp in range(1, len(component)):
            new_states[component[comp]] = set()
        for idx_comp in range(1, len(component)):
            new_states[component[idx_comp]].add(prepared_states[idx_comp])
        for k, v in new_states.items():
            new_states[k] = self._concat_states(v)

        for k, v in self.table.items():
            new_from = tuple(new_states[component[prepared_states.index(k[0])]])
            new_to = tuple(new_states[component[prepared_states.index(v[0])]])
            new_table[(new_from, k[1])] = [new_to]

        new_init_state = []
        new_final_states = []
        for st in self.init_state:
            new_init_state.append(tuple(new_states[component[prepared_states.index(st)]]))
        for st in self.final_states:
            new_final_states.append(tuple(new_states[component[prepared_states.index(st)]]))

        new_init_state = list(set(new_init_state))
        new_final_states = list(set(new_final_states))
        return DFA(table=new_table, init_state=new_init_state, final_states=new_final_states, alphabet=list(self.alphabet.keys()))

    def model_check(self, check_str):
        curr_st = self.init_state[0]
        for c in check_str:
            print(curr_st, c)
            if (curr_st, c) not in self.table:
                return False
            curr_st = self.table[(curr_st, c)][0]

        return curr_st in self.final_states

    @staticmethod
    def _concat_states(states_list: set) -> set:
        res = set()
        for st in states_list:
            res = res.union(set(st))
        return res

    @staticmethod
    def _print_table(title: str, content: list, col_names: list, row_names: list = None):
        if row_names is not None:
            col_names = [""] + col_names
            content = [[row_names[i]] + content[i] for i in range(len(row_names))]
        table = PrettyTable(align='l')
        table.title = title
        table.field_names = col_names
        table.add_rows(content)

        print(table)
        print()
