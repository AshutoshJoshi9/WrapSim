// Auto-generated scan chain
module scan_chain_wrapper(
    input scan_enable,
    input clk,
    input scan_in,
    output scan_out
);

  wire conn_1;
  wire conn_2;
  wire conn_3;
  wire conn_4;
  wire conn_5;
  wire conn_6;
  wire conn_7;
  wire conn_8;
  wire conn_9;
  wire conn_10;

  WBC WBC_in0 (
    .DFT_sdi(scan_in),
    .DFT_sdo(conn_1),
    .CFI(), .CFO(), .WINT(), .WEXT(), .WRCK()
  );
  WBC WBC_in1 (
    .DFT_sdi(conn_1),
    .DFT_sdo(conn_2),
    .CFI(), .CFO(), .WINT(), .WEXT(), .WRCK()
  );
  WBC WBC_in2 (
    .DFT_sdi(conn_2),
    .DFT_sdo(conn_3),
    .CFI(), .CFO(), .WINT(), .WEXT(), .WRCK()
  );
  WBC WBC_in3 (
    .DFT_sdi(conn_3),
    .DFT_sdo(conn_4),
    .CFI(), .CFO(), .WINT(), .WEXT(), .WRCK()
  );
  sdffrx1 \count_reg[3] (
    .SI(conn_4),
    .SO(conn_5),
    .SE(scan_enable),
    .CK(clk),
    .D(), .RN(), .Q(conn_5), .QN()
  );
  sdffrx1 \count_reg[2] (
    .SI(conn_5),
    .SO(conn_6),
    .SE(scan_enable),
    .CK(clk),
    .D(), .RN(), .Q(conn_6), .QN()
  );
  sdffrx1 \count_reg[1] (
    .SI(conn_6),
    .SO(conn_7),
    .SE(scan_enable),
    .CK(clk),
    .D(), .RN(), .Q(conn_7), .QN()
  );
  WBC WBC_out0 (
    .DFT_sdi(conn_7),
    .DFT_sdo(conn_8),
    .CFI(), .CFO(), .WINT(), .WEXT(), .WRCK()
  );
  WBC WBC_out1 (
    .DFT_sdi(conn_8),
    .DFT_sdo(conn_9),
    .CFI(), .CFO(), .WINT(), .WEXT(), .WRCK()
  );
  WBC WBC_out2 (
    .DFT_sdi(conn_9),
    .DFT_sdo(conn_10),
    .CFI(), .CFO(), .WINT(), .WEXT(), .WRCK()
  );
  WBC WBC_out3 (
    .DFT_sdi(conn_10),
    .DFT_sdo(scan_out),
    .CFI(), .CFO(), .WINT(), .WEXT(), .WRCK()
  );

endmodule