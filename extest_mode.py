# extest_mode.py

import re
import os
import numpy as np
import matplotlib.pyplot as plt
from pyverilog.vparser.parser import parse
import pyverilog.vparser.ast as vast
from tabulate import tabulate
from graphviz import Digraph

class ExtestModeDFT:
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
        
        #Extest-specific attributes
        self.main_core = None
        self.left_core = None
        self.right_core = None
        self.extest_scan_chain = []

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

        #determine top-level module (defined but never instantiated)
        top_candidates = module_defs - instantiated_modules
        top_module = next(iter(top_candidates), None)

        #add the Wrapper Boundary Cells for top-level module only (main core)
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

    def initialize_three_cores(self):
        """
        Initialize three cores for Extest Mode:
        1. Main core (with WBCs) - the core under test
        2. Left core (without WBCs) - additional core
        3. Right core (without WBCs) - additional core
        """
        print("\n=== Initializing Three Cores for Extest Mode ===")
        
        #main core (with WBCs) - same as intest mode
        self.main_core = {
            'name': 'main_core',
            'has_wbcs': True,
            'flipflops': self.flipflops.copy(),
            'scan_flops': self.scan_flops.copy(),
            'gates': self.gates.copy(),
            'wbc_cells': self.wbc_cells.copy()
        }
        
        #left core (without WBCs) - just the internal logic
        self.left_core = {
            'name': 'left_core',
            'has_wbcs': False,
            'flipflops': [(cell, f"left_{name}") for cell, name in self.flipflops],
            'scan_flops': [(cell, f"left_{name}") for cell, name in self.scan_flops],
            'gates': [(cell, f"left_{name}") for cell, name in self.gates],
            'wbc_cells': []
        }
        
        #right core (without WBCs) - just the internal logic
        self.right_core = {
            'name': 'right_core',
            'has_wbcs': False,
            'flipflops': [(cell, f"right_{name}") for cell, name in self.flipflops],
            'scan_flops': [(cell, f"right_{name}") for cell, name in self.scan_flops],
            'gates': [(cell, f"right_{name}") for cell, name in self.gates],
            'wbc_cells': []
        }
        
        print(f"Main core: {len(self.main_core['flipflops'])} DFFs, {len(self.main_core['scan_flops'])} SDFFs, {len(self.main_core['gates'])} gates, {len(self.main_core['wbc_cells'])} WBCs")
        print(f"Left core: {len(self.left_core['flipflops'])} DFFs, {len(self.left_core['scan_flops'])} SDFFs, {len(self.left_core['gates'])} gates, {len(self.left_core['wbc_cells'])} WBCs")
        print(f"Right core: {len(self.right_core['flipflops'])} DFFs, {len(self.right_core['scan_flops'])} SDFFs, {len(self.right_core['gates'])} gates, {len(self.right_core['wbc_cells'])} WBCs")

    def construct_extest_scan_chain(self):
        """
        Construct scan chain for Extest Mode:
        Only includes WBCs from the main core (no internal flip-flops)
        Order: WBC_in[0] -> WBC_in[1] -> ... -> WBC_out[0] -> WBC_out[1] -> ...
        """
        print("\n=== Constructing Extest Scan Chain ===")
        
        #separate input and output WBCs for consistent ordering
        input_wbcs = sorted(
            [w for w in self.main_core['wbc_cells'] if w['direction'] == 'input'],
            key=lambda x: x['instance']
        )
        output_wbcs = sorted(
            [w for w in self.main_core['wbc_cells'] if w['direction'] == 'output'],
            key=lambda x: x['instance']
        )
        
        #extest scan chain: only WBCs, no internal flip-flops
        wbc_chain = input_wbcs + output_wbcs
        
        self.extest_scan_chain = []
        
        for idx, wbc in enumerate(wbc_chain):
            scan_cell = {
                'cell_type': wbc['cell_type'],
                'instance': wbc['instance'],
                'direction': wbc['direction'],
                'signal': wbc['signal'],
                'SI': 'extest_scan_in' if idx == 0 else f'extest_scan_out_{idx - 1}',
                'SO': f'extest_scan_out_{idx}'
            }
            self.extest_scan_chain.append(scan_cell)
        
        print(f"Extest scan chain length: {len(self.extest_scan_chain)}")
        print("Extest scan chain order:")
        for i, cell in enumerate(self.extest_scan_chain):
            print(f"  {i+1}. {cell['instance']} ({cell['direction']}) - {cell['signal']}")

    def display_extest_summary(self):
        print("\n=== EXTEST MODE SUMMARY ===")
        
        print("\n[ Main Core (with WBCs) ]")
        print(f"Flip-flops: {len(self.main_core['flipflops'])}")
        print(f"Scan Flip-flops: {len(self.main_core['scan_flops'])}")
        print(f"Logic Gates: {len(self.main_core['gates'])}")
        print(f"WBCs: {len(self.main_core['wbc_cells'])}")
        
        print("\n[ Left Core (without WBCs) ]")
        print(f"Flip-flops: {len(self.left_core['flipflops'])}")
        print(f"Scan Flip-flops: {len(self.left_core['scan_flops'])}")
        print(f"Logic Gates: {len(self.left_core['gates'])}")
        print(f"WBCs: {len(self.left_core['wbc_cells'])}")
        
        print("\n[ Right Core (without WBCs) ]")
        print(f"Flip-flops: {len(self.right_core['flipflops'])}")
        print(f"Scan Flip-flops: {len(self.right_core['scan_flops'])}")
        print(f"Logic Gates: {len(self.right_core['gates'])}")
        print(f"WBCs: {len(self.right_core['wbc_cells'])}")
        
        print("\n[ Extest Scan Chain (WBCs only) ]")
        print(tabulate(self.extest_scan_chain, headers="keys") or "None")

    def create_extest_schematic(self, output_file="extest_schematic"):
        """
        Create schematic showing three cores and extest scan chain, and show connections from WBCs to left/right core flip-flops.
        """
        dot = Digraph(comment="Extest Mode Schematic")
        
        #Set graph attributes for better layout
        dot.attr(rankdir='LR')
        
        #create subgraphs for each core
        with dot.subgraph(name='cluster_left') as left:
            left.attr(label='Left Core (No WBCs)', style='filled', color='lightgrey')
            left.attr(rank='same')
            # Add left core DFFs
            for cell, name in self.left_core['flipflops']:
                label = f"{cell}\n{name}"
                left.node(name, label, shape="box", style="filled", color="lightgrey")
            # Add left core SDFFs
            for cell, name in self.left_core['scan_flops']:
                label = f"{cell}\n{name}"
                left.node(name, label, shape="box", style="filled", color="lightgreen")
            # Add left core gates
            for cell, name in self.left_core['gates']:
                left.node(name, f"{cell}\n{name}", shape="ellipse", color="orange")
        
        with dot.subgraph(name='cluster_main') as main:
            main.attr(label='Main Core (with WBCs)', style='filled', color='lightblue')
            main.attr(rank='same')
            #aadd main core DFFs
            for cell, name in self.main_core['flipflops']:
                label = f"{cell}\n{name}"
                main.node(name, label, shape="box", style="filled", color="lightblue")
            #add main core SDFFs
            for cell, name in self.main_core['scan_flops']:
                label = f"{cell}\n{name}"
                main.node(name, label, shape="box", style="filled", color="lightcyan")
            #add main core gates
            for cell, name in self.main_core['gates']:
                main.node(name, f"{cell}\n{name}", shape="ellipse", color="orange")
            #add WBCs to main core
            for wbc in self.main_core['wbc_cells']:
                input_ports = ', '.join(wbc['inputs'])
                output_ports = ', '.join(wbc['outputs'])
                label = (
                    f"{wbc['cell_type']}\n{wbc['instance']}\nSignal: {wbc['signal']}\n"
                    f"IN: {input_ports}\nOUT: {output_ports}"
                )
                main.node(wbc['instance'], label, shape="octagon", style="filled", color="yellow")
        
        with dot.subgraph(name='cluster_right') as right:
            right.attr(label='Right Core (No WBCs)', style='filled', color='lightgrey')
            right.attr(rank='same')
            #add right core DFFs
            for cell, name in self.right_core['flipflops']:
                label = f"{cell}\n{name}"
                right.node(name, label, shape="box", style="filled", color="lightgrey")
            #add right core SDFFs
            for cell, name in self.right_core['scan_flops']:
                label = f"{cell}\n{name}"
                right.node(name, label, shape="box", style="filled", color="lightgreen")
            #add right core gates
            for cell, name in self.right_core['gates']:
                right.node(name, f"{cell}\n{name}", shape="ellipse", color="orange")
        
        #draw extest scan chain path (WBCs only)
        for idx in range(len(self.extest_scan_chain) - 1):
            from_cell = self.extest_scan_chain[idx]
            to_cell = self.extest_scan_chain[idx + 1]
            dot.edge(from_cell['instance'], to_cell['instance'], 
                    label=f"SO->SI", color="red", penwidth="2")
        
        #add scan chain input/output labels
        if self.extest_scan_chain:
            dot.node("extest_scan_in", "Extest\nScan In", shape="diamond", color="red")
            dot.node("extest_scan_out", "Extest\nScan Out", shape="diamond", color="red")
            dot.edge("extest_scan_in", self.extest_scan_chain[0]['instance'], 
                    color="red", penwidth="2")
            dot.edge(self.extest_scan_chain[-1]['instance'], "extest_scan_out", 
                    color="red", penwidth="2")
        
        #creating specific connections as for convenience:
        # WBC_in[0] -> left_count_reg[0]
        # WBC_in[1] -> left_count_reg[1] 
        # WBC_in[2] -> left_count_reg[2]
        # WBC_in[3] -> left_count_reg[3]
        # WBC_out[0] -> right_count_reg[0]
        # WBC_out[1] -> right_count_reg[1]
        # WBC_out[2] -> right_count_reg[2]
        # WBC_out[3] -> right_count_reg[3]
        
        #get input WBCs sorted by signal name to ensure correct order
        input_wbcs = sorted(
            [wbc for wbc in self.main_core['wbc_cells'] if wbc['direction'] == 'input'],
            key=lambda x: x['signal']
        )
        
        #get output WBCs sorted by signal name to ensure correct order
        output_wbcs = sorted(
            [wbc for wbc in self.main_core['wbc_cells'] if wbc['direction'] == 'output'],
            key=lambda x: x['signal']
        )
        
        #get left core flip-flops sorted by name to ensure correct order
        left_ff_names = []
        for _, name in sorted(self.left_core['flipflops'] + self.left_core['scan_flops'], key=lambda x: x[1]):
            left_ff_names.append(name)
        
        #get right core flip-flops sorted by name to ensure correct order
        right_ff_names = []
        for _, name in sorted(self.right_core['flipflops'] + self.right_core['scan_flops'], key=lambda x: x[1]):
            right_ff_names.append(name)
        
        #create specific input WBC to left core connections
        for i in range(min(len(input_wbcs), len(left_ff_names))):
            wbc = input_wbcs[i]
            left_ff = left_ff_names[i]
            dot.edge(wbc['instance'], left_ff, 
                    color="blue", style="dashed", 
                    label=f"WBC_in[{i}]->left_count_reg[{i}]")
        
        #create specific output WBC to right core connections
        for i in range(min(len(output_wbcs), len(right_ff_names))):
            wbc = output_wbcs[i]
            right_ff = right_ff_names[i]
            dot.edge(wbc['instance'], right_ff, 
                    color="green", style="dashed", 
                    label=f"WBC_out[{i}]->right_count_reg[{i}]")
        
        dot.render(output_file, view=True, format="pdf")

    def run(self):
        """
        Execute the complete Extest Mode setup
        """
        print("=== EXTEST MODE SETUP ===")
        self.parse_file()
        self.extract_design_info()
        self.initialize_three_cores()
        self.construct_extest_scan_chain()
        self.display_extest_summary()
        self.create_extest_schematic()

if __name__ == "__main__":
    analyzer = ExtestModeDFT("./simple_counter.v")
    analyzer.run() 