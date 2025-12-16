# Dependency Graph (Visualize via Mermaid)

```mermaid
graph TD
    subgraph scripts
    style scripts fill:#f9f,stroke:#333,stroke-width:2px
    scripts_migrate_data_standard[scripts.migrate_data_standard]
    scripts_sync_universe[scripts.sync_universe]
    scripts_verify_turbo_v3[scripts.verify_turbo_v3]
    scripts_research_alpha[scripts.research_alpha]
    scripts_verify_generalization[scripts.verify_generalization]
    scripts_ingest_fear_rss[scripts.ingest_fear_rss]
    scripts_build_fear_feature[scripts.build_fear_feature]
    scripts_discover_modules[scripts.discover_modules]
    scripts_map_module_to_params[scripts.map_module_to_params]
    scripts_activate_profile[scripts.activate_profile]
    scripts_verify_profile_loader[scripts.verify_profile_loader]
    scripts_batch_profile_eval[scripts.batch_profile_eval]
    scripts_research_profit_first[scripts.research_profit_first]
    scripts_report_edge_buckets[scripts.report_edge_buckets]
    scripts_replay_profit_engine_v1[scripts.replay_profit_engine_v1]
    scripts_run_launcher[scripts.run_launcher]
    scripts_analyze_edge_matrix[scripts.analyze_edge_matrix]
    scripts_run_edge_map_batch[scripts.run_edge_map_batch]
    scripts_run_edge_map_parallel[scripts.run_edge_map_parallel]
    scripts_edge_map_400[scripts.edge_map_400]
    scripts_visualize_edge_map[scripts.visualize_edge_map]
    scripts_visualize_edge_map_regime[scripts.visualize_edge_map_regime]
    scripts_auto_guard_param_reco[scripts.auto_guard_param_reco]
    scripts_report_overall_summary[scripts.report_overall_summary]
    scripts_report_cost_impact[scripts.report_cost_impact]
    scripts_report_regime_guard_reco[scripts.report_regime_guard_reco]
    scripts_generate_full_report[scripts.generate_full_report]
    scripts_dashboard_edge_map[scripts.dashboard_edge_map]
    scripts_telegram_risk_alarm[scripts.telegram_risk_alarm]
    scripts_realtime_data_collector[scripts.realtime_data_collector]
    scripts_batch_edge_map_400[scripts.batch_edge_map_400]
    scripts_realtime_simulator[scripts.realtime_simulator]
    scripts_run_full_pipeline[scripts.run_full_pipeline]
    scripts_analyze_portfolio_vs_market[scripts.analyze_portfolio_vs_market]
    scripts_verify_rescue_005930[scripts.verify_rescue_005930]
    scripts_verify_rescue_top10[scripts.verify_rescue_top10]
    scripts_run_param_conflict_report[scripts.run_param_conflict_report]
    scripts_verify_alpha_vol_scaled[scripts.verify_alpha_vol_scaled]
    scripts_verify_alpha_tuning[scripts.verify_alpha_tuning]
    scripts_alpha_tuning_fast[scripts.alpha_tuning_fast]
    scripts_debug_path[scripts.debug_path]
    scripts_verify_ssot[scripts.verify_ssot]
    scripts_generate_ssot_tuning[scripts.generate_ssot_tuning]
    scripts_extract_winner[scripts.extract_winner]
    scripts_diagnose_hynix[scripts.diagnose_hynix]
    scripts_scan_heroes[scripts.scan_heroes]
    scripts_build_universe_400[scripts.build_universe_400]
    scripts_check_data_availability[scripts.check_data_availability]
    scripts_check_import_cycles[scripts.check_import_cycles]
    scripts_build_inventory[scripts.build_inventory]
    scripts_startup_01_preflight_check[scripts.startup.01_preflight_check]
    scripts_analysis_fs_fast_reality_check[scripts.analysis.fs_fast_reality_check]
    scripts_analysis_analyze_regime_performance[scripts.analysis.analyze_regime_performance]
    scripts_analysis_analyze_strategy_mechanics[scripts.analysis.analyze_strategy_mechanics]
    scripts_analysis_analyze_v3_regime_performance[scripts.analysis.analyze_v3_regime_performance]
    scripts_analysis_analyze_fs_orb_distribution[scripts.analysis.analyze_fs_orb_distribution]
    scripts_analysis_tag_regimes_for_hybrid[scripts.analysis.tag_regimes_for_hybrid]
    scripts_analysis_compare_hybrid_vs_baselines[scripts.analysis.compare_hybrid_vs_baselines]
    scripts_analysis_analyze_pnl_by_regime_and_strategy[scripts.analysis.analyze_pnl_by_regime_and_strategy]
    scripts_analysis_build_playbook_hybrid_v3_from_pnl[scripts.analysis.build_playbook_hybrid_v3_from_pnl]
    scripts_analysis_compare_sharpened[scripts.analysis.compare_sharpened]
    scripts_analysis_score_universe_for_dgefinal[scripts.analysis.score_universe_for_dgefinal]
    scripts_analysis_tag_trades_with_regimes[scripts.analysis.tag_trades_with_regimes]
    scripts_analysis_compute_regime_summary[scripts.analysis.compute_regime_summary]
    scripts_analysis_build_regime_report_markdown[scripts.analysis.build_regime_report_markdown]
    scripts_analysis_micro_regime_analysis[scripts.analysis.micro_regime_analysis]
    scripts_analysis_temp_calc_r1[scripts.analysis.temp_calc_r1]
    scripts_analysis_filter_r3_trades[scripts.analysis.filter_r3_trades]
    scripts_analysis_analyze_nov_crash[scripts.analysis.analyze_nov_crash]
    scripts_optimization_optimize_exits_by_micro_regime[scripts.optimization.optimize_exits_by_micro_regime]
    scripts_healthcheck_run_trading_healthcheck[scripts.healthcheck.run_trading_healthcheck]
    scripts_backtest_run_dge_v0_3_fs_orb_sweep[scripts.backtest.run_dge_v0_3_fs_orb_sweep]
    scripts_backtest_run_dge_v0_3_compounding[scripts.backtest.run_dge_v0_3_compounding]
    scripts_backtest_run_dge_hybrid_backtest[scripts.backtest.run_dge_hybrid_backtest]
    scripts_backtest_run_generic_backtest[scripts.backtest.run_generic_backtest]
    scripts_backtest_run_pure_v2_backtest[scripts.backtest.run_pure_v2_backtest]
    scripts_backtest_run_pure_v3_backtest[scripts.backtest.run_pure_v3_backtest]
    scripts_backtest_run_hybrid_v2_full_attack[scripts.backtest.run_hybrid_v2_full_attack]
    scripts_backtest_run_hybrid_v3_backtest[scripts.backtest.run_hybrid_v3_backtest]
    scripts_backtest_run_dgefinal_portfolio_backtest[scripts.backtest.run_dgefinal_portfolio_backtest]
    scripts_backtest_run_dgefinal_intraday_backtest[scripts.backtest.run_dgefinal_intraday_backtest]
    scripts_backtest_run_champion_rule_backtest[scripts.backtest.run_champion_rule_backtest]
    scripts_backtest_micro_regime[scripts.backtest.micro_regime]
    scripts_backtest_run_champion_rule_v3[scripts.backtest.run_champion_rule_v3]
    scripts_data_verify_6m_data[scripts.data.verify_6m_data]
    scripts_experimental_run_dgefinal_swing_portfolio[scripts.experimental.run_dgefinal_swing_portfolio]
    scripts_experimental_analyze_dgefinal_swing_results[scripts.experimental.analyze_dgefinal_swing_results]
    scripts_experimental_sweep_engine2[scripts.experimental.sweep_engine2]
    scripts_experimental_check_crash_regime[scripts.experimental.check_crash_regime]
    scripts_experimental_optimize_dynamic_allocation[scripts.experimental.optimize_dynamic_allocation]
    scripts_experimental_run_final_scenario_b[scripts.experimental.run_final_scenario_b]
    scripts_experimental_run_verification_5_vs_8[scripts.experimental.run_verification_5_vs_8]
    scripts_experimental_visualize_final_5percent[scripts.experimental.visualize_final_5percent]
    scripts_experimental_sweep_1_to_5[scripts.experimental.sweep_1_to_5]
    scripts_experimental_sweep_dynamic_turbo[scripts.experimental.sweep_dynamic_turbo]
    scripts_experimental_run_10year_dynamic_turbo[scripts.experimental.run_10year_dynamic_turbo]
    scripts_experimental_calc_deployment_rate[scripts.experimental.calc_deployment_rate]
    scripts_experimental_calc_deployment_distribution[scripts.experimental.calc_deployment_distribution]
    scripts_experimental_check_turbo_risk[scripts.experimental.check_turbo_risk]
    scripts_experimental_visualize_turbo_1year[scripts.experimental.visualize_turbo_1year]
    scripts_experimental_verify_compounding[scripts.experimental.verify_compounding]
    scripts_experimental_visualize_turbo_simple_interest[scripts.experimental.visualize_turbo_simple_interest]
    scripts_ui_monitor_test_ui[scripts.ui.monitor_test_ui]
    scripts__archive_run_us_factor_backtest[scripts._archive.run_us_factor_backtest]
    scripts__archive_validate_us_sp500_data_coverage[scripts._archive.validate_us_sp500_data_coverage]
    scripts__archive_generate_garam_system_report[scripts._archive.generate_garam_system_report]
    scripts__archive_schedule_kr_data_collection[scripts._archive.schedule_kr_data_collection]
    scripts__archive_run_us_factor_strategies[scripts._archive.run_us_factor_strategies]
    scripts__archive_garam_startup[scripts._archive.garam_startup]
    scripts__archive_collect_kr_intraday_direct[scripts._archive.collect_kr_intraday_direct]
    scripts__archive_inject_mock_trade[scripts._archive.inject_mock_trade]
    scripts__archive_run_kr_intraday_performance[scripts._archive.run_kr_intraday_performance]
    scripts__archive_run_integrated_portfolio_sim[scripts._archive.run_integrated_portfolio_sim]
    scripts__archive_run_shadow_loop[scripts._archive.run_shadow_loop]
    scripts__archive_run_system_health_check[scripts._archive.run_system_health_check]
    scripts__archive_kr_realtime_feeder[scripts._archive.kr_realtime_feeder]
    scripts__archive_watch_shadow_loop[scripts._archive.watch_shadow_loop]
    scripts__archive_build_ai_dataset[scripts._archive.build_ai_dataset]
    scripts__archive_train_ai_models[scripts._archive.train_ai_models]
    scripts__archive_fetch_historical_data[scripts._archive.fetch_historical_data]
    scripts__archive_label_20y_regimes[scripts._archive.label_20y_regimes]
    scripts__archive_optimize_regime_strategies[scripts._archive.optimize_regime_strategies]
    scripts__archive_test_regime_router[scripts._archive.test_regime_router]
    scripts__archive_fetch_history_kiwoom[scripts._archive.fetch_history_kiwoom]
    scripts__archive_build_regime_summary[scripts._archive.build_regime_summary]
    scripts__archive_generate_daily_playbook[scripts._archive.generate_daily_playbook]
    scripts__archive_run_regime_playbook[scripts._archive.run_regime_playbook]
    scripts__archive_run_20y_backtest[scripts._archive.run_20y_backtest]
    scripts__archive_run_miracle_optimization[scripts._archive.run_miracle_optimization]
    scripts__archive_run_miracle_verification[scripts._archive.run_miracle_verification]
    scripts__archive_test_dashboard_performance[scripts._archive.test_dashboard_performance]
    scripts__archive_run_policy_backtest[scripts._archive.run_policy_backtest]
    scripts__archive_run_gap_analysis[scripts._archive.run_gap_analysis]
    scripts__archive_run_param_conflict_report[scripts._archive.run_param_conflict_report]
    scripts__archive_generate_detailed_block_report[scripts._archive.generate_detailed_block_report]
    scripts__archive_analyze_multi_horizon_logs[scripts._archive.analyze_multi_horizon_logs]
    scripts__archive_analyze_multi_horizon_blocks[scripts._archive.analyze_multi_horizon_blocks]
    scripts__archive_run_wfo[scripts._archive.run_wfo]
    scripts__archive_analyze_wfo_results[scripts._archive.analyze_wfo_results]
    scripts__archive_run_dge_daily[scripts._archive.run_dge_daily]
    scripts__archive_run_swing_daily[scripts._archive.run_swing_daily]
    scripts__archive_analyze_coordination_logs[scripts._archive.analyze_coordination_logs]
    scripts__archive_fetch_intraday_kiwoom[scripts._archive.fetch_intraday_kiwoom]
    scripts__archive_validate_intraday_data[scripts._archive.validate_intraday_data]
    scripts__archive_analyze_paper_trading_logs[scripts._archive.analyze_paper_trading_logs]
    scripts__archive_analyze_portfolio_efficiency[scripts._archive.analyze_portfolio_efficiency]
    scripts__archive_select_top10_universe[scripts._archive.select_top10_universe]
    scripts__archive_run_dge_multi[scripts._archive.run_dge_multi]
    scripts__archive_research_heatscore[scripts._archive.research_heatscore]
    scripts__archive_research_acceleration[scripts._archive.research_acceleration]
    scripts__archive_check_system_health[scripts._archive.check_system_health]
    scripts__archive_run_regression_suite[scripts._archive.run_regression_suite]
    scripts__archive_chaos_safety_check[scripts._archive.chaos_safety_check]
    scripts__archive_simulate_projection[scripts._archive.simulate_projection]
    scripts__archive_daily_routine[scripts._archive.daily_routine]
    scripts__archive_generate_eod_report[scripts._archive.generate_eod_report]
    scripts__archive_create_dummy_plan[scripts._archive.create_dummy_plan]
    scripts__archive_run_today_simulation[scripts._archive.run_today_simulation]
    scripts__archive_repo_health_scan[scripts._archive.repo_health_scan]
    scripts__archive_run_backtest_dge[scripts._archive.run_backtest_dge]
    scripts__archive_run_backtest_ab_comparison[scripts._archive.run_backtest_ab_comparison]
    scripts__archive_run_backtest_v3_comparison[scripts._archive.run_backtest_v3_comparison]
    scripts__archive_test_paper_broker[scripts._archive.test_paper_broker]
    scripts__archive_run_paper_trading[scripts._archive.run_paper_trading]
    scripts__archive_run_paper_hybrid[scripts._archive.run_paper_hybrid]
    scripts__archive_debug_daily_df[scripts._archive.debug_daily_df]
    scripts__archive_stress_test_capacity[scripts._archive.stress_test_capacity]
    scripts__archive_fetch_minute_data_selected[scripts._archive.fetch_minute_data_selected]
    scripts__archive_run_live_dge_final[scripts._archive.run_live_dge_final]
    scripts__archive_fetch_champion_universe_data[scripts._archive.fetch_champion_universe_data]
    scripts__archive_verify_data_integrity[scripts._archive.verify_data_integrity]
    scripts__archive_test_fetch_old_minute_data[scripts._archive.test_fetch_old_minute_data]
    scripts__archive_generate_real_scores[scripts._archive.generate_real_scores]
    scripts__archive_run_real_simulation[scripts._archive.run_real_simulation]
    scripts__archive_analyze_regime_distribution[scripts._archive.analyze_regime_distribution]
    scripts__archive_analyze_alpha_performance[scripts._archive.analyze_alpha_performance]
    scripts__archive_analyze_final_results[scripts._archive.analyze_final_results]
    scripts__archive_build_intraday_features[scripts._archive.build_intraday_features]
    scripts__archive_visualize_results[scripts._archive.visualize_results]
    scripts__archive_visualize_compounding[scripts._archive.visualize_compounding]
    scripts__archive_analyze_drawdown_duration[scripts._archive.analyze_drawdown_duration]
    scripts__archive_visualize_comparison_s4_s5[scripts._archive.visualize_comparison_s4_s5]
    scripts__archive_visualize_comparison_s4_s6[scripts._archive.visualize_comparison_s4_s6]
    scripts__archive_visualize_comparison_s4_s7[scripts._archive.visualize_comparison_s4_s7]
    scripts__archive_visualize_comparison_s4_s8[scripts._archive.visualize_comparison_s4_s8]
    scripts__archive_visualize_comparison_s4_s9[scripts._archive.visualize_comparison_s4_s9]
    scripts__archive_visualize_comparison_s4_s11[scripts._archive.visualize_comparison_s4_s11]
    scripts__archive_run_live_trading[scripts._archive.run_live_trading]
    scripts__archive_fetch_daily_data_fdr[scripts._archive.fetch_daily_data_fdr]
    scripts__archive_run_simulation_dec1_dec3[scripts._archive.run_simulation_dec1_dec3]
    scripts__archive_run_simulation_1month[scripts._archive.run_simulation_1month]
    scripts__archive_visualize_1month_simulation[scripts._archive.visualize_1month_simulation]
    scripts__archive_verify_aggregator[scripts._archive.verify_aggregator]
    scripts__archive_run_simulation_multialpha_dec1_5[scripts._archive.run_simulation_multialpha_dec1_5]
    scripts__archive_run_simulation_1year[scripts._archive.run_simulation_1year]
    scripts__archive_compare_results[scripts._archive.compare_results]
    scripts__archive_run_optimization[scripts._archive.run_optimization]
    scripts__archive_run_simulation_5days[scripts._archive.run_simulation_5days]
    scripts__archive_check_data_freshness[scripts._archive.check_data_freshness]
    scripts__archive_test_kiwoom_connection[scripts._archive.test_kiwoom_connection]
    scripts__archive_run_simulation_dynamic[scripts._archive.run_simulation_dynamic]
    scripts__archive_fix_simulation_state[scripts._archive.fix_simulation_state]
    scripts__archive_sync_signals_state[scripts._archive.sync_signals_state]
    scripts__archive_analyze_simulation_performance[scripts._archive.analyze_simulation_performance]
    scripts__archive_run_simulation_1year_dynamic[scripts._archive.run_simulation_1year_dynamic]
    scripts__archive_test_dashboard_api[scripts._archive.test_dashboard_api]
    scripts__archive_test_dashboard_api_history[scripts._archive.test_dashboard_api_history]
    scripts__archive_test_engine_init[scripts._archive.test_engine_init]
    scripts__archive_test_engine_dynamic[scripts._archive.test_engine_dynamic]
    scripts__archive_optimize_dual_engine[scripts._archive.optimize_dual_engine]
    scripts__archive_run_dual_engine_1y_detailed[scripts._archive.run_dual_engine_1y_detailed]
    scripts__archive_analyze_trades[scripts._archive.analyze_trades]
    scripts__archive_kiwoom_maintenance[scripts._archive.kiwoom_maintenance]
    scripts__archive_run_simulation_mss_verify[scripts._archive.run_simulation_mss_verify]
    scripts__archive_run_verify_dual_engine[scripts._archive.run_verify_dual_engine]
    scripts__archive_backfill_comparison_data[scripts._archive.backfill_comparison_data]
    scripts__archive_generate_dummy_history[scripts._archive.generate_dummy_history]
    scripts__archive_debug_signals_read[scripts._archive.debug_signals_read]
    scripts__archive_analyze_drawdown_dates[scripts._archive.analyze_drawdown_dates]
    scripts__archive_analyze_selection_detail[scripts._archive.analyze_selection_detail]
    scripts__archive_analyze_forensic_deep_dive[scripts._archive.analyze_forensic_deep_dive]
    scripts__archive_analyze_micro_simulation[scripts._archive.analyze_micro_simulation]
    scripts__archive_analyze_trailing_stop[scripts._archive.analyze_trailing_stop]
    scripts__archive_analyze_volatility_sizing[scripts._archive.analyze_volatility_sizing]
    scripts__archive_build_vol_factors[scripts._archive.build_vol_factors]
    scripts__archive_simulate_vol_strategy[scripts._archive.simulate_vol_strategy]
    scripts__archive_run_verify_dual_engine_volatility[scripts._archive.run_verify_dual_engine_volatility]
    scripts__archive_debug_alpha[scripts._archive.debug_alpha]
    scripts__archive_run_comparison_1year[scripts._archive.run_comparison_1year]
    scripts__archive_run_mix_study[scripts._archive.run_mix_study]
    scripts__archive_update_dashboard_data[scripts._archive.update_dashboard_data]
    scripts__archive_run_paper_replay[scripts._archive.run_paper_replay]
    scripts__archive_verify_backtest_data[scripts._archive.verify_backtest_data]
    scripts__archive_performance_reporter[scripts._archive.performance_reporter]
    scripts__archive_diagnose_data_pipeline[scripts._archive.diagnose_data_pipeline]
    scripts__archive_generate_scores[scripts._archive.generate_scores]
    scripts__archive_auto_start[scripts._archive.auto_start]
    scripts__archive_simple_watchdog[scripts._archive.simple_watchdog]
    scripts__archive_telegram_listener[scripts._archive.telegram_listener]
    scripts__archive_telegram_minimal[scripts._archive.telegram_minimal]
    scripts__archive_fetch_kospi[scripts._archive.fetch_kospi]
    scripts__archive_run_weighted_sim[scripts._archive.run_weighted_sim]
    scripts__archive_optimize_weighted_sim[scripts._archive.optimize_weighted_sim]
    scripts__archive_verify_shakeout_1m[scripts._archive.verify_shakeout_1m]
    scripts__archive_visualize_replay_prototype[scripts._archive.visualize_replay_prototype]
    scripts__archive_visualize_replay_real[scripts._archive.visualize_replay_real]
    scripts__archive_verify_rebuild_b2[scripts._archive.verify_rebuild_b2]
    scripts__archive_root_legacy_config[scripts._archive.root_legacy.config]
    scripts__archive_root_legacy_run_all_tests[scripts._archive.root_legacy.run_all_tests]
    scripts__archive_root_legacy_health_service[scripts._archive.root_legacy.health_service]
    scripts__archive_root_legacy_analyze_performance[scripts._archive.root_legacy.analyze_performance]
    scripts__archive_root_legacy_analyze_final_comprehensive[scripts._archive.root_legacy.analyze_final_comprehensive]
    scripts__archive_root_legacy_analyze_adaptive_turbo[scripts._archive.root_legacy.analyze_adaptive_turbo]
    scripts__archive_root_legacy_analyze_turbo_overlay[scripts._archive.root_legacy.analyze_turbo_overlay]
    scripts__archive_root_legacy_analyze_turbo_v1_1[scripts._archive.root_legacy.analyze_turbo_v1_1]
    scripts__archive_root_legacy_analyze_sep_dd[scripts._archive.root_legacy.analyze_sep_dd]
    scripts__archive_root_legacy_analyze_turbo_v2[scripts._archive.root_legacy.analyze_turbo_v2]
    scripts__archive_root_legacy_analyze_turbo_v2_1[scripts._archive.root_legacy.analyze_turbo_v2_1]
    scripts__archive_root_legacy_analyze_turbo_v2_2[scripts._archive.root_legacy.analyze_turbo_v2_2]
    scripts__archive_root_legacy_analyze_turbo_comprehensive[scripts._archive.root_legacy.analyze_turbo_comprehensive]
    scripts__archive_root_legacy_analyze_turbo_intraday[scripts._archive.root_legacy.analyze_turbo_intraday]
    scripts__archive_root_legacy_analyze_107_files[scripts._archive.root_legacy.analyze_107_files]
    scripts__archive_root_legacy_analyze_hero_results[scripts._archive.root_legacy.analyze_hero_results]
    scripts__archive_root_legacy_analyze_v21_results[scripts._archive.root_legacy.analyze_v21_results]
    scripts__archive_root_legacy_verify_system_health[scripts._archive.root_legacy.verify_system_health]
    scripts_research_backtest_and_plot[scripts.research.backtest_and_plot]
    scripts_research_report_generator[scripts.research.report_generator]
    scripts_research_run_pulse_pipeline[scripts.research.run_pulse_pipeline]
    scripts_research_reporter[scripts.research.reporter]
    scripts_research_run_strategy_loop[scripts.research.run_strategy_loop]
    scripts_research_run_all[scripts.research.run_all]
    scripts_research_universe_loader[scripts.research.universe_loader]
    scripts_research_gate[scripts.research.gate]
    scripts_research_pulse_ev_runner[scripts.research.pulse_ev_runner]
    scripts_research_portfolio_topk_backtest[scripts.research.portfolio_topk_backtest]
    scripts_research_pulse_recommend[scripts.research.pulse_recommend]
    scripts_research_apply_recommendations[scripts.research.apply_recommendations]
    scripts_research_pulse_recommend_symbolwise[scripts.research.pulse_recommend_symbolwise]
    scripts_research_apply_symbolwise_patch[scripts.research.apply_symbolwise_patch]
    scripts_research_pulse_surface[scripts.research.pulse_surface]
    scripts_research_pulse_surface_runner[scripts.research.pulse_surface_runner]
    scripts_research_apply_surface_patch[scripts.research.apply_surface_patch]
    scripts_research_pulse_analyze_hold_ev[scripts.research.pulse.analyze_hold_ev]
    scripts_live_run_live_kiwoom[scripts.live.run_live_kiwoom]
    end
    subgraph garam_core
    style garam_core fill:#bbf,stroke:#333,stroke-width:2px
    garam_core_config_profile_loader[garam_core.config.profile_loader]
    garam_core_config_app_config[garam_core.config.app_config]
    garam_core_config_settings[garam_core.config.settings]
    garam_core_schema_market_schema[garam_core.schema.market_schema]
    garam_core_schema_fear_schema[garam_core.schema.fear_schema]
    garam_core_data_loader[garam_core.data.loader]
    garam_core_data_feature_loader[garam_core.data.feature_loader]
    garam_core_engine_turbo[garam_core.engine.turbo]
    garam_core_engine_regime[garam_core.engine.regime]
    garam_core_engine_signal[garam_core.engine.signal]
    garam_core_engine_state[garam_core.engine.state]
    garam_core_engine_edge[garam_core.engine.edge]
    garam_core_engine_signal_profit_first[garam_core.engine.signal_profit_first]
    garam_core_engine_turbo_edge[garam_core.engine.turbo_edge]
    garam_core_engine_exit_edge[garam_core.engine.exit_edge]
    garam_core_engine_position_manager[garam_core.engine.position_manager]
    garam_core_engine_fear_opportunity[garam_core.engine.fear_opportunity]
    garam_core_engine_alpha_reversal[garam_core.engine.alpha_reversal]
    garam_core_engine_signals_short_term[garam_core.engine.signals_short_term]
    garam_core_replay_replay_runner[garam_core.replay.replay_runner]
    garam_core_replay___init__[garam_core.replay.__init__]
    garam_core_health_gate[garam_core.health.gate]
    garam_core_health_recollect_consistency[garam_core.health.recollect_consistency]
    garam_core_health_quarantine_and_recollect[garam_core.health.quarantine_and_recollect]
    garam_core_health_diagnostic_report[garam_core.health.diagnostic_report]
    garam_core_execution_fill_model[garam_core.execution.fill_model]
    garam_core_execution_cost_model[garam_core.execution.cost_model]
    garam_core_reports_render_gap_dashboard[garam_core.reports.render_gap_dashboard]
    garam_core_risk_fear_gate[garam_core.risk.fear_gate]
    garam_core_live_live_state[garam_core.live.live_state]
    garam_core_live_kill_switch[garam_core.live.kill_switch]
    garam_core_live_execution_guard[garam_core.live.execution_guard]
    garam_core_live_order_router[garam_core.live.order_router]
    garam_core_live_live_runner[garam_core.live.live_runner]
    garam_core_live_engine_stack[garam_core.live.engine_stack]
    garam_core_live_live_runner_stack[garam_core.live.live_runner_stack]
    garam_core_live_pnl_tracker[garam_core.live.pnl_tracker]
    garam_core_live_engine_stack_short[garam_core.live.engine_stack_short]
    garam_core_live_spec[garam_core.live.spec]
    garam_core_live_interfaces[garam_core.live.interfaces]
    garam_core_live_aggregator[garam_core.live.aggregator]
    garam_core_live_state[garam_core.live.state]
    garam_core_live_runner[garam_core.live.runner]
    garam_core_live_kiwoom_wrapper[garam_core.live.kiwoom_wrapper]
    garam_core_live_kiwoom_feed[garam_core.live.kiwoom_feed]
    garam_core_live_kiwoom_gateway[garam_core.live.kiwoom_gateway]
    garam_core_live_gateways_paper[garam_core.live.gateways.paper]
    garam_core_research_pulse_load_data[garam_core.research.pulse.load_data]
    garam_core_research_pulse_pulse_stat[garam_core.research.pulse.pulse_stat]
    garam_core_research_pulse_pulse_ev[garam_core.research.pulse.pulse_ev]
    garam_core_research_pulse_label_gen[garam_core.research.pulse.label_gen]
    garam_core_research_pulse_features_ml[garam_core.research.pulse.features_ml]
    garam_core_research_pulse_train_ml[garam_core.research.pulse.train_ml]
    garam_core_research_pulse_regime[garam_core.research.pulse.regime]
    garam_core_research_pulse_backtest_integrated[garam_core.research.pulse.backtest_integrated]
    garam_core_strategy_base[garam_core.strategy.base]
    garam_core_strategy_registry[garam_core.strategy.registry]
    garam_core_strategy_catalog_mean_reversion[garam_core.strategy.catalog.mean_reversion]
    garam_core_strategy_catalog_breakout[garam_core.strategy.catalog.breakout]
    garam_core_strategy_catalog_fear_contrarian[garam_core.strategy.catalog.fear_contrarian]
    garam_core_strategy_catalog_regime_switch[garam_core.strategy.catalog.regime_switch]
    garam_core_backtest_engine_unified[garam_core.backtest.engine_unified]
    garam_core_reporting_report_writer[garam_core.reporting.report_writer]
    garam_core_reporting___init__[garam_core.reporting.__init__]
    garam_core_analysis_edge_matrix[garam_core.analysis.edge_matrix]
    garam_core_analysis_edge_decomposer[garam_core.analysis.edge_decomposer]
    garam_core_analysis_hero_finder[garam_core.analysis.hero_finder]
    garam_core_analysis_capital_policy[garam_core.analysis.capital_policy]
    garam_core_fastlane_feature_store[garam_core.fastlane.feature_store]
    garam_core_fastlane_policy_eval[garam_core.fastlane.policy_eval]
    end
    subgraph pipeline
    style pipeline fill:#bfb,stroke:#333,stroke-width:2px
    pipeline_ingest_run_ingest_kiwoom[pipeline.ingest.run_ingest_kiwoom]
    pipeline_validate_run_validation[pipeline.validate.run_validation]
    pipeline_store_data_loader[pipeline.store.data_loader]
    pipeline_feature_factory[pipeline.feature.factory]
    pipeline_feature_feature_loader[pipeline.feature.feature_loader]
    pipeline_feature_library_trend[pipeline.feature.library.trend]
    pipeline_feature_library_volatility[pipeline.feature.library.volatility]
    pipeline_feature_library_sentiment[pipeline.feature.library.sentiment]
    pipeline_feature_library_flow[pipeline.feature.library.flow]
    pipeline_feature_library___init__[pipeline.feature.library.__init__]
    pipeline_feature_library_momentum[pipeline.feature.library.momentum]
    pipeline_signal_strategies[pipeline.signal.strategies]
    pipeline_signal_signal_loader[pipeline.signal.signal_loader]
    pipeline_signal_hero_finder[pipeline.signal.hero_finder]
    pipeline_monitor_log_manager[pipeline.monitor.log_manager]
    pipeline_monitor_monitor_ingestion[pipeline.monitor.monitor_ingestion]
    pipeline_execution_order_manager[pipeline.execution.order_manager]
    pipeline_execution_run_live[pipeline.execution.run_live]
    end
    api_server_fixed --> ui_api_simulation_api
    scripts_migrate_data_standard --> garam_core_health_gate
    scripts_sync_universe --> garam_core_health_gate
    scripts_verify_turbo_v3 --> garam_core_execution_cost_model
    scripts_verify_turbo_v3 --> garam_core_reporting_report_writer
    scripts_verify_turbo_v3 --> garam_core_analysis_edge_matrix
    scripts_verify_turbo_v3 --> garam_core_engine_signal
    scripts_verify_turbo_v3 --> garam_core_engine_regime
    scripts_verify_turbo_v3 --> garam_core_execution_fill_model
    scripts_verify_turbo_v3 --> garam_core_data_loader
    scripts_verify_turbo_v3 --> garam_core_engine_turbo
    scripts_verify_turbo_v3 --> garam_core_replay_replay_runner
    scripts_research_alpha --> garam_core_execution_cost_model
    scripts_research_alpha --> garam_core_engine_signal
    scripts_research_alpha --> garam_core_engine_regime
    scripts_research_alpha --> garam_core_execution_fill_model
    scripts_research_alpha --> garam_core_engine_turbo
    scripts_research_alpha --> garam_core_replay_replay_runner
    scripts_verify_generalization --> garam_core_execution_cost_model
    scripts_verify_generalization --> garam_core_engine_signal
    scripts_verify_generalization --> garam_core_engine_regime
    scripts_verify_generalization --> garam_core_execution_fill_model
    scripts_verify_generalization --> garam_core_engine_turbo
    scripts_verify_generalization --> garam_core_replay_replay_runner
    scripts_discover_modules --> garam_core_data_feature_loader
    scripts_discover_modules --> garam_core_data_loader
    scripts_discover_modules --> garam_core_health_gate
    scripts_verify_profile_loader --> garam_core_config_profile_loader
    scripts_batch_profile_eval --> garam_core_engine_regime
    scripts_batch_profile_eval --> garam_core_config_profile_loader
    scripts_batch_profile_eval --> garam_core_replay_replay_runner
    scripts_research_profit_first --> garam_core_execution_cost_model
    scripts_research_profit_first --> garam_core_engine_regime
    scripts_research_profit_first --> garam_core_execution_fill_model
    scripts_research_profit_first --> garam_core_engine_signal_profit_first
    scripts_research_profit_first --> garam_core_engine_turbo
    scripts_research_profit_first --> garam_core_replay_replay_runner
    scripts_report_edge_buckets --> garam_core_data_loader
    scripts_report_edge_buckets --> garam_core_engine_edge
    scripts_report_edge_buckets --> garam_core_health_gate
    scripts_replay_profit_engine_v1 --> garam_core_engine_position_manager
    scripts_replay_profit_engine_v1 --> garam_core_execution_cost_model
    scripts_replay_profit_engine_v1 --> garam_core_engine_fear_opportunity
    scripts_replay_profit_engine_v1 --> garam_core_engine_turbo_edge
    scripts_replay_profit_engine_v1 --> garam_core_engine_regime
    scripts_replay_profit_engine_v1 --> garam_core_execution_fill_model
    scripts_replay_profit_engine_v1 --> garam_core_engine_signal_profit_first
    scripts_replay_profit_engine_v1 --> garam_core_replay_replay_runner
    scripts_replay_profit_engine_v1 --> garam_core_engine_exit_edge
    scripts_verify_rescue_005930 --> garam_core_execution_cost_model
    scripts_verify_rescue_005930 --> garam_core_engine_signal
    scripts_verify_rescue_005930 --> garam_core_engine_regime
    scripts_verify_rescue_005930 --> garam_core_execution_fill_model
    scripts_verify_rescue_005930 --> garam_core_engine_turbo
    scripts_verify_rescue_005930 --> garam_core_replay_replay_runner
    scripts_verify_rescue_top10 --> garam_core_execution_cost_model
    scripts_verify_rescue_top10 --> garam_core_engine_signal
    scripts_verify_rescue_top10 --> garam_core_engine_regime
    scripts_verify_rescue_top10 --> garam_core_execution_fill_model
    scripts_verify_rescue_top10 --> garam_core_engine_turbo
    scripts_verify_rescue_top10 --> garam_core_replay_replay_runner
    scripts_verify_alpha_vol_scaled --> garam_core_execution_cost_model
    scripts_verify_alpha_vol_scaled --> garam_core_engine_signal
    scripts_verify_alpha_vol_scaled --> garam_core_engine_regime
    scripts_verify_alpha_vol_scaled --> garam_core_execution_fill_model
    scripts_verify_alpha_vol_scaled --> garam_core_engine_turbo
    scripts_verify_alpha_vol_scaled --> garam_core_replay_replay_runner
    scripts_verify_alpha_tuning --> garam_core_execution_cost_model
    scripts_verify_alpha_tuning --> garam_core_engine_turbo
    scripts_verify_alpha_tuning --> garam_core_engine_signal
    scripts_verify_alpha_tuning --> garam_core_engine_regime
    scripts_verify_alpha_tuning --> garam_core_execution_fill_model
    scripts_verify_alpha_tuning --> garam_core_replay_replay_runner
    scripts_alpha_tuning_fast --> garam_core_fastlane_feature_store
    scripts_alpha_tuning_fast --> garam_core_fastlane_policy_eval
    scripts_alpha_tuning_fast --> garam_core_analysis_edge_decomposer
    scripts_debug_path --> garam_core
    scripts_debug_path --> garam_core_health_gate
    scripts_verify_ssot --> garam_core_reporting_report_writer
    scripts_generate_ssot_tuning --> garam_core_reporting_report_writer
    scripts_diagnose_hynix --> garam_core_fastlane_feature_store
    scripts_diagnose_hynix --> garam_core_fastlane_policy_eval
    scripts_diagnose_hynix --> garam_core_analysis_edge_decomposer
    scripts_scan_heroes --> garam_core_analysis_hero_finder
    scripts_scan_heroes --> garam_core_fastlane_feature_store
    scripts_scan_heroes --> garam_core_analysis_capital_policy
    scripts_scan_heroes --> garam_core_fastlane_policy_eval
    scripts_check_data_availability --> garam_core_health_gate
    scripts_backtest_run_pure_v2_backtest --> scripts_backtest_run_generic_backtest
    scripts_backtest_run_pure_v3_backtest --> scripts_backtest_run_generic_backtest
    scripts_backtest_run_hybrid_v2_full_attack --> scripts_backtest_run_generic_backtest
    scripts_backtest_run_hybrid_v3_backtest --> scripts_backtest_run_generic_backtest
    scripts_ui_monitor_test_ui --> scripts_run_weighted_sim
    scripts__archive_schedule_kr_data_collection --> utils_safe_scheduler
    scripts__archive_garam_startup --> scripts_startup_preflight_check_01
    scripts__archive_run_live_dge_final --> scripts_analysis_score_universe_for_dgefinal
    scripts__archive_optimize_weighted_sim --> scripts_run_weighted_sim
    scripts__archive_verify_rebuild_b2 --> garam_core_health_gate
    scripts_research_backtest_and_plot --> garam_core_engine_signals_short_term
    scripts_research_report_generator --> garam_core_engine_signals_short_term
    scripts_research_run_pulse_pipeline --> garam_core_research_pulse_pulse_stat
    scripts_research_run_pulse_pipeline --> garam_core_research_pulse_regime
    scripts_research_run_pulse_pipeline --> garam_core_research_pulse_features_ml
    scripts_research_run_pulse_pipeline --> garam_core_research_pulse_label_gen
    scripts_research_run_pulse_pipeline --> garam_core_research_pulse_backtest_integrated
    scripts_research_run_pulse_pipeline --> garam_core_research_pulse_load_data
    scripts_research_run_pulse_pipeline --> garam_core_research_pulse_train_ml
    scripts_research_run_pulse_pipeline --> garam_core_research_pulse_pulse_ev
    scripts_research_reporter --> garam_core_analysis_edge_matrix
    scripts_research_run_strategy_loop --> garam_core_strategy_registry
    scripts_research_run_strategy_loop --> garam_core_backtest_engine_unified
    scripts_research_run_strategy_loop --> scripts_research_reporter
    scripts_research_run_strategy_loop --> garam_core_research_pulse_load_data
    scripts_research_run_all --> garam_core_strategy_registry
    scripts_research_run_all --> scripts_research_pulse_surface_runner
    scripts_research_run_all --> scripts_research_portfolio_topk_backtest
    scripts_research_run_all --> scripts_research_apply_symbolwise_patch
    scripts_research_run_all --> garam_core_backtest_engine_unified
    scripts_research_run_all --> scripts_research_reporter
    scripts_research_run_all --> scripts_research_apply_surface_patch
    scripts_research_run_all --> scripts_research_universe_loader
    scripts_research_run_all --> scripts_research_gate
    scripts_research_run_all --> garam_core_research_pulse_load_data
    scripts_research_run_all --> scripts_research_pulse_recommend_symbolwise
    scripts_research_run_all --> scripts_research_pulse_ev_runner
    scripts_research_portfolio_topk_backtest --> garam_core_strategy_registry
    scripts_research_portfolio_topk_backtest --> garam_core_research_pulse_load_data
    scripts_research_pulse_recommend_symbolwise --> scripts_research_pulse_recommend
    scripts_research_pulse_surface --> garam_core_strategy_registry
    scripts_research_pulse_surface --> garam_core_backtest_engine_unified
    scripts_research_pulse_surface_runner --> scripts_research_pulse_surface
    scripts_research_pulse_analyze_hold_ev --> garam_core_strategy_registry
    scripts_research_pulse_analyze_hold_ev --> garam_core_backtest_engine_unified
    scripts_research_pulse_analyze_hold_ev --> garam_core_research_pulse_load_data
    scripts_live_run_live_kiwoom --> garam_core_live_kiwoom_wrapper
    scripts_live_run_live_kiwoom --> garam_core_live_gateways_paper
    scripts_live_run_live_kiwoom --> garam_core_live_spec
    scripts_live_run_live_kiwoom --> garam_core_live_kiwoom_gateway
    scripts_live_run_live_kiwoom --> garam_core_live_kiwoom_feed
    scripts_live_run_live_kiwoom --> scripts_live_run_live
    scripts_live_run_live_kiwoom --> garam_core_live_runner
    scripts_live_run_live_kiwoom --> garam_core_live_aggregator
    tests_test_validate_us_sp500_data_coverage --> scripts_validate_us_sp500_data_coverage
    tests_test_generate_garam_system_report --> scripts_generate_garam_system_report
    tests_test_performance_runner --> scripts_run_kr_intraday_performance
    tests_test_phase21_contracts --> garam_core_analysis_hero_finder
    tests_test_capital_policy --> garam_core_analysis_hero_finder
    tests_test_capital_policy --> garam_core_analysis_capital_policy
    tests_ui_test_dashboard_api --> ui_api_dashboard_api
    garam_signals_fs_fast --> utils
    pipeline_feature_feature_loader --> pipeline_feature_factory
    pipeline_feature_feature_loader --> pipeline_monitor_log_manager
    pipeline_feature_feature_loader --> pipeline_store_data_loader
    pipeline_signal_signal_loader --> pipeline_feature_feature_loader
    pipeline_signal_signal_loader --> pipeline_monitor_log_manager
    pipeline_signal_signal_loader --> pipeline_signal_strategies
    pipeline_execution_run_live --> garam_core_live_order_router
    pipeline_execution_run_live --> garam_core_engine_regime
    pipeline_execution_run_live --> garam_core_data_loader
    pipeline_execution_run_live --> garam_core_live_execution_guard
    pipeline_execution_run_live --> garam_core_engine_signal_profit_first
    pipeline_execution_run_live --> garam_core_live_live_runner_stack
    pipeline_execution_run_live --> garam_core_engine_position_manager
    pipeline_execution_run_live --> garam_core_live_engine_stack
    pipeline_execution_run_live --> garam_core_risk_fear_gate
    pipeline_execution_run_live --> garam_core_engine_signal
    pipeline_execution_run_live --> garam_core_engine_turbo
    pipeline_execution_run_live --> garam_core_engine_exit_edge
    pipeline_execution_run_live --> garam_core_execution_cost_model
    pipeline_execution_run_live --> garam_core_engine_fear_opportunity
    pipeline_execution_run_live --> garam_core_engine_turbo_edge
    pipeline_execution_run_live --> garam_core_config_app_config
    archive_scripts_run_profile_replay --> garam_core_engine_regime
    archive_scripts_run_profile_replay --> garam_core_config_profile_loader
    archive_scripts_run_profile_replay --> garam_core_replay_replay_runner
    archive_scripts_run_live_dry --> garam_core_data_feature_loader
    archive_scripts_run_live_dry --> garam_core_live_live_runner
    archive_scripts_run_live_dry --> garam_core_engine_regime
    archive_scripts_run_live_dry --> garam_core_data_loader
    archive_scripts_run_live_dry --> garam_core_config_profile_loader
    archive_scripts_run_live_safe --> garam_core_data_feature_loader
    archive_scripts_run_live_safe --> garam_core_live_order_router
    archive_scripts_run_live_safe --> garam_core_live_live_runner
    archive_scripts_run_live_safe --> garam_core_engine_regime
    archive_scripts_run_live_safe --> garam_core_data_loader
    archive_scripts_run_live_safe --> garam_core_live_execution_guard
    archive_scripts_run_live_safe --> garam_core_live_kill_switch
    archive_scripts_run_live_safe --> garam_core_config_profile_loader
    garam_core_config_profile_loader --> garam_core_execution_cost_model
    garam_core_config_profile_loader --> garam_core_risk_fear_gate
    garam_core_config_profile_loader --> garam_core_engine_signal
    garam_core_config_profile_loader --> garam_core_execution_fill_model
    garam_core_config_profile_loader --> garam_core_engine_turbo
    garam_core_data_feature_loader --> garam_core_schema_fear_schema
    garam_core_engine_signal_profit_first --> garam_core_engine_alpha_reversal
    garam_core_engine_signal_profit_first --> garam_core_engine_edge
    garam_core_engine_turbo_edge --> garam_core_engine_edge
    garam_core_engine_exit_edge --> garam_core_engine_edge
    garam_core_replay_replay_runner --> garam_core_engine_regime
    garam_core_replay_replay_runner --> garam_core_data_loader
    garam_core_replay_replay_runner --> garam_core_config_profile_loader
    garam_core_replay_replay_runner --> garam_core_engine_signal_profit_first
    garam_core_replay_replay_runner --> garam_core_execution_fill_model
    garam_core_replay_replay_runner --> garam_core_engine_position_manager
    garam_core_replay_replay_runner --> garam_core_data_feature_loader
    garam_core_replay_replay_runner --> garam_core_engine_state
    garam_core_replay_replay_runner --> garam_core_risk_fear_gate
    garam_core_replay_replay_runner --> garam_core_engine_signal
    garam_core_replay_replay_runner --> garam_core_engine_turbo
    garam_core_replay_replay_runner --> garam_core_live_kill_switch
    garam_core_replay_replay_runner --> garam_core_engine_exit_edge
    garam_core_replay_replay_runner --> garam_core_execution_cost_model
    garam_core_replay_replay_runner --> garam_core_engine_fear_opportunity
    garam_core_replay_replay_runner --> garam_core_engine_turbo_edge
    garam_core_replay_replay_runner --> garam_core_health_gate
    garam_core_health_diagnostic_report --> garam_core_data_feature_loader
    garam_core_health_diagnostic_report --> garam_core_engine_signal
    garam_core_health_diagnostic_report --> garam_core_engine_regime
    garam_core_health_diagnostic_report --> garam_core_health_recollect_consistency
    garam_core_health_diagnostic_report --> garam_core_data_loader
    garam_core_health_diagnostic_report --> garam_core_health_gate
    garam_core_health_diagnostic_report --> garam_core_engine_turbo
    garam_core_health_diagnostic_report --> garam_core_replay_replay_runner
    garam_core_live_order_router --> garam_core_execution_cost_model
    garam_core_live_live_runner --> garam_core_live_live_state
    garam_core_live_live_runner --> garam_core_risk_fear_gate
    garam_core_live_live_runner --> garam_core_engine_signal
    garam_core_live_live_runner --> garam_core_engine_regime
    garam_core_live_live_runner --> garam_core_engine_turbo
    garam_core_live_engine_stack --> garam_core_engine_position_manager
    garam_core_live_engine_stack --> garam_core_engine_fear_opportunity
    garam_core_live_engine_stack --> garam_core_engine_turbo_edge
    garam_core_live_engine_stack --> garam_core_risk_fear_gate
    garam_core_live_engine_stack --> garam_core_engine_signal
    garam_core_live_engine_stack --> garam_core_engine_regime
    garam_core_live_engine_stack --> garam_core_engine_signal_profit_first
    garam_core_live_engine_stack --> garam_core_engine_turbo
    garam_core_live_engine_stack --> garam_core_engine_exit_edge
    garam_core_live_live_runner_stack --> garam_core_live_engine_stack
    garam_core_live_live_runner_stack --> garam_core_live_order_router
    garam_core_live_live_runner_stack --> garam_core_live_execution_guard
    garam_core_live_engine_stack_short --> garam_core_live_engine_stack
    garam_core_live_runner --> garam_core_strategy_registry
    garam_core_live_runner --> garam_core_live_interfaces
    garam_core_live_runner --> garam_core_live_spec
    garam_core_live_runner --> garam_core_research_pulse_load_data
    garam_core_live_runner --> garam_core_live_state
    garam_core_live_kiwoom_feed --> garam_core_live_interfaces
    garam_core_live_kiwoom_feed --> garam_core_live_aggregator
    garam_core_live_kiwoom_gateway --> garam_core_live_interfaces
    garam_core_live_gateways_paper --> garam_core_live_interfaces
    garam_core_research_pulse_backtest_integrated --> garam_core_research_pulse_features_ml
    garam_core_strategy_registry --> garam_core_strategy_base
    garam_core_strategy_catalog_mean_reversion --> garam_core_strategy_base
    garam_core_strategy_catalog_breakout --> garam_core_strategy_base
    garam_core_strategy_catalog_breakout --> garam_core_engine_signals_short_term
    garam_core_strategy_catalog_fear_contrarian --> garam_core_strategy_base
    garam_core_strategy_catalog_fear_contrarian --> garam_core_engine_signals_short_term
    garam_core_strategy_catalog_regime_switch --> garam_core_strategy_catalog_breakout
    garam_core_strategy_catalog_regime_switch --> garam_core_strategy_catalog_mean_reversion
    garam_core_strategy_catalog_regime_switch --> garam_core_strategy_base
    garam_core_backtest_engine_unified --> garam_core_strategy_base
```

*Total Internal Edges: 262*