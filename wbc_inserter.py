from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
import pyverilog.vparser.ast as vast


class WBCInserter:
    def __init__(self, filepath):
        self.filepath = filepath
        self.ast = None
        self.modified_ast = None

    def parse(self):
        self.ast, _ = parse([self.filepath])
        print("[WBCInserter] Parsed input netlist.")

    def add_wbcs(self):
        top_module = None
        for item in self.ast.description.definitions:
            if isinstance(item, vast.ModuleDef):
                top_module = item
                break

        if not top_module:
            raise ValueError("Top-level module not found.")

        input_wbcs = []
        output_wbcs = []

        for port in top_module.portlist.ports:
            if isinstance(port, vast.Ioport):
                if isinstance(port.first, vast.Input):
                    inst_name = f"WBC_in_{port.first.name}"
                    input_wbcs.append(vast.Instance(
                        "InputWBC", inst_name, [], []
                    ))
                elif isinstance(port.first, vast.Output):
                    inst_name = f"WBC_out_{port.first.name}"
                    output_wbcs.append(vast.Instance(
                        "OutputWBC", inst_name, [], []
                    ))

        # Append WBCs to module
        if input_wbcs:
            top_module.items.append(
                vast.InstanceList("InputWBC", [], input_wbcs)
            )
        if output_wbcs:
            top_module.items.append(
                vast.InstanceList("OutputWBC", [], output_wbcs)
            )

        self.modified_ast = self.ast
        print("[WBCInserter] Added WBCs to top-level ports.")

    def generate_new_netlist(self, output_path="net_wbc.v"):
        codegen = ASTCodeGenerator()
        verilog_code = codegen.visit(self.modified_ast)
        with open(output_path, "w") as f:
            f.write(verilog_code)
        print(f"[WBCInserter] Wrote modified netlist to: {output_path}")
