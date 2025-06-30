module extest_wrapper(
    input wire clk,
    input wire reset,
    input wire en,
    input wire extest_mode,
    input wire extest_scan_in,
    output wire extest_scan_out,
    input wire [3:0] in,      // Original inputs (for reference)
    output wire [3:0] out     // Original outputs (for reference)
);

    // Extest scan chain: 8 WBCs (4 input + 4 output)
    reg [7:0] extest_scan_chain;
    
    // WBC connections
    wire [3:0] wbc_in;   // Input WBCs
    wire [3:0] wbc_out;  // Output WBCs
    
    // Assign WBC values from scan chain
    assign wbc_in = extest_scan_chain[7:4];   // Upper 4 bits for input WBCs
    assign wbc_out = extest_scan_chain[3:0];  // Lower 4 bits for output WBCs
    
    // Scan chain output
    assign extest_scan_out = extest_scan_chain[0];  // LSB first
    
    // Main counter instance
    simple_counter counter_inst (
        .clk(clk),
        .reset(reset),
        .en(en),
        .in(extest_mode ? wbc_in : in),  // Use WBC inputs in extest mode
        .out(out)
    );
    
    // Scan chain shift logic
    always @(posedge clk) begin
        if (extest_mode && en) begin
            // Shift operation
            extest_scan_chain <= {extest_scan_in, extest_scan_chain[7:1]};
        end
        else if (extest_mode && !en) begin
            // Capture operation - load WBC outputs back into scan chain
            extest_scan_chain[3:0] <= out;  // Capture counter outputs
            // Keep input WBCs unchanged during capture
        end
    end

endmodule 