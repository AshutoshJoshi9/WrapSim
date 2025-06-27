module simple_counter(clk, reset, en, in, out);
    input clk, reset, en;
    input [3:0] in;
    output [3:0] out;

    // Simple 4-bit up counter logic
    // D[0] = Q[0] ^ 1 (toggle LSB)
    // D[1] = Q[1] ^ (Q[0] & 1) (toggle if LSB was 1)
    // D[2] = Q[2] ^ (Q[1] & Q[0] & 1) (toggle if both lower bits were 1)
    // D[3] = Q[3] ^ (Q[2] & Q[1] & Q[0] & 1) (toggle if all lower bits were 1)

    // Internal nets
    wire n_0, n_1, n_2, n_3, n_4, n_5, n_6, n_7, n_8, n_9, n_10, n_11;

    // Reset signal (active low)
    CLKINVX1 g0 (.A(reset), .Y(n_0));

    // D[0] = Q[0] ^ 1 = ~Q[0]
    CLKINVX1 g1 (.A(out[0]), .Y(n_1));
    assign n_2 = n_1;  // D[0]

    // D[1] = Q[1] ^ (Q[0] & 1) = Q[1] ^ Q[0]
    XOR2XL g2 (.A(out[1]), .B(out[0]), .Y(n_3));
    assign n_4 = n_3;  // D[1]

    // D[2] = Q[2] ^ (Q[1] & Q[0])
    AND2XL g3 (.A(out[1]), .B(out[0]), .Y(n_5));
    XOR2XL g4 (.A(out[2]), .B(n_5), .Y(n_6));
    assign n_7 = n_6;  // D[2]

    // D[3] = Q[3] ^ (Q[2] & Q[1] & Q[0])
    AND2XL g5 (.A(out[2]), .B(out[1]), .Y(n_8));
    AND2XL g6 (.A(n_8), .B(out[0]), .Y(n_9));
    XOR2XL g7 (.A(out[3]), .B(n_9), .Y(n_10));
    assign n_11 = n_10;  // D[3]

    // Flip-flops
    SDFFRX1 count_reg_3 (.D(n_11), .SE(en), .SI(in[3]), .CK(clk), .RN(n_0), .Q(out[3]), .QN());
    SDFFRX1 count_reg_2 (.D(n_7), .SE(en), .SI(in[2]), .CK(clk), .RN(n_0), .Q(out[2]), .QN());
    SDFFRX1 count_reg_1 (.D(n_4), .SE(en), .SI(in[1]), .CK(clk), .RN(n_0), .Q(out[1]), .QN());
    DFFRX1 count_reg_0 (.D(n_2), .CK(clk), .RN(n_0), .Q(out[0]), .QN());

endmodule

module top(clk, reset, en, in, out);
    input clk, reset, en;
    input [3:0] in;
    output [3:0] out;

    simple_counter counter_inst (
        .clk(clk),
        .reset(reset),
        .en(en),
        .in(in),
        .out(out)
    );

endmodule 