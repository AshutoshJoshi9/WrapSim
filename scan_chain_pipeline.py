# scan_chain_pipeline.py

from logic_evaluator import LogicEvaluator
from main import VerilogScanDFT
import random
import csv

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
        self.verbose = True  # Add verbose flag

    def shift_in(self, vector):
        if self.verbose:
            print("[SHIFT-IN]")
        for i, bit in enumerate(vector):
            for j in reversed(range(1, len(self.cells))):
                self.cells[j].Q = self.cells[j-1].Q
            self.cells[0].Q = int(bit)
            self.record_state(f"ShiftIn {i+1}")

    def capture(self, se_map=None, si_map=None, reset_map=None):
        if self.verbose:
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
        if self.verbose:
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
        if self.verbose:
            print("\n[TRACE LOG]")
            for label, state in self.history:
                print(f"{label}: {state}")

    def run(self, test_vector, verbose=True):
        self.verbose = verbose
        self.history = []  # Clear history for each run
        
        if verbose:
            print(f"\n=== RUNNING SCAN CHAIN TEST: {test_vector} ===")
        
        # --- Scan/shift-in mode ---
        self.shift_in(test_vector)
        # Set SE=0 for all SDFFs for functional mode
        se_map_func = {inst: 0 for inst in self.evaluator.sdff_cells}
        si_map_func = {inst: 0 for inst in self.evaluator.sdff_cells}
        # --- Functional capture ---
        self.capture(se_map=se_map_func, si_map=si_map_func)
        # --- Scan/shift-out mode ---
        signature = self.shift_out()
        
        if verbose:
            self.print_trace()
            print(f"\nFinal Signature: {signature}")
        
        return signature

def exhaustive_scan_test(simulator, chain_length):
    print(f"\n=== Exhaustive Scan Chain Test: {2**chain_length} vectors ===")
    results = {}
    
    # Create CSV file for results
    csv_filename = f"scan_chain_results_{chain_length}bit.csv"
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Input Vector', 'Output Signature'])
        
        for i in range(2**chain_length):
            vec = format(i, f'0{chain_length}b')
            print(f"Testing vector {i+1}/{2**chain_length}: {vec}")
            
            # Run simulation with minimal output
            sig = simulator.run(vec, verbose=False)
            results[vec] = sig
            
            # Write to CSV
            writer.writerow([vec, sig])
            
            # Print every 100th result to avoid overwhelming output
            if (i + 1) % 100 == 0 or i < 10:
                print(f"  {vec} -> {sig}")
    
    print(f"\nResults saved to: {csv_filename}")
    print(f"Total vectors tested: {len(results)}")
    
    # Analyze results
    unique_signatures = set(results.values())
    print(f"Unique signatures: {len(unique_signatures)}")
    print(f"Collision rate: {1 - len(unique_signatures)/len(results):.2%}")
    
    return results

if __name__ == "__main__":
    analyzer = VerilogScanDFT("./simple_counter.v")
    analyzer.run()
    evaluator = LogicEvaluator(analyzer.ast)
    evaluator.build_model()
    evaluator.debug_model()
    scan_chain = analyzer.scan_chain
    simulator = ScanChainSimulator(scan_chain, evaluator)

    # Exhaustive test for all possible scan chain input vectors
    exhaustive_scan_test(simulator, len(scan_chain))
