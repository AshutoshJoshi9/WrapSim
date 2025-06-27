# from logic_evaluator import LogicEvaluator
# from main import VerilogScanDFT
# import random

# class ScanCell:
#     def __init__(self, name, cell_type):
#         self.name = name
#         self.cell_type = cell_type
#         self.Q = 0
#         self.D = 0

# class ScanChainSimulator:
#     def __init__(self, scan_chain, evaluator):
#         self.cells = [ScanCell(cell['instance'], cell['cell_type']) for cell in scan_chain]
#         self.evaluator = evaluator
#         self.history = []

#     def shift_in(self, vector):
#         print("[SHIFT-IN]")
#         for i, bit in enumerate(vector):
#             for j in reversed(range(1, len(self.cells))):
#                 self.cells[j].Q = self.cells[j-1].Q
#             self.cells[0].Q = int(bit)
#             self.record_state(f"ShiftIn {i+1}")

#     def capture(self):
#         print("[CAPTURE]")
#         for cycle in range(2):
#             q_map = {cell.name: cell.Q for cell in self.cells if cell.cell_type.lower() != 'wbc'}
#             self.evaluator.set_primary_inputs(q_map)
#             self.evaluator.propagate()
#             d_inputs = self.evaluator.evaluate_D_inputs()
#             for cell in self.cells:
#                 if cell.name in d_inputs:
#                     cell.D = d_inputs[cell.name]
#             for cell in self.cells:
#                 if cell.cell_type.lower() != 'wbc':
#                     cell.Q = cell.D
#             self.record_state(f"Capture {cycle+1}")

#     def shift_out(self):
#         print("[SHIFT-OUT]")
#         output = ''
#         for cycle in range(len(self.cells)):
#             out_bit = self.cells[-1].Q
#             output += str(out_bit)
#             # Shift right (same direction as shift-in)
#             for i in reversed(range(1, len(self.cells))):
#                 self.cells[i].Q = self.cells[i - 1].Q
#             self.cells[0].Q = 0
#             self.record_state(f"ShiftOut {cycle + 1}")
#         return output

#     def record_state(self, label):
#         state = ''.join(str(cell.Q) for cell in self.cells)
#         self.history.append((label, state))

#     def print_trace(self):
#         print("\n[TRACE LOG]")
#         for label, state in self.history:
#             print(f"{label}: {state}")

#     def run(self, test_vector):
#         print("\n=== RUNNING SCAN CHAIN TEST ===")
#         self.shift_in(test_vector)
#         self.capture()
#         signature = self.shift_out()
#         self.print_trace()
#         print(f"\nFinal Signature: {signature}")
#         return signature

# if __name__ == "__main__":
#     analyzer = VerilogScanDFT("./net1.v")
#     analyzer.run()
#     evaluator = LogicEvaluator(analyzer.ast)
#     evaluator.build_model()

#     scan_chain = analyzer.scan_chain
#     simulator = ScanChainSimulator(scan_chain, evaluator)

#     #test_vector = ''.join(random.choice('01') for _ in range(len(scan_chain)))
#     test_vector = '111110001111'
#     simulator.run(test_vector)


# scan_chain_pipeline.py

from logic_evaluator import LogicEvaluator
from main import VerilogScanDFT
import random

class ScanCell:
    def __init__(self, name, cell_type):
        self.name = name
        self.cell_type = cell_type
        self.Q = 0
        self.D = 0

class ScanChainSimulator:
    def __init__(self, scan_chain, evaluator: LogicEvaluator):
        self.cells = [ScanCell(c['instance'], c['cell_type']) for c in scan_chain]
        self.evaluator = evaluator
        self.history = []

    def shift_in(self, vector):
        print("[SHIFT-IN]")
        for i, bit in enumerate(vector):
            for j in reversed(range(1, len(self.cells))):
                self.cells[j].Q = self.cells[j-1].Q
            self.cells[0].Q = int(bit)
            self.record_state(f"ShiftIn {i+1}")

    def capture(self):
        print("[CAPTURE]")
        # Gather only real scan-FFs (exclude WBCs)
        q_map = {cell.name: cell.Q
                 for cell in self.cells
                 if cell.cell_type.lower() != 'wbc'}
        # Delegate two-cycle capture
        final_q = self.evaluator.capture(q_map, cycles=2)
        # Write back into ScanCell objects
        for cell in self.cells:
            if cell.name in final_q:
                cell.Q = final_q[cell.name]
        # Optionally record final state
        self.record_state("Capture Complete")

    def shift_out(self):
        print("[SHIFT-OUT]")
        output = ''
        for cycle in range(len(self.cells)):
            out_bit = self.cells[-1].Q
            output += str(out_bit)
            for i in reversed(range(1, len(self.cells))):
                self.cells[i].Q = self.cells[i-1].Q
            self.cells[0].Q = 0
            self.record_state(f"ShiftOut {cycle+1}")
        return output

    def record_state(self, label):
        state = ''.join(str(cell.Q) for cell in self.cells)
        self.history.append((label, state))

    def print_trace(self):
        print("\n[TRACE LOG]")
        for label, state in self.history:
            print(f"{label}: {state}")

    def run(self, test_vector):
        print("\n=== RUNNING SCAN CHAIN TEST ===")
        self.shift_in(test_vector)
        self.capture()
        signature = self.shift_out()
        self.print_trace()
        print(f"\nFinal Signature: {signature}")
        return signature

if __name__ == "__main__":
    analyzer = VerilogScanDFT("./net.v")
    analyzer.run()
    evaluator = LogicEvaluator(analyzer.ast)
    evaluator.build_model()
    evaluator.debug_model()
    scan_chain = analyzer.scan_chain
    simulator = ScanChainSimulator(scan_chain, evaluator)

    #test_vector = ''.join(random.choice('01') for _ in range(len(scan_chain)))
    test_vector = '11110001111'
    simulator.run(test_vector)
