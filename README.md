# WrapSim: Python-Based Verilog Netlist Scan Chain & DFT Simulator

## Overview

**WrapSim** is a Python-based tool for automating Design-for-Test (DFT) infrastructure on arbitrary Verilog netlists. It parses your Verilog netlist, inserts custom scan chain wrappers, and enables simulation of INTEST and EXTEST modes. The tool supports custom cell libraries and can handle both standard and scan flip-flops, as well as arbitrary combinational logic.

**Key Features:**
- **Netlist-Agnostic:** Works with any Verilog netlist.
- **Automatic Scan Chain Insertion:** Detects flip-flops and forms scan chains.
- **Custom Wrapper Insertion:** Adds boundary scan cells and DFT logic for INTEST/EXTEST.
- **Custom Cell Library Support:** Models custom gates and flip-flops as defined in your library.
- **Simulation:** Simulates scan operations, INTEST, and EXTEST modes.
- **Visualization:** Generates schematic PDFs of the scan chain and boundary structure.
- **Extensible:** Easily adaptable to new cell types or DFT strategies.

---

## Repository Structure

```
WrapSim/
├── main.py                  # Main entry: netlist parsing, scan chain/wrapper insertion, simulation
├── logic_evaluator.py       # Logic evaluation for custom gates and netlist logic, used in Capture Phase 
├── scan_chain_pipeline.py   # Pipeline for INTEST mode simulation and result generation
├── extest_mode.py           # EXTEST/INTEST mode analysis and wrapper insertion
├── extest_simulator.py      # Simulation of EXTEST mode
├── wbc_inserter.py          # Automated wrapper/boundary cell insertion
├── lib_cells.v              # Custom cell library (Verilog)
├── net.v, net1.v            # Example netlists (Verilog)
├── scan_chain.v             # Example scan chain (Verilog)
├── simple_counter.v         # Example design (can be replaced)
├── testbench.v, testbench_extest.v # Verilog testbenches for INTEST/EXTEST simulation
├── Makefile, Makefile_extest# Makefiles for cocotb-based testbench simulation
├── tests/                   # Python test scripts
├── extest_results_8bit.csv, scan_chain_results_12bit.csv # Example results
├── schematic.pdf, extest_schematic.pdf # Generated schematics
└── ... (other files)
```

---

## Requirements

- Python 3.10
- [Pyverilog](https://github.com/PyHDI/Pyverilog)
- [cocotb](https://github.com/cocotb/cocotb) (for Verilog testbench simulation)
- [GTKWave](http://gtkwave.sourceforge.net/) (for waveform viewing)
- numpy, matplotlib, tabulate, graphviz

Install dependencies:

```bash
pip install pyverilog numpy matplotlib tabulate graphviz cocotb
```

**Note:** GTKWave needs to be installed separately:
- **Ubuntu/Debian:** `sudo apt-get install gtkwave`
- **macOS:** `brew install gtkwave`
- **Windows:** Download from [GTKWave website](http://gtkwave.sourceforge.net/)

---

## Usage

### 1. **Parse and Wrap a Verilog Netlist**

To run the main tool on your netlist (replace `net.v` with your file):

```bash
python main.py
```

- Parses the Verilog netlist and cell library.
- Detects flip-flops and forms scan chains.
- Inserts custom wrapper/boundary cells for DFT.
- Simulates scan operations and generates schematic PDFs.

You can specify your own netlist and cell library by editing the file paths in `main.py`.

---

### 2. **EXTEST/INTEST Mode Analysis and Simulation**

To analyze and simulate EXTEST/INTEST modes:

```bash
python extest_mode.py
python extest_simulator.py
```

- `extest_mode.py` analyzes the netlist, inserts boundary cells, and generates the EXTEST/INTEST scan chain and schematic.
- `extest_simulator.py` simulates EXTEST operations and generates result CSVs.

---

### 3. **INTEST Mode Simulation**

For INTEST mode simulation and result generation:

```bash
python scan_chain_pipeline.py
```

- Simulates INTEST mode scan operations.
- Saves results to a CSV file (e.g., `scan_chain_results_12bit.csv`).

---

### 4. **Testing**

Run all Python tests:

```bash
pytest
```

Or run individual test scripts in the `tests/` directory.

---

### 5. **Schematic Generation**

Schematic PDFs (e.g., `schematic.pdf`, `extest_schematic.pdf`) are generated automatically and can be viewed with any PDF viewer.

---

### 6. **Verilog Testbench Simulation with Waveforms**

The project includes Verilog testbenches and Makefiles for cocotb-based simulation with waveform generation.

#### **Run INTEST Mode Testbench:**

```bash
make -f Makefile
```

This will:
- Simulate the design using `testbench.v` and `tests/test_scan.py`
- Generate waveform file `wave.vcd`
- Run INTEST mode scan chain testing

#### **Run EXTEST Mode Testbench:**

```bash
make -f Makefile_extest
```

This will:
- Simulate the design using `testbench_extest.v` and `tests/test_extest.py`
- Generate waveform file `wave_extest.vcd`
- Run EXTEST mode boundary scan testing

#### **View Waveforms with GTKWave:**

```bash
# View INTEST mode waveforms
gtkwave wave.vcd

# View EXTEST mode waveforms
gtkwave wave_extest.vcd
```

**GTKWave Tips:**
- Use the hierarchy panel to select signals
- Right-click signals to add them to the waveform view
- Use zoom controls to examine specific time periods
- Save your signal configuration for future use

#### **Clean Build Artifacts:**

```bash
# Clean INTEST mode build artifacts
make -f Makefile clean

# Clean EXTEST mode build artifacts
make -f Makefile_extest extest-clean

# Clean all build artifacts (manual)
rm -rf __pycache__
rm -rf sim_build
rm -rf results.xml
rm -rf wave.vcd wave_extest.vcd
rm -rf dump.vcd
rm -rf test.log
```

---

## Customization

- **Netlist/Design:** Use your own Verilog netlist in place of the provided examples.
- **Cell Library:** Update `lib_cells.v` to match your technology/library.
- **Logic Models:** Edit `logic_evaluator.py` to add or modify gate logic as needed.

---

## Example

```bash
# Run the main scan chain/wrapper insertion and simulation
python main.py

# Analyze and simulate EXTEST mode
python extest_mode.py
python extest_simulator.py

# Run INTEST mode simulation
python scan_chain_pipeline.py

# Run Verilog testbenches with waveform generation
make -f Makefile          # INTEST mode testbench
make -f Makefile_extest   # EXTEST mode testbench

# View waveforms
gtkwave wave.vcd          # INTEST waveforms
gtkwave wave_extest.vcd   # EXTEST waveforms

# Clean build artifacts
make -f Makefile clean     # Clean INTEST artifacts
make -f Makefile_extest extest-clean  # Clean EXTEST artifacts
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.


---

## Acknowledgments

- [Pyverilog](https://github.com/PyHDI/Pyverilog)
- Open-source DFT/scan chain research community

---