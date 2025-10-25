# piler.py
import ast
import inspect

MATH_FUNC_MAP = {
    'sin':'sin','cos':'cos','tan':'tan','asin':'asin','acos':'acos',
    'atan':'atan','atan2':'atan2','sinh':'sinh','cosh':'cosh','tanh':'tanh',
    'exp':'exp','log':'log','log10':'log10','sqrt':'sqrt','fabs':'fabs',
    'pow':'pow','ceil':'ceil','floor':'floor','fmod':'fmod','hypot':'hypot',
    'round':'round',
}

def generate_c_from_func(py_func):
    """Convert Python function into C code with long double/long long, supports args and 32x unrolled loops."""
    source = inspect.getsource(py_func)
    tree = ast.parse(source)

    def indent(s, level=1):
        return '\n'.join('    '*level + line for line in s.splitlines())

    def ast_to_c(node):
        if isinstance(node, ast.FunctionDef):
            params = [f"long double {a.arg}" for a in node.args.args]
            param_str = ', '.join(params)
            body = '\n'.join(ast_to_c(n) for n in node.body)
            return f"long double {node.name}({param_str}) {{\n{indent(body)}\n}}"

        elif isinstance(node, ast.Return):
            return f"return {ast_to_c(node.value)};"

        elif isinstance(node, ast.Assign):
            targets = ', '.join(ast_to_c(t) for t in node.targets)
            return f"long double {targets} = {ast_to_c(node.value)};"

        elif isinstance(node, ast.AugAssign):
            op_map = {ast.Add:'+=', ast.Sub:'-=', ast.Mult:'*=', ast.Div:'/='}
            if isinstance(node.op, ast.Pow):
                return f"{ast_to_c(node.target)} = pow({ast_to_c(node.target)}, {ast_to_c(node.value)});"
            return f"{ast_to_c(node.target)} {op_map[type(node.op)]} {ast_to_c(node.value)};"

        elif isinstance(node, ast.BinOp):
            op_map = {ast.Add:'+', ast.Sub:'-', ast.Mult:'*', ast.Div:'/', ast.Mod:'%', ast.Pow:'pow'}
            if isinstance(node.op, ast.Pow):
                return f"pow({ast_to_c(node.left)}, {ast_to_c(node.right)})"
            return f"{ast_to_c(node.left)} {op_map[type(node.op)]} {ast_to_c(node.right)}"

        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return f"{node.value}L"
            raise NotImplementedError(f"Unsupported constant type: {type(node.value)}")

        elif isinstance(node, ast.Name):
            return node.id

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    obj_name, func_name = node.func.value.id, node.func.attr
                    if obj_name == 'math' and func_name in MATH_FUNC_MAP:
                        args = ', '.join(ast_to_c(a) for a in node.args)
                        return f"{MATH_FUNC_MAP[func_name]}({args})"
                raise NotImplementedError(f"Unsupported attribute call: {ast.dump(node)}")
            args = ', '.join(ast_to_c(a) for a in node.args)
            return f"{ast_to_c(node.func)}({args})"

        elif isinstance(node, ast.For):
            target = ast_to_c(node.target)
            iter_ = node.iter
            if isinstance(iter_, ast.Call) and isinstance(iter_.func, ast.Name) and iter_.func.id == 'range':
                # Parse range args
                if len(iter_.args) == 1:
                    start, stop = '0', ast_to_c(iter_.args[0])
                elif len(iter_.args) == 2:
                    start, stop = ast_to_c(iter_.args[0]), ast_to_c(iter_.args[1])
                else:
                    start, stop = ast_to_c(iter_.args[0]), ast_to_c(iter_.args[1])
                step = '32'  # UNROLLED 32×

                body = '\n'.join(ast_to_c(b) for b in node.body)
                unrolled = []
                for u in range(32):
                    unrolled.append(
                        body.replace(f"{target}", f"({target}+{u})")
                    )
                unrolled_code = '\n'.join(unrolled)

                return f"for (long long {target} = {start}; {target} < {stop}; {target} += {step}) {{\n{indent(unrolled_code)}\n}}"

            raise NotImplementedError("Only range() is supported in for-loops.")

        elif isinstance(node, ast.Expr):
            return ast_to_c(node.value) + ";"
        
        elif isinstance(node, ast.While):
            test = ast_to_c(node.test)
            body = '\n'.join(ast_to_c(b) for b in node.body)
            return f"while({test}) {{\n{indent(body)}\n}}"

        elif isinstance(node, ast.UnaryOp):
            op_map = {ast.USub:'-', ast.UAdd:'+'}
            return op_map[type(node.op)] + ast_to_c(node.operand)

        elif isinstance(node, ast.If):
            test = ast_to_c(node.test)
            body = '\n'.join(ast_to_c(b) for b in node.body)
            orelse = '\n'.join(ast_to_c(b) for b in node.orelse)
            return f"if({test}) {{\n{indent(body)}\n}}" + (f" else {{\n{indent(orelse)}\n}}" if orelse else "")

        elif isinstance(node, ast.Compare):
            left = ast_to_c(node.left)
            ops = {ast.Lt:'<', ast.LtE:'<=', ast.Gt:'>', ast.GtE:'>=', ast.Eq:'==', ast.NotEq:'!='}
            comparisons = []
            for op, comp in zip(node.ops, node.comparators):
                comparisons.append(f"{left} {ops[type(op)]} {ast_to_c(comp)}")
                left = ast_to_c(comp)
            return ' && '.join(comparisons)

        else:
            raise NotImplementedError(
                f"Sorry! This function can't run in SimplerJIT because it uses unsupported Python features: {type(node)}"
            )

    return "#include <stdio.h>\n#include <math.h>\n" + ast_to_c(tree.body[0])
