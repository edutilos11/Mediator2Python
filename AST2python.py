"""
Mediator语言到Python的Jinja2转换器
支持直接从字典形式的AST转换为Python代码
"""
from jinja2 import Environment, DictLoader
from typing import Dict, List, Any, Optional, Union

# Jinja2模板定义
templates = {
    # 主模板
    'main.py.j2': '''
"""
Generated Python code from Mediator language
This code simulates the behavior of Mediator automata and systems
"""

from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue
import time
from abc import ABC, abstractmethod

# 基础类型映射
{% for typedef in typedefs %}
{{ typedef }}
{% endfor %}

# 自定义函数
{% for function in functions %}
{{ function }}
{% endfor %}

# 基础通信类
class Port:
    """端口类，用于自动机之间的通信"""
    def __init__(self, name: str, direction: str, data_type: type, init_value=None):
        self.name = name
        self.direction = direction  # 'in' or 'out'
        self.data_type = data_type
        self.value = init_value
        self.req_read = False
        self.req_write = False
        self._lock = threading.Lock()
    
    def read(self):
        with self._lock:
            if self.direction == 'in' and self.req_write:
                self.req_read = False
                self.req_write = False
                return self.value
        return None
    
    def write(self, value):
        with self._lock:
            if self.direction == 'out':
                self.value = value
                self.req_write = True
                return True
        return False

class Automaton(ABC):
    """自动机基类"""
    def __init__(self, name: str):
        self.name = name
        self.ports: Dict[str, Port] = {}
        self.variables: Dict[str, Any] = {}
        self.running = False
        self._thread = None
    
    def add_port(self, name: str, direction: str, data_type: type, init_value=None):
        self.ports[name] = Port(name, direction, data_type, init_value)
    
    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run)
            self._thread.start()
    
    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join()
    
    def _run(self):
        while self.running:
            self._execute_transitions()
            time.sleep(0.001)  # 防止过度占用CPU
    
    @abstractmethod
    def _execute_transitions(self):
        """执行转换逻辑"""
        pass

# 自动机实现
{% for automaton in automata %}
{{ automaton }}
{% endfor %}

# 系统实现
{% for system in systems %}
{{ system }}
{% endfor %}

if __name__ == "__main__":
    # 示例使用代码
    print("Mediator to Python conversion completed!")
''',

    # 函数模板
    'function.py.j2': '''
{% if template_params %}
def {{ name }}({% for param in template_params %}{{ param }}, {% endfor %}{% for arg in args %}{{ arg.name }}: {{ arg.type|python_type }}{% if arg.init_value %} = {{ arg.init_value }}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}) -> {{ return_type|python_type }}:
{% else %}
def {{ name }}({% for arg in args %}{{ arg.name }}: {{ arg.type|python_type }}{% if arg.init_value %} = {{ arg.init_value }}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}) -> {{ return_type|python_type }}:
{% endif %}
    """{{ name }} function converted from Mediator"""
    {% if variables %}
    # 局部变量
    {% for var in variables %}
    {{ var.name }}: {{ var.type|python_type }} = {{ var.init_value if var.init_value else 'None' }}
    {% endfor %}
    {% endif %}
    
    # 函数体
    {% for stmt in statements %}
    {{ stmt|python_statement }}
    {% endfor %}
''',

    # 自动机模板
    'automaton.py.j2': '''
class {{ name }}{% if template_params %}Generic{% endif %}(Automaton):
    """{{ name }} automaton converted from Mediator"""
    
    def __init__(self{% if template_params %}, {% for param in template_params %}{{ param }}: type{% if not loop.last %}, {% endif %}{% endfor %}{% endif %}):
        super().__init__("{{ name }}")
        
        # 添加端口
        {% for port in ports %}
        self.add_port("{{ port.name }}", "{{ port.direction }}", {{ port.type|python_type }})
        {% endfor %}
        
        # 初始化变量
        {% for var in variables %}
        self.variables["{{ var.name }}"] = {{ var.init_value if var.init_value else 'None' }}
        {% endfor %}
    
    def _execute_transitions(self):
        """执行转换逻辑"""
        {% for transition in transitions %}
        # 转换: {{ transition.guard }}
        if {{ transition.guard|python_condition }}:
            {% for stmt in transition.statements %}
            {{ stmt|python_statement }}
            {% endfor %}
            return
        {% endfor %}
''',

    # 系统模板
    'system.py.j2': '''
class {{ name }}{% if template_params %}Generic{% endif %}:
    """{{ name }} system converted from Mediator"""
    
    def __init__(self{% if template_params %}, {% for param in template_params %}{{ param }}: type{% if not loop.last %}, {% endif %}{% endfor %}{% endif %}):
        self.name = "{{ name }}"
        self.components: Dict[str, Automaton] = {}
        self.internals: List[str] = []
        
        # 创建组件
        {% for comp_name, comp_type in components.items() %}
        self.components["{{ comp_name }}"] = {{ comp_type }}()
        {% endfor %}
        
        # 内部节点
        {% for internal in internals %}
        self.internals.append("{{ internal }}")
        {% endfor %}
        
        # 建立连接
        self._setup_connections()
    
    def _setup_connections(self):
        """建立组件之间的连接"""
        {% for connection in connections %}
        # 连接: {{ connection }}
        pass  # TODO: 实现具体的连接逻辑
        {% endfor %}
    
    def start(self):
        """启动所有组件"""
        for component in self.components.values():
            component.start()
    
    def stop(self):
        """停止所有组件"""
        for component in self.components.values():
            component.stop()
'''
}

class MediatorToPythonConverter:
    """Mediator到Python的转换器"""
    
    def __init__(self):
        self.env = Environment(loader=DictLoader(templates))
        self._setup_filters()
    
    def _setup_filters(self):
        """设置Jinja2过滤器"""
        
        def python_type_filter(mediator_type):
            """将Mediator类型转换为Python类型"""
            if isinstance(mediator_type, dict):
                type_name = mediator_type.get('name', str(mediator_type))
            elif isinstance(mediator_type, str):
                type_name = mediator_type
            else:
                type_name = str(mediator_type)
            
            # 处理泛型类型 Array[T,size] -> List[T]
            if '[' in type_name and ']' in type_name:
                base_type = type_name.split('[')[0]
                if base_type == 'Array':
                    inner_types = type_name[type_name.find('[')+1:type_name.rfind(']')]
                    element_type = inner_types.split(',')[0].strip()
                    return f'List[{python_type_filter(element_type)}]'
            
            type_mapping = {
                'int': 'int',
                'real': 'float', 
                'bool': 'bool',
                'char': 'str',
                'string': 'str',
                'void': 'None'
            }
            
            return type_mapping.get(type_name, type_name)
        
        def python_statement_filter(stmt):
            """将Mediator语句转换为Python语句"""
            stmt = str(stmt).strip()
            
            # 处理赋值语句
            if ':=' in stmt:
                stmt = stmt.replace(':=', '=')
            
            # 处理布尔值
            stmt = stmt.replace('true', 'True').replace('false', 'False')
            
            # 处理null值
            stmt = stmt.replace('null', 'None')
            
            # 处理sync语句
            if stmt.startswith('sync '):
                port_name = stmt.split()[1]
                stmt = f'# sync {port_name} - communication synchronization'
            
            # 添加适当的缩进
            return '    ' + stmt if not stmt.startswith('    ') else stmt
        
        def python_condition_filter(condition):
            """将Mediator条件转换为Python条件"""
            condition = str(condition).strip()
            
            # 处理布尔运算符
            condition = condition.replace('&&', ' and ').replace('||', ' or ')
            condition = condition.replace('!', 'not ')
            condition = condition.replace('true', 'True').replace('false', 'False')
            condition = condition.replace('null', 'None')
            
            # 处理相等比较
            condition = condition.replace('==', ' == ').replace('!=', ' != ')
            
            # 清理多余空格
            condition = ' '.join(condition.split())
            
            return condition
        
        self.env.filters['python_type'] = python_type_filter
        self.env.filters['python_statement'] = python_statement_filter  
        self.env.filters['python_condition'] = python_condition_filter
    
    def convert_from_ast(self, ast_dict: Dict[str, Any]) -> str:
        """从AST字典直接转换为Python代码"""
        
        # 提取各个部分
        typedefs = ast_dict.get('typedefs', [])
        functions_data = ast_dict.get('functions', [])
        automata_data = ast_dict.get('automata', [])
        systems_data = ast_dict.get('systems', [])
        
        # 转换函数
        converted_functions = []
        for func_dict in functions_data:
            func_code = self._convert_function_from_dict(func_dict)
            converted_functions.append(func_code)
        
        # 转换自动机
        converted_automata = []
        for auto_dict in automata_data:
            auto_code = self._convert_automaton_from_dict(auto_dict)
            converted_automata.append(auto_code)
        
        # 转换系统
        converted_systems = []
        for sys_dict in systems_data:
            sys_code = self._convert_system_from_dict(sys_dict)
            converted_systems.append(sys_code)
        
        # 生成完整程序
        template = self.env.get_template('main.py.j2')
        return template.render(
            typedefs=typedefs,
            functions=converted_functions,
            automata=converted_automata,
            systems=converted_systems
        )
    
    def _convert_function_from_dict(self, func_dict: Dict[str, Any]) -> str:
        """从字典转换函数"""
        template = self.env.get_template('function.py.j2')
        return template.render(**func_dict)
    
    def _convert_automaton_from_dict(self, auto_dict: Dict[str, Any]) -> str:
        """从字典转换自动机"""
        template = self.env.get_template('automaton.py.j2')
        return template.render(**auto_dict)
    
    def _convert_system_from_dict(self, sys_dict: Dict[str, Any]) -> str:
        """从字典转换系统"""
        template = self.env.get_template('system.py.j2')
        return template.render(**sys_dict)

# 示例使用
if __name__ == "__main__":
    converter = MediatorToPythonConverter()
    
    # 示例AST字典
    ast_dict = {
  "automata": [
    {
      "name": "heartbeat_monitor",
      "template_params": ["id"],
      "ports": [
        {"name": "hb", "direction": "in", "type": "msgHeartbeat"},
        {"name": "tick", "direction": "in", "type": "msgTick"},
        {"name": "alarm", "direction": "out", "type": "msgAlarm"}
      ],
      "variables": [
        {"name": "missed", "type": "int", "init_value": "0"},
        {"name": "threshold", "type": "int", "init_value": "3"}
      ],
      "transitions": [
        {
          "guard": "self.ports['hb'] != None",
          "statements": [
            "self.variables['missed'] = 0"
          ]
        },
        {
          "guard": "self.ports['tick'] != None",
          "statements": [
            "self.variables['missed'] = self.variables['missed'] + 1"
          ]
        },
        {
          "guard": "self.variables['missed'] >= self.variables['threshold']",
          "statements": [
            "self.ports['alarm'] = self.template_params['id'].True"
          ]
        }
      ]
    }
  ]
}

    # 转换并输出
    python_code = converter.convert_from_ast(ast_dict)
    print("转换后的Python代码:")
    print("=" * 50)
    print(python_code)