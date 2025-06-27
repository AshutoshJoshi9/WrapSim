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
        self.module_io = {}
        self.wbc_cells = []
        self.ast = None

    def parse_file(self):
        self.ast, _ = parse([self.filepath])
        print("Parsed netlist file successfully.")

    def extract_design_info(self):
        module_defs = set()
        instantiated_modules = set()

        def visit(node):
            if isinstance(node, vast.ModuleDef):
                module_defs.add(node.name)
                self.modules.append(node.name)
                input_names = []
                output_names = []
                print(f"Processing module: {node.name}")

                for item in node.children():
                    if isinstance(item, vast.Decl):
                        print(f"  Found Decl: {type(item)}")
                        for decl in item.list:
                            print(f"    Declaration: {type(decl)} - {decl}")
                            signal_base = decl.name if isinstance(decl.name, str) else decl.name.name
                            width = decl.width
                            print(f"      Signal: {signal_base}, Width: {width}")

                            if width is None:
                                if isinstance(decl, vast.Input):
                                    input_names.append(signal_base)
                                    print(f"      Added input: {signal_base}")
                                elif isinstance(decl, vast.Output):
                                    output_names.append(signal_base)
                                    print(f"      Added output: {signal_base}")
                            else:
                                msb = int(width.msb.value)
                                lsb = int(width.lsb.value)
                                bit_range = range(msb, lsb - 1, -1) if msb >= lsb else range(msb, lsb + 1)
                                expanded = [f"{signal_base}{i}" for i in bit_range]
                                if isinstance(decl, vast.Input):
                                    input_names.extend(expanded)
                                    print(f"      Added input bus: {expanded}")
                                elif isinstance(decl, vast.Output):
                                    output_names.extend(expanded)
                                    print(f"      Added output bus: {expanded}")

                self.module_io[node.name] = {
                    'input_count': len(input_names),
                    'output_count': len(output_names),
                    'input_names': input_names,
                    'output_names': output_names
                }
                print(f"  Module {node.name} I/O: {len(input_names)} inputs, {len(output_names)} outputs")

            elif isinstance(node, vast.InstanceList):
                instantiated_modules.add(node.module)

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

        # Determine top-level module (defined but never instantiated)
        top_candidates = module_defs - instantiated_modules
        top_module = next(iter(top_candidates), None)

        # Add Wrapper Boundary Cells for top-level module only
        excluded_inputs = {'clk', 'reset', 'en'}
        wbc_inputs = ['CFI', 'WINT', 'WEXT', 'WRCK', 'DFT_sdi']
        wbc_outputs = ['CFO', 'DFT_sdo']

        if top_module and top_module in self.module_io:
            print(f"Top-level module identified: {top_module}")
            io = self.module_io[top_module]

            for name in sorted(io['input_names']):
                if name not in excluded_inputs:
                    self.wbc_cells.append({
                        'cell_type': 'WBC',
                        'instance': f'WBC_{name}',
                        'direction': 'input',
                        'signal': name,
                        'inputs': wbc_inputs,
                        'outputs': wbc_outputs
                    })

            for name in sorted(io['output_names']):
                self.wbc_cells.append({
                    'cell_type': 'WBC',
                    'instance': f'WBC_{name}',
                    'direction': 'output',
                    'signal': name,
                    'inputs': wbc_inputs,
                    'outputs': wbc_outputs
                })

    def construct_scan_chain(self):
        print("Building extended scan chain.")

        # Separate and sort WBCs for consistent order
        input_wbcs = sorted(
            [w for w in self.wbc_cells if w['direction'] == 'input'],
            key=lambda x: x['instance']
        )
        output_wbcs = sorted(
            [w for w in self.wbc_cells if w['direction'] == 'output'],
            key=lambda x: x['instance']
        )

        # Combine full scan chain: inputs → all scan FFs (SDFFs and DFFs) → outputs
        full_chain = input_wbcs + [
            {'cell_type': cell, 'instance': name}
            for cell, name in (self.scan_flops + self.flipflops)
        ] + output_wbcs

        self.scan_chain = []

        for idx, element in enumerate(full_chain):
            scan_cell = {
                'cell_type': element['cell_type'],
                'instance': element['instance'],
                'SI': 'scan_in' if idx == 0 else f'scan_out_{idx - 1}',
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

        print("\n[ Extended Scan Chain Order ]")
        print(tabulate(self.scan_chain, headers="keys") or "None")

        print("\n[ Module I/O Summary ]")
        for mod, io in self.module_io.items():
            print(f"\nModule: {mod}")
            print(f"Inputs ({io['input_count']}): {', '.join(io['input_names']) or 'None'}")
            print(f"Outputs ({io['output_count']}): {', '.join(io['output_names']) or 'None'}")

        print("\n[ Wrapper Boundary Cells (WBCs) ]")
        print(tabulate(
            [
                (w['instance'], w['direction'], w['signal'],
                 ', '.join(w['inputs']), ', '.join(w['outputs']))
                for w in self.wbc_cells
            ],
            headers=["Instance", "Direction", "Signal", "Inputs", "Outputs"]
        ) or "None")

    def create_schematic(self, output_file="schematic"):
        dot = Digraph(comment="Netlist Schematic")

        # Flip-flop port definitions
        ff_inputs_sdff = ['RN', 'CK', 'D', 'SI', 'SE']
        ff_outputs_sdff = ['Q', 'QN']
        ff_inputs_dff = ['RN', 'CK', 'D']
        ff_outputs_dff = ['Q', 'QN']

        # Add scan flip-flops (SDFF)
        for cell, name in self.scan_flops:
            label = (
                f"{cell}\n{name}\n"
                f"IN: {', '.join(ff_inputs_sdff)}\n"
                f"OUT: {', '.join(ff_outputs_sdff)}"
            )
            dot.node(name, label, shape="box", style="filled", color="lightblue")

        # Add regular flip-flops (DFF)
        for cell, name in self.flipflops:
            label = (
                f"{cell}\n{name}\n"
                f"IN: {', '.join(ff_inputs_dff)}\n"
                f"OUT: {', '.join(ff_outputs_dff)}"
            )
            dot.node(name, label, shape="box", style="filled", color="lightgrey")

        # Add gates
        for cell, name in self.gates:
            dot.node(name, f"{cell}\n{name}", shape="ellipse", color="orange")

        # Add WBCs
        for w in self.wbc_cells:
            input_ports = ', '.join(w['inputs'])
            output_ports = ', '.join(w['outputs'])
            label = (
                f"{w['cell_type']}\n{w['instance']}\nSignal: {w['signal']}\n"
                f"IN: {input_ports}\nOUT: {output_ports}"
            )
            dot.node(w['instance'], label, shape="octagon", style="filled", color="yellow")

        # Draw extended scan chain path
        for idx in range(len(self.scan_chain) - 1):
            from_cell = self.scan_chain[idx]
            to_cell = self.scan_chain[idx + 1]
            # For DFFRX1, connect Q to D; for SDFF, connect SO to SI
            if from_cell['cell_type'].lower().startswith('dff'):
                from_port = 'Q'
            else:
                from_port = 'SO'
            if to_cell['cell_type'].lower().startswith('dff'):
                to_port = 'D'
            else:
                to_port = 'SI'
            dot.edge(from_cell['instance'], to_cell['instance'], label=f"{from_port}->{to_port}")

        dot.render(output_file, view=True, format="pdf")

    def run(self):
        self.parse_file()
        self.extract_design_info()
        self.construct_scan_chain()
        self.display_summary()
        self.create_schematic()

if __name__ == "__main__":
    analyzer = VerilogScanDFT("./net.v")
    analyzer.run()
