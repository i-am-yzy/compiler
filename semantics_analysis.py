from symbol_table import *
from analysis_tree import *


class SemanticAnalyzer:
    def __init__(self, analysis_tree=AnalysisTree(), st_manager=st_manager()):
        self.result = True  # 分析结果，false or true
        self.tree = analysis_tree  # 分析树
        self.st_manager = st_manager  # 符号表操作

    """
        语法分析过程中分析过的内容在此不做检查
    """

    def S(self):
        """
        S -> programstruct
        不需要进行检查
        """
        current_node_id = self.tree.find_child_node(0, 0).id
        current_node = self.tree.analysis_tree[current_node_id]  # 找到当前节点
        self.programstruct(current_node.child[0])

    def programstruct(self, node_id):
        """
        programstruct -> program_head ; program_body .
        不需要进行检查
        """
        current_node = self.tree.analysis_tree[node_id]
        self.program_head(current_node.child[0])
        self.program_body(current_node.child[2])

    def program_head(self, node_id):
        """
        program_head → program id ( idlist ){parameters=idlist;make_table('main',False,None,parameters)}
        建表，将idlist插入
        program_head → program id{make_table('main',False,None,[])}
        建表
        """
        current_node = self.tree.analysis_tree[node_id]
        parameter_list = []
        if current_node.child_num == 2:
            self.st_manager.make_table('main', parameter_list, False, None)
        elif current_node.child_num == 5:
            parameter_list = self.idlist(current_node.child[3])
            self.st_manager.make_table('main', parameter_list, False, None)
        else:
            self.result = False

    def program_body(self, node_id):
        """
        program_body → const_declarations var_declarations subprogram_declarations compound_statement
        不需要检查
        """
        current_node = self.tree.analysis_tree[node_id]
        self.const_declarations(current_node.child[0])
        self.var_declarations(current_node.child[1])
        self.subprogram_declarations(current_node.child[2])
        self.compound_statement(current_node.child[3])

    def idlist(self, node_id):
        """
        idlist → idlist , id{parameters.append((id.name,id.type))}
        将id和idlist的返回值加入参数表
        idlist → id{parameters.append((id.name,id.type))}
        将id加入参数表
        """
        current_node = self.tree.analysis_tree[node_id]
        parameters = []
        if current_node.child_num == 1:
            child_node = current_node.find_child_node(node_id, 0)
            parameters.append(Parameter(child_node.value, None, child_node.row, child_node.column, False))
        else:
            parameters.extend(self.idlist(current_node.child[0]))
            child_node = current_node.find_child_node(node_id, 2)
            parameters.append(Parameter(child_node.value, None, child_node.row, child_node.column, False))
        return parameters

    """
        常量声明部分
    """

    def const_declarations(self, node_id):
        """
        const_declarations → const const_declaration ;
        const_declarations → ε
        不需要检查
        """
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 3:
            self.const_declaration(current_node.child[1])

    def const_declaration(self, node_id):
        """
        const_declaration → const_declaration ; id relop const_value{insert_item()}
        const_declaration → id relop const_value{insert_item()}
        将标识符id插入符号表
        """
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 3:
            id_node = current_node.find_child_node(node_id, 0)
            relop_node = current_node.find_child_node(node_id, 1)
            const_value_type = self.const_value(current_node.child[2])
        else:
            self.const_declaration(current_node.child[0])
            id_node = current_node.find_child_node(node_id, 2)
            relop_node = current_node.find_child_node(node_id, 3)
            const_value_type = self.const_value(current_node.child[4])

        if relop_node.value != '=':
            print("语义错误：第{0}行, 第{1}列: 常量定义应使用‘=’".format(id_node.row, id_node.column))
            self.result = False
            return

        new_item = Item(id_node.value, "const", const_value_type[0],
                        const_value_type[1], None, [], id_node.row, [])
        if not self.st_manager.insert_item(new_item, self.st_manager.current_table_name):
            print("语义错误：第{0}行, 第{1}列: {2}重定义或该符号表不存在".format(id_node.row, id_node.column, id_node.value))
            self.result = False

    def const_value(self, node_id):
        """
        const_value → addop num{const_value.type=num}
        const_value → num {const_value.type=num}
        const_value → ' letter '{const_value.type=char}
        返回 const_value_type = (value, type)
        """
        current_node = self.tree.analysis_tree[node_id]
        const_value = None
        const_type = None
        if current_node.child_num == 2:  # const_value → addop num{const_value.type=num}
            addop_node = self.tree.find_child_node(node_id, 0)
            num_node = self.tree.find_child_node(node_id, 1)
            if addop_node.value == '+':
                const_value = num_node.value
            elif addop_node.value == '-':
                const_value = num_node.value.__neg__()
            elif addop_node.value == 'or':
                print("语义错误：第{0}行, 第{1}列: or不能给const赋值".format(addop_node.row, addop_node.column))
                const_value_type = (None, None)
                return const_value_type
            if isinstance(const_value, int):
                const_type = 'integer'
            if isinstance(const_value, float):
                const_type = 'real'
        elif current_node.child_num == 1:  # const_value → num {const_value.type=num}
            num_node = self.tree.find_child_node(node_id, 0)
            const_value = num_node.value
            if isinstance(const_value, int):
                const_type = 'integer'
            if isinstance(const_value, float):
                const_type = 'real'
        else:  # const_value → ' letter '{const_value.type=char}
            letter_node = self.tree.find_child_node(node_id, 1)
            const_value = letter_node.value
            const_type = 'char'
        const_value_type = (const_value, const_type)
        return const_value_type

    """
        变量声明部分
    """

    def var_declarations(self, node_id):
        """
        var_declarations → var var_declaration ;
        var_declarations → ε
        不需要检查
        """
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 3:
            self.var_declaration(current_node.child[1])

    def var_declaration(self, node_id):
        """
        var_declaration → var_declaration ; idlist : type{insert_item()}
        var_declaration → idlist : type{insert_item()}
        """
        current_node = self.tree.analysis_tree[node_id]
        parameter_list = []
        if current_node.child_num == 3:  # var_declaration → idlist : type{insert_item()}
            parameter_list = self.idlist(current_node.child[0])
            item_info = self.type(current_node.child[2])
            for parameter in parameter_list:
                new_item = Item(parameter.name, item_info[0], item_info[1],
                                None, None, None, parameter.row, [])
                if not self.st_manager.insert_item(new_item, self.st_manager.current_table_name):
                    print("语义错误：第{0}行, 第{1}列: {2}重定义或该符号表不存在".format(parameter.row, parameter.column, parameter.name))
                    self.result = False
        else:  # var_declaration → var_declaration ; idlist : type{insert_item()}
            self.var_declaration(current_node.child[0])
            parameter_list = self.idlist(current_node.child[2])
            item_info = self.type(current_node.child[4])
            for parameter in parameter_list:
                new_item = Item(parameter.name, item_info[0], item_info[1],
                                None, item_info[3], item_info[2][1], parameter.row, [])
                if not self.st_manager.insert_item(new_item, self.st_manager.current_table_name):
                    print("语义错误：第{0}行, 第{1}列: {2}重定义或该符号表不存在".format(parameter.row, parameter.column, parameter.name))
                    self.result = False

    def type(self, node_id):
        """
        type → basic_type {type.value = basic_type}
        type → array [ period ] of basic_type{type.id = array;type.value = basic_type;
                                            type.demension=period.demension;type.parameters=period.parameters}
        返回值：item_info = [变量类型，元素类型，数组大小(size, period)，数组维数]
        """
        current_node = self.tree.analysis_tree[node_id]
        item_info = []
        if current_node.child_num == 1:
            var_type = self.basic_type(current_node.child[0])
            item_info = ["var", var_type, (None, None), None]
        else:
            array_period = self.period(current_node.child[2])
            array_type = self.basic_type(current_node.child[5])
            size = 0
            for item in array_period:
                size += (item[1] - item[0])
            if len(array_period) > 0:
                item_info = ["array", array_type, (size, array_period), len(array_period)]
        return item_info

    def basic_type(self, node_id):
        """
        basic_type → integer{basic_type=integer}
        basic_type → real {basic_type=real}
        basic_type → boolean {basic_type=boolean}
        basic_type → char{basic_type=char}
        """
        # current_node = self.tree.analysis_tree[node_id]
        child_node = self.tree.find_child_node(node_id, 0)
        return child_node.token

    def period(self, node_id):
        """
        period → period ， num .. num {period.demension++;period.parameters.append()}
        period → num .. num{period.demension++;period.parameters.append()}
        返回值：array_period = [(下限, 上限), ]
        """
        current_node = self.tree.analysis_tree[node_id]
        array_period = []
        if current_node.child_num == 3:
            num_node1 = self.tree.find_child_node(node_id, 0)
            num_node2 = self.tree.find_child_node(node_id, 2)
        else:
            new_array_period = self.period(current_node.child[0])
            if len(new_array_period) != 0:
                array_period.extend(new_array_period)
            num_node1 = self.tree.find_child_node(node_id, 2)
            num_node2 = self.tree.find_child_node(node_id, 4)

        if num_node1.value < 0 or not isinstance(num_node1.value, int):
            print('语义错误：第{0}行, 第{1}列: 数组下标必须为非负整数'.format(num_node1.row, num_node1.column))  # 同时输出行，列
            self.result = False
            return array_period
        if num_node2.value < 0 or not isinstance(num_node2.value, int):
            print('语义错误：第{0}行, 第{1}列: 数组下标必须为非负整数'.format(num_node2.row, num_node2.column))  # 同时输出行，列
            self.result = False
            return array_period
        if num_node1.value > num_node2.value:
            print('语义错误：第{0}行, 第{1}列: 数组上下限错误'.format(num_node2.row, num_node2.column))  # 同时输出行，列
            self.result = False
            return array_period
        array_period.append((num_node1.value, num_node2.value))
        return array_period

    """
        过程、函数声明部分
    """

    def subprogram_declarations(self, node_id):
        """
        subprogram_declarations → subprogram_declarations subprogram ;
        subprogram_declarations → ε
        """
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 3:
            self.subprogram_declarations(current_node.child[0])
            self.subprogram(current_node.child[1])

    def subprogram(self, node_id):
        """
        subprogram → subprogram_head ; subprogram_body
        """
        current_node = self.tree.analysis_tree[node_id]
        self.subprogram_head(current_node.child[0])
        self.subprogram_body(current_node.child[2])

    def subprogram_head(self, node_id):
        """
        subprogram_head → procedure id formal_parameter
                                    {parameters=formal_parameter.list;make_table()}
        subprogram_head → function id formal_parameter : basic_type
                            {parameters=formal_parameter.list;return_type=basic_type;make_table()}
        """
        current_node = self.tree.analysis_tree[node_id]
        id_node = self.tree.find_child_node(node_id, 1)
        subprogram_name = id_node.value
        parameters = self.formal_parameter(current_node.child[2])
        if current_node.child_num == 3:
            self.st_manager.make_table(subprogram_name, parameters, False, None)
            # 新建一个子表，将current_table指向新的子表
        elif current_node.child_num == 5:
            return_type = self.basic_type(current_node.child[4])
            self.st_manager.make_table(subprogram_name, parameters, True, return_type)
            # 新建一个子表，将current_table指向新的子表

    def formal_parameter(self, node_id):
        """
        formal_parameter → ( parameter_list ){formal_parameter.list=parameter_list}
        formal_parameter → ε{formal_parameter.list=[]}
        """
        current_node = self.tree.analysis_tree[node_id]
        parameters = []
        if current_node.child_num == 3:
            parameters = self.parameter_list(current_node.child[1])
        return parameters

    def parameter_list(self, node_id):
        """
        parameter_list → parameter_list ; parameter {parameter_list.append(parameter)}
        parameter_list → parameter{parameter_list.append(parameter)}
        """
        current_node = self.tree.analysis_tree[node_id]
        parameters = []
        if current_node.child_num == 1:
            new_parameters = self.parameter(current_node.child[0])
            if new_parameters is not None:
                parameters.extend(new_parameters)
        elif current_node.child_num == 3:
            new_parameters = self.parameter_list(current_node.child[0])
            if new_parameters is not None:
                parameters.extend(new_parameters)
            new_parameters = self.parameter(current_node.child[2])
            if new_parameters is not None:
                parameters.extend(new_parameters)
        return parameters

    def parameter(self, node_id):
        """
        parameter → var_parameter{parameter=var_parameter}
        parameter → value_parameter{parameter=value_parameter}
        """
        # current_node = self.tree.analysis_tree[node_id]
        child_node = self.tree.find_child_node(node_id, 0)
        parameters = []
        if child_node.token == 'var_parameter':
            parameters = self.var_parameter(child_node.id)
        elif child_node.token == 'value_parameter':
            parameters = self.value_parameter(child_node.id)
        return parameters

    def var_parameter(self, node_id):
        """
        var_parameter → var value_parameter
                            {value_parameter.id='var';var_parameter=value_parameter}
        """
        child_node = self.tree.find_child_node(node_id, 1)
        parameters = self.value_parameter(child_node.id)
        for i, value in enumerate(parameters):
            parameters[i].vary = True
        return parameters

    def value_parameter(self, node_id):
        """
        value_parameter → idlist : basic_type
                                {idlist.type = basic_type;value_parameter=idlist}
        """
        current_node = self.tree.analysis_tree[node_id]
        parameters = self.idlist(current_node.child[0])
        parameter_type = self.basic_type(current_node.child[2])
        for i, value in enumerate(parameters):
            parameters[i].type = parameter_type
        return parameters

    """
        程序体部分
    """

    def subprogram_body(self, node_id):
        """
        subprogram_body → const_declarations var_declarations compound_statement
        """
        current_node = self.tree.analysis_tree[node_id]
        self.const_declarations(current_node.child[0])
        self.var_declarations(current_node.child[1])
        self.compound_statement(current_node.child[2])

    def compound_statement(self, node_id):
        """
        compound_statement → begin statement_list end
        """
        current_node = self.tree.analysis_tree[node_id]
        self.statement_list(current_node.child[1])

    def statement_list(self, node_id):
        """
        statement_list → statement_list ; statement
        statement_list → statement
        """
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 1:
            self.statement(current_node.child[0])
        elif current_node.child_num == 3:
            self.statement_list(current_node.child[0])
            self.statement(current_node.child[2])

    def statement(self, node_id):
        """
        statement → variable assignop expression
        statement → procedure_call
        statement → compound_statement
        statement → if expression then statement else_part
        statement → for id assignop expression to expression do statement
        statement → read ( variable_list ) {search_item()???为什么不在收集上来之前测试}
        statement → write ( expression_list ){search_item()???为什么不在收集上来之前测试}
        statement → ε
        """
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 1:
            child_node = self.tree.find_child_node(node_id, 0)
            if child_node.token == "procedure_call":
                self.procedure_call(child_node.id)
            elif child_node.token == "compound_statement":
                self.compound_statement(child_node.id)

        elif current_node.child_num == 3:
            variable = self.variable(current_node.child[0])
            return_type = self.expression(current_node.child[3])
            if len(variable) == 0 or len(return_type) == 0:
                return
            result_item = self.st_manager.search_item(variable[0], self.st_manager.current_table_name)
            if result_item != None:
                if variable[1] == 'array':
                    variable[1] = variable[4]
                if variable[1] == return_type[1]:
                    pass
                elif variable[1] == 'real' and return_type[1] == 'integer':
                    print('语义错误：第{0}行, 第{1}列: 尝试将integer型的值赋给一个real型的变量'.format(variable[2], variable[3]))
                    self.result = False
                elif variable[1] == 'integer' and return_type[1] == 'real':
                    print('语义错误：第{0}行, 第{1}列: 尝试将real型的值赋给一个int型的变量'.format(variable[2], variable[3]))
                    self.result = False
                else:
                    # print(return_type[1])
                    # print(variable[1])
                    print('语义错误：第{0}行, 第{1}列: 变量类型不匹配，无法赋值'.format(variable[2], variable[3]))
                    self.result = False
            else:
                print('语义错误：第{0}行, 第{1}列: 变量未定义'.format(variable[2], variable[3]))
                self.result = False
            '''
            if variable isdefined:
                if variable.type == return_type:
                    成功
                else:
                    报错 result = false
            else:
                报错 result = false
            '''

        elif current_node.child_num == 4:  # statement → read ( variable_list ) {search_item()???为什么不在收集上来之前测试}
            # statement → write ( expression_list ){search_item()???为什么不在收集上来之前测试}
            child_node = self.tree.find_child_node(node_id, 0)
            if child_node.token == 'read':
                variable_list = self.variable_list(current_node.child[2])
                if len(variable_list) != 0:
                    for item in variable_list:
                        result_item = self.st_manager.search_item(item[0], self.st_manager.current_table_name)
                        if result_item == None:
                            print('语义错误：第{0}行, 第{1}列: 变量{2}未定义'.format(item[2], item[3], item[0]))
                            self.result = False
                        else:
                            result_item.used_row.append(item[2])
            elif child_node.token == 'write':
                expression_list = self.expression_list(current_node.child[2])
                if len(expression_list) != 0:
                    for item in expression_list:
                        if item[0] != 'expression':
                            result_item = self.st_manager.search_item(item[0], self.st_manager.current_table_name)
                            if result_item == None:
                                print('语义错误：第{0}行, 第{1}列: 变量{2}未定义'.format(item[2], item[3], item[0]))
                                self.result = False
                            else:
                                result_item.used_row.append(item[2])
                        else:  # 如果是expression
                            pass

        elif current_node.child_num == 5:
            return_type = self.expression(current_node.child[1])  # if a then b: a 应该为boolean表达式
            if len(return_type) == 0:
                self.result = False
            elif return_type[1] != 'boolean':
                print('语义错误：第{0}行: if A then B：A 应该为布尔表达式'.format(self.tree.find_child_node(node_id, 0).row))
                # 选择 if 那一行
                self.result == False
            self.statement(current_node.child[3])
            self.else_part(current_node.child[4])
        elif current_node.child_num == 8:
            id_node = self.tree.find_child_node(node_id, 1)
            child_assignop = self.tree.find_child_node(node_id, 2)
            return_type1 = self.expression(current_node.child[3])  # 第一个expression
            return_type2 = self.expression(current_node.child[5])  # 第二个expression
            result_item = self.st_manager.search_symbol_table(id_node.value, self.st_manager.current_table_name)
            if result_item == None:
                print("语义错误：第{0}行, 第{1}列: id未定义".format(id_node.row, id_node.column))
                self.result = False
            if result_item != None and len(return_type1) != 0 and len(return_type2) != 0:
                result_item.used_row.append(id_node.row)
                if result_item.value_type == 'integer' and return_type1[1] == 'integer' and return_type2[
                    1] == 'integer':
                    self.statement(current_node.child[7])
                else:
                    print('语义错误：第{0}行: for 语句中，迭代变量类型应为integer'.format(id_node.row))  # 选择id 那一行
                    self.result = False
            else:
                self.result = False
            '''
            if id_node.value is_defined：
                if (return_type1 == int && return_type2 == int) or 
                   (return_type == char and return_type2 == char):
                    if return_type1 = id.type:
                        才进行statement
            else：
                报错
            '''

        else:
            pass  # 可能有错误处理

    def variable_list(self, node_id):
        """
        variable_list → variable_list , variable {variable_list.append()}
        variable_list → variable{variable_list.append()}
        返回id_list = [[id名，类型，行，列, 数组值的类型(不是数组，则为None)], ]
        """
        current_node = self.tree.analysis_tree[node_id]
        id_list = []
        if current_node.child_num == 3:
            if len(id_list) != 0:
                id_list.extend(self.variable_list(current_node.child[0]))
            id_list.append(self.variable(current_node.child[2]))
        elif current_node.child_num == 1:
            id_list.append(self.variable(current_node.child[0]))
        else:
            pass  # 可能进行错误处理
        return id_list

    def variable(self, node_id):
        """
        variable → id id_varpart{search_item();可能需要数组越界检查}
        返回 [id名，类型，行，列, 数组值的类型(不是数组，则为None)]
        """
        variable = []
        current_node = self.tree.analysis_tree[node_id]
        id_node = self.tree.find_child_node(node_id, 0)
        id_node_varpart = self.tree.find_child_node(node_id, 1)
        current_item = self.st_manager.search_symbol_table(id_node.value, self.st_manager.current_table_name)
        if current_item != None:
            current_item.used_row.append(id_node.row)
            # identifier_type = {'function', 'procedure', 'program'}
            # if current_item.identifier_type not in identifier_type:
            self.id_varpart(current_node.child[1])
            if current_item.identifier_type == 'array':
                if id_node_varpart.child_num == 3:
                    variable = [current_item.name, 'array', id_node.row, id_node.column, current_item.value_type]
                else:
                    print("语义错误：第{0}行, 第{1}列: 无法对数组名进行操作".format(id_node.row, id_node.column))
                    self.result = False
            else:
                variable = [current_item.name, current_item.value_type, id_node.row, id_node.column, None]
            # else:
            #     print('id不应该是一个过程或者函数')
            #     self.result = False
        else:
            print("语义错误：第{0}行, 第{1}列: {2}未定义".format(id_node.row, id_node.column, id_node.value))
            self.result = False
        # 这里应该直接判断是否定义，如果未定义报错,直接不分析id_varpart
        # 可以直接查到id的类型, 如果id表示的是一个过程或者函数，也报错
        return variable

    def id_varpart(self, node_id):
        """
        id_varpart → [ expression_list ] {id_varpart=expression_list}
        id_varpart → ε
        """
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 3:
            expression_list = self.expression_list(current_node.child[1])
            if len(expression_list) != 0:
                for expression in expression_list:
                    if expression[1] != 'integer':
                        print('语义错误：第{0}行: 数组下标应该为integer'.format(self.tree.find_child_node(node_id, 0).row))
                        self.result = False
            '''
            如果是返回值，则判断类型是不是int
            如果是id，是不是int
            不是，报错
            '''

    def procedure_call(self, node_id):
        """
        procedure_call → id
        procedure_call → id ( expression_list ){id=search_item();传参判定}
        """

    def else_part(self, node_id):
        """
        else_part → else statement
        else_part → ε
        """

    def expression_list(self, node_id):
        """
        expression_list → expression_list , expression {expression_list.append()}
        expression_list → expression{expression_list.append()}
        返回expression_list = [[id, type, row, column],
                              [expression, return_type, None, None],
                              #[array, element_type, id的行，id的列] 可以不要#]
        """
        current_node = self.tree.analysis_tree[node_id]
        expression_list = []
        if current_node.child_num == 3:
            expression_list = self.expression_list(current_node.child[0])
            result = self.expression(current_node.child[2])
            if len(result) != 0:
                expression_list.append(self.expression(current_node.child[2]))
        elif current_node.child_num == 1:
            result = self.expression(current_node.child[0])
            if len(result) != 0:
                expression_list.append(self.expression(current_node.child[0]))
        return expression_list

    def expression(self, node_id):
        """
        expression → simple_expression relop simple_expression{逻辑判断决定赋值}
        expression → simple_expression{expression.type = simple_expression.type}
        返回：[expression, return_type, None, None] or
              [id, type, row, column] or \n
              # [array, element_type, id的行，id的列] 这个可以不要
        """
        expression = []
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 3:
            se1 = self.simple_expression(current_node.child[0])
            se2 = self.simple_expression(current_node.child[2])
            relop_node = self.tree.find_child_node(node_id, 1)  # 可能有一些操作
            if len(se1) != 0 and len(se2) != 0:
                if se1[1] == se2[1]:
                    if se1[1] == 'integer' or se1[1] == 'real':
                        expression = ['expression', 'boolean', relop_node.row, relop_node.column]  # 这里使用relop的 行 列
                    else:
                        print('语义错误：第{0}行: 该类型无法比较'.format(relop_node.row))  # 这里使用relop的 行
                        self.result = False
                else:
                    print("语义错误：第{0}行: 类型不一样，无法比较".format(relop_node.row))  # 这里使用relop 的行
                    self.result = False
            '''
            检查两个simple_expression是否类型可以比较，
            如果可以则返回值类型为 boolean
            '''
        elif current_node.child_num == 1:
            expression = self.simple_expression(current_node.child[0])
        else:
            pass  # 可能进行错误处理
        return expression

    def simple_expression(self, node_id):
        """
        simple_expression → simple_expression addop term {逻辑判断决定赋值}
        simple_expression → term{simple_expression.type = term.type}
        返回[id, type, row, column] or # [array, item_type, id的行, id的列] 这个可以不要
            or [expression, return_type, None, None]
        """
        simple_expression = []
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 3:
            sub_simple_expressipon = self.simple_expression(current_node.child[0])
            child_addop = self.tree.find_child_node(node_id, 1)  # 可能要用到该属性
            # or的类型检查
            sub_term = self.term(current_node.child[2])
            if len(sub_simple_expressipon) != 0 and len(sub_term) != 0:
                if sub_simple_expressipon[1] == sub_term[1]:
                    if child_addop.value != 'or':
                        if sub_term[1] == 'integer' or sub_term[1] == 'real':
                            simple_expression = ['expression', sub_term[1], child_addop.row,
                                                 child_addop.column]  # 这里使用addop的行，列
                        else:
                            print("语义错误：第{0}行: 类型不匹配，无法执行addop操作".format(child_addop.row))  # 这里使用addop的行
                            self.result = False
                    else:
                        if sub_term[1] == 'integer' or sub_term[1] == 'boolean':
                            simple_expression = ['expression', sub_term[1], child_addop.row,
                                                 child_addop.column]  # 这里使用addop的行，列
                        else:
                            print("语义错误：第{0}行: 类型不匹配，无法执行 or 操作".format(child_addop.row))  # 这里使用addop的行
                            self.result = False
                else:
                    if child_addop.value != 'or':
                        if sub_term[1] == 'integer' and sub_simple_expressipon[1] == 'real':
                            simple_expression = ['expression', 'real', child_addop.row, child_addop.column]
                        elif sub_term[1] == 'real' and sub_simple_expressipon[1] == 'integer':
                            simple_expression = ['expression', 'real', child_addop.row, child_addop.column]
                        else:
                            print("语义错误：第{0}行: 类型不匹配，无法执行addop操作".format(child_addop.row))  # 这里使用addop的行
                            self.result = False
                    else:
                        print("语义错误：第{0}行: 类型不匹配，无法执行addop操作".format(child_addop.row))  # 这里使用addop的行
                        self.result = False
            '''
            判断两个是否能够addop，
            如果能simple_expression = ['expression', type, None, None]，否则，为空
            可能涉及到一些类型转换，例如int转real之类的
            '''
        elif current_node.child_num == 1:
            simple_expression = self.term(current_node.child[0])
        else:
            pass  # 可能进行错误处理
        return simple_expression

    def term(self, node_id):
        """
        term → term mulop factor{逻辑判断决定赋值}
        term → factor{term.type = factor.type}
        返回[id, type, row, column] or [array, item_type, id的行, id的列]
            or [expression, return_type, None, None]
        """
        term = []
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 3:
            sub_term = self.term(current_node.child[0])
            mulop_node = self.tree.find_child_node(node_id, 1)  # 可能要用到
            sub_factor = self.factor(current_node.child[2])
            mulop_set = {'*', '/', 'div', 'mod', 'and'}
            if len(sub_factor) != 0 and len(sub_term) != 0:
                if sub_term[1] == sub_factor[1]:
                    if sub_term[1] == "integer":
                        if mulop_node.value == '/':
                            term = ["expression", "real", mulop_node.row, mulop_node.column]  # 这里使用的 mulop 的行列
                        elif mulop_node.value == '*' or mulop_node.value == 'div' or mulop_node == 'mod':
                            term = ["expression", "integer", mulop_node.row, mulop_node.column]  # 这里使用的 mulop 的行列
                        else:
                            print('语义错误：第{0}行: integer类型不能进行and运算'.format(mulop_node.row))
                            self.result = False
                    elif sub_term[1] == "real":
                        if mulop_node.value == '*' or mulop_node.value == '/':
                            term = ["expression", "real", mulop_node.row, mulop_node.column]  # 这里使用的 mulop 的行列
                        else:
                            print('语义错误：第{0}行: real类型不能进行{1}运算'.format(mulop_node.row, mulop_node.value))
                            self.result = False
                    elif sub_term[1] == "boolean":
                        if mulop_node.value == 'and':
                            term = ["expression", "boolean", mulop_node.row, mulop_node.column]  # 这里使用的 mulop 的行列
                        else:
                            print('语义错误：第{0}行: boolean类型不能进行{1}运算'.format(mulop_node.row, mulop_node.value))
                            self.result = False
                    else:
                        print('语义错误：第{0}行: char类型不能进行{1}运算'.format(mulop_node.row, mulop_node.value))
                        self.result = False
                else:
                    '''
                    判断是否能够做运算。
                    如果可能，则要做强制类型转换，例如int转real
                    '''
                    if (sub_term[1] == "integer" and sub_factor[1] == "real") or \
                            (sub_term[1] == "real" and sub_factor[1] == "integer"):
                        if mulop_node.value == '*' or mulop_node.value == '/':
                            term = ["expression", "real", mulop_node.row, mulop_node.column]  # 这里使用的 mulop 的行列
                        else:
                            print('语义错误：第{0}行: 该类型不能进行{1}运算'.format(mulop_node.row, mulop_node.value))
                            self.result = False
                    else:
                        print('语义错误：第{0}行: 该类型不能进行{1}运算'.format(mulop_node.row, mulop_node.value))
                        self.result = False
        elif current_node.child_num == 1:
            term = self.factor(current_node.child[0])
        return term

    def factor(self, node_id):
        """
        factor → num {factor.type = num.type}
        factor → variable {factor.type = variable.type}
        factor → id ( expression_list ){id.type=search_item();传参判定;factor.type = id.type}
        factor → ( expression ) {factor.type = expression.type}
        factor → not factor {factor.type = factor1.type}
        factor → uminus factor {factor.type = factor1.type}
        返回[id, type, row, column] or [array, item_type, id的行, id的列]
            or [expression, return_type, None, None]
        """
        factor = []
        current_node = self.tree.analysis_tree[node_id]
        if current_node.child_num == 1:
            child_node = self.tree.find_child_node(node_id, 0)
            if child_node.token == "num":
                if isinstance(current_node.value, int):
                    child_type = "integer"
                else:  # num只可能出现int、real两种类型
                    child_type = "real"
                factor = ["expression", child_type, child_node.row, child_node.column]
            elif child_node.token == "variable":
                variable = self.variable(child_node.id)
                if len(variable) != 0:
                    if variable[1] == "array":
                        factor = [variable[0], variable[4], variable[2], variable[3]]
                    else:
                        factor = [variable[0], variable[1], variable[2], variable[3]]
        elif current_node.child_num == 4:
            '''
            检查id是否是一个函数或者过程，是否定义
            如果未定义直接报错，然后直接return
            还要在这里进行引用行填写
            要分析expression_list的参数类型以及个数，是否符合要求
            '''
            id_node = self.tree.find_child_node(node_id, 0)
            result_item = self.st_manager.search_item(id_node.value, self.st_manager.current_table_name)
            if result_item is not None:
                result_item.used_row.append(id_node.row)  # TODO:需要将result更新回符号表
                if result_item.identifier_type == "function" or result_item.identifier_type == "procedure":
                    expression_list = self.expression_list(current_node.child[2])
                    args = []
                    if len(expression_list) != 0:
                        for expression in expression_list:
                            args.append(expression[1])
                    return_type = self.st_manager.complare_args(id_node.value, args)  # TODO:comolare_args函数未完成
                    if not return_type:
                        print("语义错误：第{0}行, 第{1}列: 参数值不匹配".format(id_node.row, id_node.column))  # 在id行报错
                        self.result = False
                    else:
                        factor = ["expression", return_type, id_node.row, id_node.column]  # 行，列是 id的行列

                else:
                    print("语义错误：第{0}行, 第{1}列: id不是一个函数或者过程".format(id_node.row, id_node.column))  # 在id行报错
                    self.result = False
            else:
                print("语义错误：第{0}行, 第{1}列: id未定义".format(id_node.row, id_node.column))  # 在id行报错
                self.result = False
        elif current_node.child_num == 3:
            expression = self.expression(current_node.child[1])
            if len(expression) != 0:
                factor = ["expression", expression[1], expression[2], expression[3]]
        elif current_node.child_num == 2:
            child_node = self.tree.find_child_node(node_id, 0)
            if child_node.token == "not":
                sub_factor = self.factor(current_node.child[1])
                if len(sub_factor) != 0:
                    if sub_factor[1] == "boolean" or sub_factor[1] == "integer":
                        factor = ["expression", sub_factor[1], child_node.row, child_node.column]  # row,column为not的那一行
                    else:
                        print("语义错误：第{0}行, 第{1}列: {2}类型不能使用 not 运算".format(child_node.row, 
                                                                           child_node.column, sub_factor[1]))
                        self.result = False
            elif child_node.token == "uminus":
                sub_factor = self.factor(current_node.child[1])
                if len(sub_factor) != 0:
                    if sub_factor[1] == "integer" or sub_factor[1] == "real":
                        factor = ["expression", sub_factor[1], child_node.row, child_node.column]
                    else:
                        print("语义错误：第{0}行, 第{1}列: {2}类型无法进行uminus操作".format(child_node.row,
                                                                            child_node.column, sub_factor[1]))
                        self.result = False
        return factor
