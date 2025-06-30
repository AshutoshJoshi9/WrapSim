# test_extest.py

from extest_mode import ExtestModeDFT
from main import VerilogScanDFT

def compare_intest_vs_extest():
    """
    Compare Intest Mode vs Extest Mode scan chains
    """
    print("=== COMPARISON: INTEST vs EXTEST MODE ===\n")
    
    # Initialize Intest Mode
    print("1. INTEST MODE (Original)")
    intest_analyzer = VerilogScanDFT("./simple_counter.v")
    intest_analyzer.run()
    
    print(f"\nIntest scan chain length: {len(intest_analyzer.scan_chain)}")
    print("Intest scan chain includes:")
    intest_wbcs = [cell for cell in intest_analyzer.scan_chain if cell['cell_type'] == 'WBC']
    intest_ffs = [cell for cell in intest_analyzer.scan_chain if 'dff' in cell['cell_type'].lower() or 'sdff' in cell['cell_type'].lower()]
    print(f"  - {len(intest_wbcs)} WBCs")
    print(f"  - {len(intest_ffs)} Flip-flops (SDFFs + DFFs)")
    
    # Initialize Extest Mode
    print("\n2. EXTEST MODE (New)")
    extest_analyzer = ExtestModeDFT("./simple_counter.v")
    extest_analyzer.run()
    
    print(f"\nExtest scan chain length: {len(extest_analyzer.extest_scan_chain)}")
    print("Extest scan chain includes:")
    extest_wbcs = [cell for cell in extest_analyzer.extest_scan_chain if cell['cell_type'] == 'WBC']
    extest_ffs = [cell for cell in extest_analyzer.extest_scan_chain if 'dff' in cell['cell_type'].lower() or 'sdff' in cell['cell_type'].lower()]
    print(f"  - {len(extest_wbcs)} WBCs")
    print(f"  - {len(extest_ffs)} Flip-flops (SDFFs + DFFs)")
    
    # Summary comparison
    print("\n=== SUMMARY COMPARISON ===")
    print(f"Intest Mode: {len(intest_analyzer.scan_chain)} total cells in scan chain")
    print(f"Extest Mode: {len(extest_analyzer.extest_scan_chain)} total cells in scan chain")
    print(f"Difference: {len(intest_analyzer.scan_chain) - len(extest_analyzer.extest_scan_chain)} fewer cells in Extest Mode")
    
    print("\nExtest Mode advantages:")
    print("- Shorter scan chain (faster testing)")
    print("- Tests only boundary connections")
    print("- Three cores initialized (main + left + right)")
    print("- Main core has WBCs, other cores don't")

def demonstrate_extest_scan_chain():
    """
    Demonstrate the Extest Mode scan chain operation
    """
    print("\n=== EXTEST SCAN CHAIN DEMONSTRATION ===")
    
    extest_analyzer = ExtestModeDFT("./simple_counter.v")
    extest_analyzer.run()
    
    print("\nExtest scan chain operation:")
    print("1. Scan In: Test vectors are shifted through WBCs only")
    print("2. Capture: WBCs capture boundary signals")
    print("3. Scan Out: Boundary responses are shifted out")
    
    print("\nScan chain order:")
    for i, cell in enumerate(extest_analyzer.extest_scan_chain):
        print(f"  {i+1}. {cell['instance']} ({cell['direction']}) - {cell['signal']}")
    
    print("\nThis allows testing of:")
    print("- Input boundary connections")
    print("- Output boundary connections") 
    print("- Inter-core connections")
    print("- Without testing internal logic")

if __name__ == "__main__":
    compare_intest_vs_extest()
    demonstrate_extest_scan_chain() 