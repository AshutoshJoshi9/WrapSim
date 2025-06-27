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
        # Now includes both SDFF and DFF cells in the scan chain
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

    def capture(self, se_map=None, si_map=None, reset_map=None):
        print("[CAPTURE]")
        # Gather only real scan-FFs (exclude WBCs)
        q_map = {cell.name: cell.Q for cell in self.cells if cell.cell_type.lower() != 'wbc'}
        # Use the new evaluator.capture interface
        final_q = self.evaluator.capture(q_map, cycles=2, se_map=se_map, si_map=si_map, reset_map=reset_map)
        for cell in self.cells:
            if cell.name in final_q:
                cell.Q = final_q[cell.name]
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
        # --- Scan/shift-in mode ---
        self.shift_in(test_vector)
        # Set SE=0 for all SDFFs for functional mode
        se_map_func = {inst: 0 for inst in self.evaluator.sdff_cells}
        si_map_func = {inst: 0 for inst in self.evaluator.sdff_cells}
        # --- Functional capture ---
        self.capture(se_map=se_map_func, si_map=si_map_func)
        # --- Scan/shift-out mode ---
        signature = self.shift_out()
        self.print_trace()
        print(f"\nFinal Signature: {signature}")
        return signature

if __name__ == "__main__":
    analyzer = VerilogScanDFT("./simple_counter.v")
    analyzer.run()
    evaluator = LogicEvaluator(analyzer.ast)
    evaluator.build_model()
    evaluator.debug_model()
    scan_chain = analyzer.scan_chain
    simulator = ScanChainSimulator(scan_chain, evaluator)

    test_vector = ''.join(random.choice('01') for _ in range(len(scan_chain)))
    #test_vector = '101010101010'  # Alternating pattern to show capture working
    simulator.run(test_vector)
