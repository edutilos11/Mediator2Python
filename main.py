from mediator2AST import *
from AST2python import *

if __name__ == "__main__":
    txt_path = os.path.join(script_dir, "original.txt")
    with open(txt_path, 'r', encoding="utf-8") as f:
        source = f.read()
    
    mediator_parser = Lark(
        grammar,
        parser = 'lalr',
        transformer = MediatorTransformer()
    )
    AST = mediator_parser.parse(source)
    ADict = LLM(AST.pretty(), template="prompt_template.txt")
    python_code = converter.convert_from_ast(ADict)