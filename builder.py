from automaton import DFA
from typing import List, Tuple
from graphviz import Digraph

isDebug = False


class TreeNode:
    def __init__(self, v=None, l=None, r=None):
        self.left = l
        self.right = r
        self.value = v
        self.followpos = []
        self.label_i = ''

    def copy(cur):
        return TreeNode(cur.value, cur.left, cur.right)
    left = None
    right = None
    value = None

    def show_tree(self, dot=None, show_params=False, show_end=False):
        if not dot:
            dot = Digraph()
        label = "END" if show_end and self.value == '#' else str(self.value)
        label += ("  " + str(self.label_i) if self.label_i else "")

        def nodes_to_idx(nodes):
            return [node.idx for node in nodes]
        if show_params:
            label = label + "(" + str(self.nullable) + ", " \
                    + str(nodes_to_idx(self.firstpos)) + ", "\
                    + str(nodes_to_idx(self.lastpos)) + ", " + str(nodes_to_idx(self.followpos)) + ")"

        dot.node(str(self.idx), label)

        if self.left:
            dot.edge(str(self.idx), str(self.left.idx))
            self.left.show_tree(dot, show_params=show_params)
        if self.right:
            dot.edge(str(self.idx), str(self.right.idx))
            self.right.show_tree(dot, show_params=show_params)

        return dot

    def update_idx(self, i=0):
        self.idx = i
        if self.left:
            self.left.update_idx(i * 2 + 1)
        if self.right:
            self.right.update_idx(i * 2 + 2)

    def update_nullable(self):
        if self.left:
            self.left.update_nullable()
        if self.right:
            self.right.update_nullable()

        if self.value == '*':
            self.nullable = True
        elif self.value == '|':
            self.nullable = self.left.nullable or self.right.nullable
        elif self.value == '':
            self.nullable = self.left.nullable and self.right.nullable
        else:
            self.nullable = False
        return self.nullable

    def calc_firstpos(self):
        if self.left:
            self.left.calc_firstpos()
        if self.right:
            self.right.calc_firstpos()

        if self.value in ['*', '+']:
            self.firstpos = self.left.firstpos.copy()
        elif self.value == '':
            self.firstpos = self.left.firstpos.copy()
            if self.left.nullable:
                self.firstpos += self.right.firstpos
        elif self.value == '|':
            self.firstpos = self.left.firstpos + self.right.firstpos
        else:
            self.firstpos = [self]
        return self.firstpos

    def calc_lastpos(self):
        if self.left:
            self.left.calc_lastpos()
        if self.right:
            self.right.calc_lastpos()

        if self.value in ['*', '+']:
            self.lastpos = self.left.lastpos.copy()
        elif self.value == '':
            self.lastpos = self.right.lastpos.copy()
            if self.right.nullable:
                self.lastpos += self.left.lastpos
        elif self.value == '|':
            self.lastpos = self.left.lastpos + self.right.lastpos
        else:
            self.lastpos = [self]
        return self.lastpos

    def calc_followpos(self):
        if self.left:
            self.left.calc_followpos()
        if self.right:
            self.right.calc_followpos()
        if self.value == '':
            for i in self.left.lastpos:
                i.followpos += self.right.firstpos
        elif self.value == '*' or self.value == '+':
            for i in self.lastpos:
                i.followpos += self.firstpos

    def dfs_tree(self, func_in=None, func_out=None):
        if func_in:
            func_in(self)
        if self.left:
            self.left.dfs_tree(func_in, func_out)
        if self.right:
            self.right.dfs_tree(func_in, func_out)
        if func_out:
            func_out(self)


def print_debug(*msgs):
    if isDebug:
        print('DBG: EXPR: ', *msgs)


def _make_tree(regexp) -> Tuple[TreeNode, List[TreeNode], List[str]]:
    def get_expr(exp) -> Tuple[TreeNode, int]:
        def cat_exprs(left, right):
            return TreeNode('', left, right)

        print_debug("".join(exp))
        cur_pos = 0
        tree = None

        if exp[cur_pos] == '(':
            cur_pos += 1
            e, n = get_expr(exp[cur_pos:])
            cur_pos += n
            tree = e
            while exp[cur_pos] != ')':
                e, n = get_expr(exp[cur_pos:])
                cur_pos += n
                tree = cat_exprs(tree, e)
        elif exp[cur_pos] not in ['+', '*', '|', ')']:
            tree = TreeNode(exp[cur_pos])
        else:
            raise Exception('Waiting for "(", term: ' + "".join(exp) + ' ' + str(cur_pos))

        cur_pos += 1
        if cur_pos < len(exp) and exp[cur_pos] in ['+', '*']:
                tree = TreeNode(exp[cur_pos], tree)
                cur_pos += 1

        if cur_pos < len(exp) and exp[cur_pos] == '|':
                next_expr, l = get_expr(exp[cur_pos+1:])
                return TreeNode('|', tree, next_expr), cur_pos + 1 + l

        return tree, cur_pos
    tree, _ = get_expr(['('] + list(regexp) + [')'])
    tree.update_idx()
    tree.update_nullable()
    tree.calc_firstpos()
    tree.calc_lastpos()
    tree.calc_followpos()

    leafs = []

    def add_leaf(node: TreeNode):
        if node.value not in ['|', '*', '+', '']:
            leafs.append(node)

    tree.dfs_tree(func_out=add_leaf)
    for idx, leaf in enumerate(leafs, 1):
        leaf.label_i = idx
    alphabet = list(set([leaf.value for leaf in leafs]))

    return tree, leafs, alphabet


def build_dfa(root: TreeNode, alphabet, end_symb='#'):
    def make_state(nodes):
        return tuple(sorted([node.label_i for node in nodes]))

    def is_end(nodes):
        for node in nodes:
            if node.value == end_symb:
                return True
        return False
    Dstates = []

    table = {}
    queue = [root.firstpos]

    last = []
    while len(queue):
        state = queue.pop()
        Dstates += [make_state(state)]

        for c in alphabet:
            U = []
            for p in state:
                if p.value == c:
                    U += p.followpos
            U = list(set(U))
            if not len(U):
                continue

            if make_state(U) not in Dstates:
                queue.append(U)

            table[make_state(state), c] = [make_state(U)]

            print_debug(make_state(state), c, [make_state(U)])

        if is_end(state):
            last += [make_state(state)]

    alphabet2 = []
    for c in alphabet:
        if c != end_symb:
            alphabet2.append(c)
    return DFA(table=table, init_state=[Dstates[0]], final_states=last, alphabet=alphabet2)


def create_dfa(regexp: str):
    tree, leafs, alphabet = _make_tree(regexp + '#')
    print("Синтаксическое дерево (см. файл \"Синтаксическое дерево.pdf\")")
    tree.show_tree().render("Синтаксическое дерево", view=True)

    return build_dfa(tree, alphabet)


