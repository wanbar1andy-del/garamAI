
@echo off
title GARAM ACTIVE LEARNING SIMULATION
echo [GARAM] Simulating Execution Feedback Loop...
python -c "from core.liquidity.architect import LiquidityArchitect; arch = LiquidityArchitect(); print('Initial k:', arch.impact_k); arch.learn_from_execution(10000, 70000, 70500, 5000000, 0.02); print('Final k:', arch.impact_k)"
pause
