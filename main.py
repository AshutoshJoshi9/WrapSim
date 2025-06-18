import re
import os
import numpy as np
import matplotlib.pyplot as plt
from pyverilog.vparser.parser import parse
import pyverilog.vparser.ast as vast
from tabulate import tabulate
from graphviz import Digraph

class VerilogScanDFT:
    def __init__(self, filepath):
        self.filepath = filepath
        self.modules = []
        self.flipflops = []
        self.scan_flops = []
        self.gates = []
        self.scan_chain = []
        self.module_io = {}  # Updated: now includes signal names
        self.ast = None

    def parse_file(self):
        self.ast, _ = parse([self.filepath])
        print("Parsed netlist file successfully.")
    
    # def extract_design_info(self):
    #     def visit(node):
    #         if isinstance(node, vast.ModuleDef):
    #             self.modules.append(node.name)
    #             input_names = []
    #             output_names = []

    #             for item in node.children():
    #                 if isinstance(item, vast.Decl):
    #                     for decl in item.list:
    #                         if isinstance(decl, vast.Input):
    #                             if isinstance(decl.name, str):
    #                                 input_names.append(decl.name)
    #                             else:
    #                                 input_names.append(decl.name.name)
    #                         elif isinstance(decl, vast.Output):
    #                             if isinstance(decl.name, str):
    #                                 output_names.append(decl.name)
    #                             else:
    #                                 output_names.append(decl.name.name)

    #             self.module_io[node.name] = {
    #                 'input_count': len(input_names),
    #                 'output_count': len(output_names),
    #                 'input_names': input_names,
    #                 'output_names': output_names
    #             }

    #         elif isinstance(node, vast.InstanceList):
    #             for inst in node.instances:
    #                 cell = node.module.lower()
    #                 name = inst.name

    #                 if "sdff" in cell:
    #                     self.scan_flops.append((cell, name))
    #                 elif "dff" in cell:
    #                     self.flipflops.append((cell, name))
    #                 elif any(gate in cell for gate in ['aoi', 'oai', 'and', 'or', 'nand', 'nor', 'xor', 'xnor', 'clkinv']):
    #                     self.gates.append((cell, name))

    #         for c in node.children():
    #             visit(c)

    #     visit(self.ast)

    def extract_design_info(self):
        def visit(node):
            if isinstance(node, vast.ModuleDef):
                self.modules.append(node.name)
                input_names = []
                output_names = []

                for item in node.children():
                    if isinstance(item, vast.Decl):
                        for decl in item.list:
                            if isinstance(decl, vast.Input) or isinstance(decl, vast.Output):
                                signal_base = decl.name if isinstance(decl.name, str) else decl.name.name
                                width = decl.width

                                if width is None:
                                    # Scalar signal
                                    if isinstance(decl, vast.Input):
                                        input_names.append(signal_base)
                                    else:
                                        output_names.append(signal_base)
                                else:
                                    # Vector signal
                                    msb = int(width.msb.value)
                                    lsb = int(width.lsb.value)
                                    bit_range = range(msb, lsb - 1, -1) if msb >= lsb else range(msb, lsb + 1)

                                    expanded = [f"{signal_base}{i}" for i in bit_range]

                                    if isinstance(decl, vast.Input):
                                        input_names.extend(expanded)
                                    else:
                                        output_names.extend(expanded)

                self.module_io[node.name] = {
                    'input_count': len(input_names),
                    'output_count': len(output_names),
                    'input_names': input_names,
                    'output_names': output_names
                }

            elif isinstance(node, vast.InstanceList):
                for inst in node.instances:
                    cell = node.module.lower()
                    name = inst.name

                    if "sdff" in cell:
                        self.scan_flops.append((cell, name))
                    elif "dff" in cell:
                        self.flipflops.append((cell, name))
                    elif any(gate in cell for gate in ['aoi', 'oai', 'and', 'or', 'nand', 'nor', 'xor', 'xnor', 'clkinv']):
                        self.gates.append((cell, name))

            for c in node.children():
                visit(c)

        visit(self.ast)




    def construct_scan_chain(self):
        print("Building scan chain.")
        for idx, (cell, name) in enumerate(self.scan_flops):
            scan_cell = {
                'cell_type': cell,
                'instance': name,
                'SE': 'scan_enable',
                'CK': 'clk',
                'SI': f'scan_in' if idx == 0 else f'scan_out_{idx - 1}',
                'SO': f'scan_out_{idx}'
            }
            self.scan_chain.append(scan_cell)

    def display_summary(self):
        print("\n[ Flip-Flops ]")
        print(tabulate(self.flipflops, headers=["Cell", "Instance"]) or "None")

        print("\n[ Scan Flip-Flops ]")
        print(tabulate(self.scan_flops, headers=["Cell", "Instance"]) or "None")

        print("\n[ Logic Gates ]")
        print(tabulate(self.gates, headers=["Type", "Instance"]) or "None")
        
        print("\n[ Scan Chain Order ]")
        print(tabulate(self.scan_chain, headers="keys") or "None")

        print("\n[ Module I/O Summary ]")
        for mod, io in self.module_io.items():
            print(f"\nModule: {mod}")
            print(f"Inputs ({io['input_count']}): {', '.join(io['input_names']) or 'None'}")
            print(f"Outputs ({io['output_count']}): {', '.join(io['output_names']) or 'None'}")


    def create_schematic(self, output_file="schematic"):
        dot = Digraph(comment="Netlist Schematic")
        # Add scan flip-flops as nodes
        for idx, (cell, name) in enumerate(self.scan_flops):
            dot.node(name, f"{cell}\n{name}", shape="box", style="filled", color="lightblue")
        
        # Add regular flip-flops
        for cell, name in self.flipflops:
            dot.node(name, f"{cell}\n{name}", shape="box", style="filled", color="lightgrey")
        
        # Add gates
        for cell, name in self.gates:
            dot.node(name, f"{cell}\n{name}", shape="ellipse", color="orange")
        
        # Draw scan chain path
        for idx in range(len(self.scan_flops) - 1):
            from_name = self.scan_flops[idx][1]
            to_name = self.scan_flops[idx + 1][1]
            dot.edge(from_name, to_name, label="scan")
        
        # Optionally, add logic connections if you have them
        # (You'd need to parse net connections from the netlist for this)
        
        dot.render(output_file, view=True, format="pdf")  # or format="png"
   
    def run(self):
        self.parse_file()
        self.extract_design_info()
        self.construct_scan_chain()
        self.display_summary()
        self.create_schematic()


if __name__ == "__main__":
    analyzer = VerilogScanDFT("./net.v")
    analyzer.run()