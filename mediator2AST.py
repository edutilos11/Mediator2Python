import os
import json
from lark import Lark, Transformer
from lark.tree import Tree

class MediatorTransformer(Transformer):
    def __init__(self):
        self.type_parameters = set()

    def template(self, children):
        processed = []
        for param in children:
            if isinstance(param, Tree) and param.data == 'template_param':
                # param.children == [ID Token, Tree parameter_type]
                name_tok, type_tree = param.children
                name = str(name_tok)
                # 区分抽象与具体
                if isinstance(type_tree, Tree) and type_tree.data == 'abstract_type_param':
                    kind = "type"
                    self.type_parameters.add(name)
                elif isinstance(type_tree, Tree) and type_tree.data == 'concrete_type_param':
                    # children[0] 是具体类型的 AST 或 Token
                    inner = type_tree.children[0]
                    kind = inner['name'] if isinstance(inner, dict) else str(inner)
                else:
                    kind = type_tree.data if isinstance(type_tree, Tree) else str(type_tree)
                processed.append((name, kind))
            else:
                # 已是 (name, kind) 形式
                processed.append(param)
        return processed

    def type_ref(self, name):
        name = str(name[0])
        if name in self.type_parameters:
            return {"type": "abstract", "name": name}
        else:
            return {"type": "concrete", "name": name}

script_dir = os.path.dirname(os.path.abspath(__file__))

# 载入工作目录下的 mediator.lark 作为语法定义
with open(os.path.join(script_dir, "mediator.lark"), "r", encoding="utf-8") as f:
    grammar = f.read()

mediator_parser = Lark(
    grammar,
    parser = 'lalr',
    transformer = MediatorTransformer()
)

def main():
    # 从工作目录读取待解析的源代码 original.txt
    txt_path = os.path.join(script_dir, "original.txt")
    with open(txt_path, 'r', encoding="utf-8") as f:
        source = f.read()
    # 调用解析器
    tree = mediator_parser.parse(source)

    with open(os.path.join(script_dir, "parsed_tree.txt"), "w", encoding="utf-8") as f:
        f.write(tree.pretty())
    # 将解析结果转成 JSON 格式并打印
    # structured = format_output(tree)
    # print(json.dumps(structured, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    main()