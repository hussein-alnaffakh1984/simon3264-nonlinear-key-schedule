// One key-schedule round update, proposed v3:  t = ROR3(k3) ^ k1 ^ (ROL1(k3) & ROL8(k3));  o = k0 ^ t ^ ROR1(t) ^ 0xFFFC ^ z
module ks_round_v3(input [15:0] k0, k1, k2, k3, input z, output [15:0] o);
  wire [15:0] t = {k3[2:0], k3[15:3]} ^ k1 ^ ({k3[14:0], k3[15]} & {k3[7:0], k3[15:8]});
  wire [15:0] u = t ^ {t[0], t[15:1]};
  assign o = k0 ^ u ^ {15'h7FFE, z};
endmodule
