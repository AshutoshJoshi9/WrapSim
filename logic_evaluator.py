# from pyverilog.vparser.parser import parse
# from pyverilog.vparser.ast import *
# from collections import defaultdict

# class LogicEvaluator:
#     def __init__(self, ast):
#         self.ast = ast
#         self.signal_values = {}               # signal name -> 0 or 1
#         self.signal_drivers = {}              # signal name -> instance name or assignment
#         self.gate_inputs = defaultdict(list)  # instance name -> input signal names
#         self.gate_types = {}                  # instance name -> gate type (and, or, etc.)
#         self.d_inputs = {}                    # flipflop instance -> D signal name

#     def build_model(self):
#         def visit(node):
#             if isinstance(node, InstanceList):
#                 cell_type = node.module.lower()
#                 for inst in node.instances:
#                     inst_name = inst.name
#                     #ports = {p.portname: self.extract_name(p.arg) for p in inst.portlist}
#                     ports = {}
#                     for p in inst.portlist:
#                         if hasattr(p, 'portname') and hasattr(p, 'arg'):
#                             ports[p.portname] = self.extract_name(p.arg)
#                         else:
#                             print(f"Skipping malformed port: {p}")

#                     if cell_type in ['sdff', 'dff']:
#                         self.d_inputs[inst_name] = ports.get('D')
#                     elif any(g in cell_type for g in ['and', 'or', 'nand', 'nor', 'xor', 'xnor']):
#                         self.gate_types[inst_name] = cell_type
#                         for pname, arg in ports.items():
#                             if pname in ['A', 'B', 'A1', 'A2', 'B1', 'B2']:
#                                 self.gate_inputs[inst_name].append(arg)
#                             elif pname in ['Y', 'ZN', 'Z']:
#                                 self.signal_drivers[arg] = inst_name

#             elif isinstance(node, Assign):
#                 lhs = self.extract_name(node.left)
#                 rhs = self.extract_name(node.right)
#                 self.signal_drivers[lhs] = rhs

#             for c in node.children():
#                 visit(c)

#         visit(self.ast)

#     def extract_name(self, node):
#         if isinstance(node, Identifier):
#             return node.name
#         elif isinstance(node, Pointer):
#             return f"{node.var.name}{node.ptr.value}"
#         elif isinstance(node, IntConst):
#             return node.value
#         return str(node)

#     def set_primary_inputs(self, values: dict):
#         self.signal_values.update(values)

#     def evaluate_gate(self, inst_name):
#         gtype = self.gate_types[inst_name]
#         inputs = [int(self.signal_values.get(sig, 0)) for sig in self.gate_inputs[inst_name]]

#         if gtype == 'and': return int(all(inputs))
#         if gtype == 'or': return int(any(inputs))
#         if gtype == 'nand': return int(not all(inputs))
#         if gtype == 'nor': return int(not any(inputs))
#         if gtype == 'xor': return int(sum(inputs) % 2)
#         if gtype == 'xnor': return int((sum(inputs) % 2) == 0)
#         return 0

#     def propagate(self):
#         changed = True
#         iteration = 0
#         while changed:
#             changed = False
#             for signal, driver in self.signal_drivers.items():
#                 if driver in self.gate_types:
#                     new_val = self.evaluate_gate(driver)
#                     if self.signal_values.get(signal) != new_val:
#                         self.signal_values[signal] = new_val
#                         changed = True
#                 elif isinstance(driver, str):  # assign a = b
#                     val = self.signal_values.get(driver, 0)
#                     if self.signal_values.get(signal) != val:
#                         self.signal_values[signal] = val
#                         changed = True

#     def evaluate_D_inputs(self) -> dict:
#         results = {}
#         for flop, d_signal in self.d_inputs.items():
#             val = self.signal_values.get(d_signal, 0)
#             results[flop] = val
#         return results

# logic_evaluator.py

from pyverilog.vparser.ast import InstanceList, Assign, Identifier, Pointer, IntConst
from collections import defaultdict

class LogicEvaluator:
    def __init__(self, ast):
        self.ast = ast
        # flop-instance → D-net   (e.g. '\count_reg[3]' → 'n_6')
        self.d_inputs    = {}
        # flop-instance → Q-net   (e.g. '\count_reg[3]' → 'out[3]')
        self.q_outputs   = {}
        # gate-instance → gate type (e.g. 'and2xl', 'oai2bb2xl', …)
        self.gate_types  = {}
        # gate-instance → list of input nets
        self.gate_inputs = defaultdict(list)
        # gate-instance → all port mappings (portname_lower → netname)
        self.gate_ports  = {}
        # net-name → driver (either a gate-instance or another net via assign)
        self.signal_drivers = {}
        # net-name → logic value (0/1) during propagate
        self.signal_values  = {}

    def _extract_name(self, node):
        if isinstance(node, Identifier):
            return node.name
        if isinstance(node, Pointer):
            # produce exactly "busname[index]" to match Verilog nets
            return f"{node.var.name}[{node.ptr.value}]"
        if isinstance(node, IntConst):
            return node.value
        # Handle Lvalue and Rvalue objects
        if hasattr(node, 'name'):
            return node.name
        if hasattr(node, 'var') and hasattr(node, 'ptr'):
            return f"{node.var.name}[{node.ptr.value}]"
        # Try to access the underlying node
        if hasattr(node, 'node'):
            return self._extract_name(node.node)
        # Try to get the first child if it's a container
        if hasattr(node, 'children') and callable(node.children):
            children = list(node.children())
            if children:
                return self._extract_name(children[0])
        # fallback
        return str(node)

    def build_model(self):
        """
        Walk the AST and fill:
          • self.d_inputs, self.q_outputs for every sdff/dff cell
          • self.gate_types, self.gate_ports for every other cell
          • self.signal_drivers to point each net at its gate-driver or assign source
        Also, track SE and SI for SDFFs.
        """
        self.sdff_cells = set()
        self.dff_cells = set()
        self.se_inputs = {}  # SDFF instance -> SE net
        self.si_inputs = {}  # SDFF instance -> SI net
        def visit(node):
            if isinstance(node, InstanceList):
                mtype = node.module.lower()
                for inst in node.instances:
                    inst_name = inst.name
                    # Diagnostic print
                    print(f"Instance: {inst_name}, inst: {inst}, portlist: {getattr(inst, 'portlist', None)}")
                    ports = {}
                    # Try named ports first
                    if hasattr(inst, 'portlist') and inst.portlist:
                        for idx, p in enumerate(inst.portlist):
                            # If portname is missing, fallback to positional mapping
                            pname = getattr(p, 'portname', None)
                            # Extract the net/signal name from .expr or .argname
                            if hasattr(p, 'expr'):
                                netname = self._extract_name(p.expr)
                            elif hasattr(p, 'argname'):
                                netname = self._extract_name(p.argname)
                            else:
                                netname = None
                            if pname is not None:
                                ports[pname.lower()] = netname
                            else:
                                # Positional mapping for SDFFRX1 and DFFRX1
                                if 'sdff' in mtype:
                                    pos_names = ['d', 'se', 'si', 'ck', 'rn', 'q', 'qn']
                                elif 'dff' in mtype:
                                    pos_names = ['d', 'ck', 'rn', 'q', 'qn']
                                else:
                                    pos_names = []
                                if idx < len(pos_names):
                                    ports[pos_names[idx]] = netname
                    if 'sdff' in mtype:
                        print(f"SDFF Instance: {inst_name}, Ports: {ports}")
                        self.sdff_cells.add(inst_name)
                        self.d_inputs  [inst_name] = ports.get('d')
                        self.q_outputs [inst_name] = ports.get('q')
                        self.se_inputs [inst_name] = ports.get('se')
                        self.si_inputs [inst_name] = ports.get('si')
                    elif 'dff' in mtype:
                        print(f"DFF Instance: {inst_name}, Ports: {ports}")
                        self.dff_cells.add(inst_name)
                        self.d_inputs  [inst_name] = ports.get('d')
                        self.q_outputs [inst_name] = ports.get('q')
                    else:
                        # a combinational/library cell
                        self.gate_types [inst_name] = mtype
                        self.gate_ports [inst_name] = ports
                        # classify ports: y,z,zn are outputs, rest are inputs
                        for pname, net in ports.items():
                            if pname in ('y','z','zn'):
                                self.signal_drivers[net] = inst_name
                            else:
                                self.gate_inputs[inst_name].append(net)
            elif isinstance(node, Assign):
                # Handle assign statements properly
                lhs = self._extract_name(node.left)
                rhs = self._extract_name(node.right)
                print(f"  Assign: {lhs} = {rhs}")
                if lhs and rhs and lhs != 'None' and rhs != 'None':
                    self.signal_drivers[lhs] = rhs
                    print(f"    Added signal driver: {lhs} driven by {rhs}")
                else:
                    print(f"    Skipping invalid assign: {lhs} = {rhs}")
            # recurse
            for c in node.children():
                visit(c)
        visit(self.ast)

    def debug_model(self):
        print("=== Flop .D nets ===")
        for inst, net in self.d_inputs.items():
            print(f"  {inst}.D → {net}")
        print("=== Flop .Q nets ===")
        for inst, net in self.q_outputs.items():
            print(f"  {inst}.Q → {net}")
        print("=== Sample of signal_drivers ===")
        for idx, (net, drv) in enumerate(self.signal_drivers.items()):
            if idx < 10:
                print(f"  {net} driven by {drv}")

    def set_primary_inputs(self, values: dict):
        """Inject primary net-values before propagation."""
        self.signal_values.update(values)

    def evaluate_gate(self, inst_name):
        """Boolean eval of a single library/gate cell by substring of its type."""
        gtype = self.gate_types[inst_name]
        ports = self.gate_ports[inst_name]
        # helper to fetch a port's current logic (default=0)
        get = lambda pn: int(self.signal_values.get(ports.get(pn, ''), 0))

        # inverter?
        if 'inv' in gtype:
            return int(not get('a'))

        # NAND / AND
        if 'nand' in gtype:
            return int(not (get('a') and get('b')))
        if 'and' in gtype:
            return int(get('a') and get('b'))

        # NOR / OR
        if 'nor' in gtype:
            return int(not (get('a') or get('b')))
        if 'or' in gtype:
            return int(get('a') or get('b'))

        # XOR / XNOR
        if 'xnor' in gtype:
            return int((get('a') ^ get('b')) == 0)
        if 'xor' in gtype:
            return int(get('a') ^ get('b'))

        # OAI2BB2:  Y = ~((~(A0N & A1N)) & (B0 & B1))
        if 'oai2bb2' in gtype:
            a0n = get('a0n')
            a1n = get('a1n')
            b0  = get('b0')
            b1  = get('b1')
            return int(not ((not (a0n and a1n)) and (b0 or b1)))

        # AOI2BB1:  Y = ~((~(A0N | A1N)) | B0)
        if 'aoi2bb1' in gtype:
            a0n = get('a0n')
            a1n = get('a1n')
            b0  = get('b0')
            return int(not ((not(a0n or a1n)) or b0))

        # AOI21: Y = ~ (B0 | (A0 & A1))
        if 'aoi21' in gtype:
            a0 = get('a0')
            a1 = get('a1')
            b0 = get('b0')
            return int(not (b0 or (a0 and a1)))

        raise NotImplementedError(f"Gate type '{gtype}' not supported")

    def propagate(self):
        """
        Iterate until no net-value changes.
        Simulates unit delay for all gates by updating all outputs simultaneously.
        """
        changed = True
        iteration = 0
        max_iterations = 10  # Prevent infinite oscillation
        while changed and iteration < max_iterations:
            iteration += 1
            print(f"[Propagate iteration {iteration}]")
            changed = False
            
            # Compute all new values first (unit delay simulation)
            new_values = {}
            for net, drv in list(self.signal_drivers.items()):
                if drv in self.gate_types:
                    val = self.evaluate_gate(drv)
                    print(f"  Gate {drv} ({self.gate_types[drv]}): {net} = {val}")
                else:
                    # simple wire assignment
                    val = int(self.signal_values.get(drv, 0))
                    print(f"  Wire {drv} → {net}: {val}")
                new_values[net] = val
            
            # Now update all signal values at once (unit delay)
            for net, val in new_values.items():
                old_val = self.signal_values.get(net, 0)
                if old_val != val:
                    self.signal_values[net] = val
                    changed = True
                    print(f"    *** {net} changed from {old_val} to {val}")
            
            if not changed:
                print(f"  No more changes after {iteration} iterations")
        if iteration >= max_iterations:
            print(f"  WARNING: Propagation stopped after {max_iterations} iterations due to oscillation")

    def evaluate_D_inputs(self) -> dict:
        """
        After propagation, read off each flop's D-net.
        Returns: {inst_name: 0/1}
        """
        return {
            inst: int(self.signal_values.get(d_net, 0))
            for inst, d_net in self.d_inputs.items()
        }

    def simulate_flops(self, current_q, se_map=None, si_map=None, reset_map=None):
        """
        Simulate all flops for one clock edge.
        - current_q: dict of {inst_name: Q}
        - se_map: dict of {inst_name: SE value} for SDFFs
        - si_map: dict of {inst_name: SI value} for SDFFs
        - reset_map: dict of {inst_name: reset value} (1=inactive, 0=reset)
        Returns new_q: dict of {inst_name: Q}
        """
        new_q = {}
        for inst in current_q:
            # Default: not in reset
            reset_val = 1 if reset_map is None else reset_map.get(inst, 1)
            if reset_val == 0:
                new_q[inst] = 0
                continue
            if inst in self.sdff_cells:
                se = se_map.get(inst, 0) if se_map else 0
                if se:
                    new_q[inst] = si_map.get(inst, 0) if si_map else 0
                else:
                    d_net = self.d_inputs[inst]
                    new_q[inst] = int(self.signal_values.get(d_net, 0))
            elif inst in self.dff_cells:
                d_net = self.d_inputs[inst]
                new_q[inst] = int(self.signal_values.get(d_net, 0))
        return new_q

    def capture(self, initial_q: dict, cycles: int = 2, se_map=None, si_map=None, reset_map=None) -> dict:
        """
        Simulate `cycles` back-to-back rising edges:
          1) drive each flop's Q-net with its current Q
          2) propagate the network
          3) sample D-nets
          4) Q <- D (or SI for SDFF if SE=1)
        Returns final {inst_name: Q}
        """
        current_q = initial_q.copy()
        for cycle in range(cycles):
            # 1. Set Q outputs to nets
            primaries = {
                self.q_outputs[inst]: bit
                for inst, bit in current_q.items()
                if inst in self.q_outputs and self.q_outputs[inst] is not None
            }
            self.signal_values.clear()
            self.set_primary_inputs(primaries)
            # 2. Propagate combinational logic until stable
            self.propagate()
            # 3. Simulate flops (update Qs for next cycle)
            current_q = self.simulate_flops(current_q, se_map, si_map, reset_map)
            # 4. Debug output
            print(f"[Capture cycle {cycle+1}] Q values: {current_q}")
            print(f"[Capture cycle {cycle+1}] D inputs: {{inst: self.signal_values.get(self.d_inputs[inst], 0) for inst in current_q}}"); print({inst: self.signal_values.get(self.d_inputs[inst], 0) for inst in current_q})
        return current_q
