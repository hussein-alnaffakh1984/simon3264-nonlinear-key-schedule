// Round-serialized key schedule: one round key per clock. After `load`, rk_out = rk[0]; r clocks later rk_out = rk[r].
// 64 state flip-flops + 5-bit round counter + constant lookup; identical for the three variants except the round logic.
`ifndef VARIANT
`define VARIANT ks_round_std
`endif
`ifndef TOPNAME
`define TOPNAME ks_serial
`endif
module `TOPNAME (input clk, input load, input [63:0] mk, output [15:0] rk_out);
  reg  [15:0] k0, k1, k2, k3;
  reg  [4:0]  cnt;
  wire [31:0] Z0 = 32'h0386A45F;                        // z0[0..27], bit j = z0[j]
  wire [15:0] nw;
  `VARIANT u(.k0(k0), .k1(k1), .k2(k2), .k3(k3), .z(Z0[cnt]), .o(nw));
  always @(posedge clk) begin
    if (load) begin k0 <= mk[15:0]; k1 <= mk[31:16]; k2 <= mk[47:32]; k3 <= mk[63:48]; cnt <= 5'd0; end
    else      begin k0 <= k1; k1 <= k2; k2 <= k3; k3 <= nw; cnt <= cnt + 5'd1; end
  end
  assign rk_out = k0;
endmodule
