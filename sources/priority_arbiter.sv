`timescale 1ns/1ps

module priority_arbiter #(
    parameter int N          = 4,
    parameter int PRIO_WIDTH = 4
)(
    input  logic               clk,
    input  logic               reset,      // Active-LOW
    input  logic [N-1:0]       req,
    output logic [N-1:0]       gnt,
    output logic               gnt_valid
);

    localparam logic [PRIO_WIDTH-1:0] MAX_PRIO = {PRIO_WIDTH{1'b1}};

    // ------------------------------------------------------------
    // Base priority (static)
    // ------------------------------------------------------------
    logic [PRIO_WIDTH-1:0] base_prio [N];

    genvar gi;
    generate
        for (gi = 0; gi < N; gi++) begin : BASE
            assign base_prio[gi] = PRIO_WIDTH'(N-1-gi);
        end
    endgenerate

    // ------------------------------------------------------------
    // State
    // ------------------------------------------------------------
    logic [PRIO_WIDTH-1:0] eff_prio   [N];
    logic [PRIO_WIDTH-1:0] eff_prio_n [N];

    logic [N-1:0] req_d;   // previous-cycle request

    // Grant selection
    logic [$clog2(N)-1:0] grant_idx;
    logic                 grant_found;

    // ------------------------------------------------------------
    // Arbitration: max effective priority
    // Tie-break: lowest index
    // ------------------------------------------------------------
    always @(*) begin
        gnt         = '0;
        gnt_valid   = 1'b0;
        grant_found = 1'b0;
        grant_idx   = '0;

        for (int i = 0; i < N; i++) begin
            if (req[i]) begin
                if (!grant_found || (eff_prio[i] > eff_prio[grant_idx])) begin
                    grant_found = 1'b1;
                    grant_idx   = i;
                end
            end
        end

        if (grant_found) begin
            gnt[grant_idx] = 1'b1;
            gnt_valid      = 1'b1;
        end
    end

    // ------------------------------------------------------------
    // Effective priority next-state logic
    // ------------------------------------------------------------
    always @(*) begin
        for (int i = 0; i < N; i++) begin
            eff_prio_n[i] = eff_prio[i];

            // Case 1: Granted → reset
            if (gnt[i]) begin
                eff_prio_n[i] = base_prio[i];
            end
            // Case 2: Continuous request & not granted → age
            else if (req[i] && req_d[i]) begin
                if (eff_prio[i] < MAX_PRIO)
                    eff_prio_n[i] = eff_prio[i] + 1'b1;
            end
            // Case 3: Request dropped or new request → hold
        end
    end

    // ------------------------------------------------------------
    // Sequential state update
    // ------------------------------------------------------------
    always_ff @(posedge clk or negedge reset) begin
        if (!reset) begin
            for (int i = 0; i < N; i++) begin
                eff_prio[i] <= base_prio[i];
            end
            req_d <= '0;
        end
        else begin
            for (int i = 0; i < N; i++) begin
                eff_prio[i] <= eff_prio_n[i];
            end
            req_d <= req;
        end
    end

endmodule
