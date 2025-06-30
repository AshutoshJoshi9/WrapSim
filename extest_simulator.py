# extest_simulator.py

from extest_mode import ExtestModeDFT
from logic_evaluator import LogicEvaluator
from main import VerilogScanDFT
import csv

class ExtestCell:
    def __init__(self, name, cell_type, direction=None, signal=None):
        self.name = name
        self.cell_type = cell_type
        self.direction = direction
        self.signal = signal
        self.value = 0  # Current value in the WBC

class ExtestSimulator:
    def __init__(self, extest_analyzer: ExtestModeDFT):
        self.extest_analyzer = extest_analyzer
        self.wbc_cells = []
        self.history = []
        self.verbose = True
        
        # Initialize WBC cells from the extest scan chain
        for cell in extest_analyzer.extest_scan_chain:
            wbc = ExtestCell(
                name=cell['instance'],
                cell_type=cell['cell_type'],
                direction=cell['direction'],
                signal=cell['signal']
            )
            self.wbc_cells.append(wbc)
        
        # Create logic evaluators for left and right cores
        self.left_evaluator = None
        self.right_evaluator = None
        self.setup_core_evaluators()
    
    def setup_core_evaluators(self):
        """
        Set up logic evaluators for left and right cores
        """
        print("\n=== Setting up Core Logic Evaluators ===")
        
        # Use the same netlist but with prefixed instance names
        # We'll need to create modified netlists for left and right cores
        # For now, we'll use the original netlist and handle the naming in simulation
        
        # Initialize evaluators (they'll be configured during capture)
        self.left_evaluator = LogicEvaluator(self.extest_analyzer.ast)
        self.right_evaluator = LogicEvaluator(self.extest_analyzer.ast)
        
        print("Logic evaluators initialized for left and right cores")

    def shift_in(self, test_vector):
        """
        Shift test vector into main core WBCs
        """
        if self.verbose:
            print(f"\n[SHIFT-IN] Loading test vector: {test_vector}")
        
        # Ensure test vector length matches WBC count
        if len(test_vector) != len(self.wbc_cells):
            raise ValueError(f"Test vector length {len(test_vector)} doesn't match WBC count {len(self.wbc_cells)}")
        
        # Load test vector into WBCs
        for i, bit in enumerate(test_vector):
            self.wbc_cells[i].value = int(bit)
            if self.verbose:
                print(f"  {self.wbc_cells[i].name} ({self.wbc_cells[i].direction}) = {bit}")
        
        self.record_state("ShiftIn Complete")

    def capture(self, cycles=1):
        """
        Capture phase: Simulate left and right cores in functional mode
        """
        if self.verbose:
            print(f"\n[CAPTURE] Running {cycles} functional cycles")
        
        # Separate input and output WBCs
        input_wbcs = [wbc for wbc in self.wbc_cells if wbc.direction == 'input']
        output_wbcs = [wbc for wbc in self.wbc_cells if wbc.direction == 'output']
        
        # Build evaluators for left and right cores
        self.left_evaluator.build_model()
        self.right_evaluator.build_model()
        
        # Initialize Q values for left and right cores
        # We'll use the WBC values to set initial Q values
        left_q = {}
        right_q = {}
        
        # Map WBC values to flip-flops by bit position
        # Based on simple_counter.v: count_reg_3->out[3], count_reg_2->out[2], count_reg_1->out[1], count_reg_0->out[0]
        flop_to_bit = {
            'count_reg_3': 3,  # MSB
            'count_reg_2': 2,
            'count_reg_1': 1, 
            'count_reg_0': 0   # LSB
        }
        
        # Map input WBCs to left core flip-flops
        for i, wbc in enumerate(input_wbcs):
            bit_pos = i  # WBC_in0 -> bit 0, WBC_in1 -> bit 1, etc.
            for flop_name, flop_bit in flop_to_bit.items():
                if flop_bit == bit_pos:
                    left_q[flop_name] = wbc.value
                    if self.verbose:
                        print(f"  Mapping WBC_in{i} (bit {bit_pos}) -> {flop_name} = {wbc.value}")
        
        # Map output WBCs to right core flip-flops
        for i, wbc in enumerate(output_wbcs):
            bit_pos = i  # WBC_out0 -> bit 0, WBC_out1 -> bit 1, etc.
            for flop_name, flop_bit in flop_to_bit.items():
                if flop_bit == bit_pos:
                    right_q[flop_name] = wbc.value
                    if self.verbose:
                        print(f"  Mapping WBC_out{i} (bit {bit_pos}) -> {flop_name} = {wbc.value}")
        
        # Run capture simulation for left and right cores
        # Set SE=0 for functional mode (not scan mode)
        se_map = {inst: 0 for inst in self.left_evaluator.sdff_cells}
        si_map = {inst: 0 for inst in self.left_evaluator.sdff_cells}
        
        # Capture for left core
        self.left_final_q = self.left_evaluator.capture(left_q, cycles=cycles, se_map=se_map, si_map=si_map)
        
        # Capture for right core
        self.right_final_q = self.right_evaluator.capture(right_q, cycles=cycles, se_map=se_map, si_map=si_map)
        
        self.record_state("Capture Complete")

    def shift_out(self):
        """
        Shift out: Load core values back into WBCs and generate signature
        """
        if self.verbose:
            print("\n[SHIFT-OUT] Loading core values into WBCs")
        
        # Debug: Print the actual Q values from the evaluators
        print(f"DEBUG: left_final_q = {self.left_final_q}")
        print(f"DEBUG: right_final_q = {self.right_final_q}")
        
        # Separate input and output WBCs
        input_wbcs = [wbc for wbc in self.wbc_cells if wbc.direction == 'input']
        output_wbcs = [wbc for wbc in self.wbc_cells if wbc.direction == 'output']
        
        # Create a mapping from flip-flop instance name to bit position
        # Based on simple_counter.v: count_reg_3->out[3], count_reg_2->out[2], count_reg_1->out[1], count_reg_0->out[0]
        flop_to_bit = {
            'count_reg_3': 3,  # MSB
            'count_reg_2': 2,
            'count_reg_1': 1, 
            'count_reg_0': 0   # LSB
        }
        
        # Load left core values into input WBCs
        # Create a list to hold values in correct bit order
        left_core_values = [0] * 4  # Initialize with zeros
        for flop_name, value in self.left_final_q.items():
            if flop_name in flop_to_bit:
                bit_pos = flop_to_bit[flop_name]
                left_core_values[bit_pos] = value
                if self.verbose:
                    print(f"  Left core {flop_name} (bit {bit_pos}) = {value}")
        
        # Map left core values to input WBCs
        for i, wbc in enumerate(input_wbcs):
            if i < 4:
                wbc.value = left_core_values[i]
                if self.verbose:
                    print(f"  {wbc.name} (input) = {wbc.value} (from left core bit {i})")
        
        # Load right core values into output WBCs
        # Create a list to hold values in correct bit order
        right_core_values = [0] * 4  # Initialize with zeros
        for flop_name, value in self.right_final_q.items():
            if flop_name in flop_to_bit:
                bit_pos = flop_to_bit[flop_name]
                right_core_values[bit_pos] = value
                if self.verbose:
                    print(f"  Right core {flop_name} (bit {bit_pos}) = {value}")
        
        # Map right core values to output WBCs
        for i, wbc in enumerate(output_wbcs):
            if i < 4:
                wbc.value = right_core_values[i]
                if self.verbose:
                    print(f"  {wbc.name} (output) = {wbc.value} (from right core bit {i})")
        
        # Generate signature: concatenate all WBC values in testvector order
        signature = ''.join(str(wbc.value) for wbc in input_wbcs + output_wbcs)
        
        if self.verbose:
            print(f"Generated signature: {signature}")
        
        self.record_state("ShiftOut Complete")
        return signature

    def record_state(self, label):
        """Record the current state for tracing"""
        state = ''.join(str(wbc.value) for wbc in self.wbc_cells)
        self.history.append((label, state))

    def print_trace(self):
        """Print the complete test trace"""
        if self.verbose:
            print("\n[EXTEST TRACE LOG]")
            for label, state in self.history:
                print(f"{label}: {state}")

    def run_extest(self, test_vector, verbose=True):
        """
        Run complete Extest Mode test
        """
        self.verbose = verbose
        self.history = []  # Clear history for each run
        
        if verbose:
            print(f"\n=== RUNNING EXTEST MODE: {test_vector} ===")
        
        # Phase 1: Shift-in test vector into WBCs
        self.shift_in(test_vector)
        
        # Phase 2: Capture - simulate left and right cores
        self.capture(cycles=1)
        
        # Phase 3: Shift-out - generate signature
        signature = self.shift_out()
        
        if verbose:
            self.print_trace()
            print(f"\nFinal Extest Signature: {signature}")
        
        return signature

def exhaustive_extest_test(simulator, wbc_count):
    """
    Run exhaustive test for all possible WBC input vectors
    """
    print(f"\n=== Exhaustive Extest Test: {2**wbc_count} vectors ===")
    results = {}
    
    # Create CSV file for results
    csv_filename = f"extest_results_{wbc_count}bit.csv"
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Input Vector', 'Output Signature'])
        
        for i in range(2**wbc_count):
            vec = format(i, f'0{wbc_count}b')
            print(f"Testing vector {i+1}/{2**wbc_count}: {vec}")
            
            # Run simulation with minimal output
            sig = simulator.run_extest(vec, verbose=False)
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
    # Initialize Extest Mode
    extest_analyzer = ExtestModeDFT("./simple_counter.v")
    extest_analyzer.run()
    
    # Create Extest simulator
    simulator = ExtestSimulator(extest_analyzer)
    
    # Test 10 diverse vectors
    test_vectors = [
        "00000000",
        "00000001",
        "00000010",
        "00000100",
        "00001000",
        "00010000",
        "00100000",
        "01000000",
        "10000000",
        "11111111"
    ]
    for test_vector in test_vectors:
        print("\n" + "="*40)
        print(f"Testing vector: {test_vector}")
        signature = simulator.run_extest(test_vector)
        print(f"Input Vector: {test_vector}")
        print(f"Output Signature: {signature}")
        print("="*40)
    
    # Don't run exhaustive test for now
    exhaustive_extest_test(simulator, len(simulator.wbc_cells)) 